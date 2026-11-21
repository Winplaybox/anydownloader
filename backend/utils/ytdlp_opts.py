"""
Single source of truth for yt-dlp options.

Every yt-dlp call (resolve, extract, download) MUST use `robust_opts()` so the
Deno JS runtime, multi-client fallback, cookies and proxy are applied everywhere.
Before this module existed, PR #7 only applied them to downloads, so /api/resolve
and /api/extract kept failing with "Failed to extract any player response".

Env (all optional):
  YTDLP_COOKIES_FILE   path to a Netscape cookies file (e.g. Render Secret File)
  YTDLP_COOKIES        cookies file content
  YTDLP_PROXY          http(s)/socks proxy URL
  YTDLP_DENO_PATH      explicit deno binary
  YTDLP_PLAYER_CLIENTS comma list, default "web_embedded,default,tv,web_safari,mweb,android_vr"
"""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from typing import Any, Dict, Optional

try:
    import yt_dlp  # noqa: F401
    _YTDLP_VERSION = yt_dlp.version.__version__
except Exception:  # pragma: no cover
    _YTDLP_VERSION = "unknown"

_lock = threading.Lock()
_runtimes_cache: Optional[Dict[str, Dict[str, str]]] = None
_cookie_cache: Optional[str] = None
_cookie_loaded = False
_logged = False

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def ensure_node_on_path() -> Optional[str]:
    """Node from the `nodejs-wheel-binaries` package is not on PATH on Render; add it so
    yt-dlp and pytubefix (BotGuard PO tokens) can use it. Returns the node path or None."""
    node = shutil.which("node")
    if node:
        return node
    try:
        from nodejs_wheel import executable as _nw  # type: ignore
        bin_dir = os.path.join(_nw.ROOT_DIR, "bin")
        cand = os.path.join(bin_dir, "node.exe" if os.name == "nt" else "node")
        if os.path.exists(cand):
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            return cand
    except Exception:
        pass
    return None


def find_js_runtimes() -> Dict[str, Dict[str, str]]:
    """Deno (from the `deno` PyPI package on Render) first, Node as fallback. Cached."""
    global _runtimes_cache
    if _runtimes_cache is not None:
        return _runtimes_cache
    runtimes: Dict[str, Dict[str, str]] = {}
    deno_path = os.environ.get("YTDLP_DENO_PATH", "").strip() or shutil.which("deno")
    if not deno_path:
        try:
            import deno as _deno_pkg  # type: ignore
            deno_path = _deno_pkg.find_deno_bin()
        except Exception:
            deno_path = None
    if deno_path:
        runtimes["deno"] = {"path": deno_path}
    node_path = ensure_node_on_path()
    if node_path:
        runtimes["node"] = {"path": node_path}
    _runtimes_cache = runtimes
    return runtimes


def normalize_netscape_cookies(text: str) -> str:
    """Accept cookies pasted into a dashboard: literal \\n and spaces instead of tabs."""
    text = text.replace("\\n", "\n").replace("\r", "")
    out = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or (stripped.startswith("#") and not stripped.startswith("#HttpOnly_")):
            out.append(stripped)
            continue
        if "\t" not in stripped:
            parts = stripped.split(None, 6)
            if len(parts) == 7:
                stripped = "\t".join(parts)
        out.append(stripped)
    body = "\n".join(out).strip() + "\n"
    if not body.startswith("# Netscape HTTP Cookie File"):
        body = "# Netscape HTTP Cookie File\n" + body
    return body


def cookiefile() -> Optional[str]:
    """Writable per-process copy of the cookies (yt-dlp rewrites the file on exit)."""
    global _cookie_cache, _cookie_loaded
    with _lock:
        if _cookie_loaded:
            return _cookie_cache if (_cookie_cache and os.path.exists(_cookie_cache)) else None
        _cookie_loaded = True
        src_text = None
        src_file = os.environ.get("YTDLP_COOKIES_FILE", "").strip()
        if src_file and os.path.isfile(src_file):
            with open(src_file, "r", encoding="utf-8", errors="ignore") as fh:
                src_text = fh.read()
        elif os.environ.get("YTDLP_COOKIES", "").strip():
            src_text = os.environ["YTDLP_COOKIES"]
        if not src_text:
            return None
        dest = os.path.join(tempfile.gettempdir(), f"ovd_yt_cookies_{os.getpid()}.txt")
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(normalize_netscape_cookies(src_text))
        _cookie_cache = dest
        return dest


# web_embedded needs no PO token or login and is what public downloader sites rely on;
# yt-dlp falls through to the next client for videos that disallow embedding.
DEFAULT_PLAYER_CLIENTS = "web_embedded,default,tv,web_safari,mweb,android_vr"


def failure_reason(err: str) -> str:
    """Coarse, user-safe failure class for the API response (never raw yt-dlp text)."""
    e = (err or "").lower()
    if is_youtube_block(err):
        return "youtube_block"
    if "ffmpeg" in e or "ffprobe" in e or "postprocess" in e:
        return "ffmpeg"
    if "requested format is not available" in e:
        return "format"
    if "no space left" in e or "errno 28" in e:
        return "disk"
    if "permission" in e or "errno 13" in e or "read-only" in e:
        return "permission"
    if any(t in e for t in ("timed out", "timeout", "connection", "name or service", "ssl", "unable to download webpage")):
        return "network"
    if "unsupported url" in e:
        return "unsupported"
    if "login" in e or "sign in" in e:
        return "login_required"
    return "unknown"


def player_clients() -> list:
    raw = os.environ.get("YTDLP_PLAYER_CLIENTS", DEFAULT_PLAYER_CLIENTS)
    return [c.strip() for c in raw.split(",") if c.strip()]


def robust_opts(mode: str = "extract", *, socket_timeout: Optional[float] = None,
                cookies_path: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
    """
    mode="extract": fail fast (metadata for the UI must answer in < ~20 s)
    mode="download": more retries, longer timeouts
    """
    global _logged
    fast = mode == "extract"
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": socket_timeout or (12 if fast else 30),
        "retries": 1 if fast else 3,
        "extractor_retries": 1 if fast else 3,
        "http_headers": {"User-Agent": DESKTOP_UA, "Accept-Language": "en-US,en;q=0.9"},
        "extractor_args": {"youtube": {"player_client": player_clients()}},
    }
    if fast:
        opts["skip_download"] = True
    runtimes = find_js_runtimes()
    if runtimes:
        opts["js_runtimes"] = runtimes
    cf = cookies_path if (cookies_path and os.path.exists(cookies_path)) else cookiefile()
    if cf:
        opts["cookiefile"] = cf
    px = proxy or os.environ.get("YTDLP_PROXY", "").strip()
    if px:
        opts["proxy"] = px
    if not _logged:
        _logged = True
        print(f"[yt-dlp] version={_YTDLP_VERSION} js_runtimes={sorted(runtimes) or 'NONE'} "
              f"clients={player_clients()} cookies={'yes' if cf else 'no'} proxy={'yes' if px else 'no'}",
              flush=True)
    return opts


def is_youtube_block(err: str) -> bool:
    e = (err or "").lower()
    return any(s in e for s in (
        "failed to extract any player response", "sign in to confirm", "not a bot",
        "http error 429", "precondition check failed", "po token", "this content isn't available",
    ))
