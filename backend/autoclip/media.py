"""Media helpers: source acquisition (upload / yt-dlp), probing, audio, loudness.
ffmpeg discovery + probe are reused from the AI Video Editor so both modules behave identically."""
from __future__ import annotations

import logging
import math
import os
import urllib.parse
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from . import config

try:
    from backend.services.video_editor import render as _ed
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services.video_editor import render as _ed  # type: ignore

log = logging.getLogger("autoclip.media")

RenderError = _ed.RenderError
bin_path = _ed._bin
run = _ed.run
probe = _ed.probe
extract_audio_16k = _ed.extract_audio_16k
FONTS_DIR = _ed.FONTS_DIR
filter_path = _ed._filter_path


class SourceError(Exception):
    """User-facing problem with the source (bad link, too long, private, ...)."""


# --------------------------------------------------------------------------- #
# Links
# --------------------------------------------------------------------------- #

def check_url(raw: str) -> str:
    """Only http(s) links on allowlisted video sites. Returns the cleaned URL or raises SourceError."""
    url = (raw or "").strip()
    if len(url) > 2000:
        raise SourceError("That link is too long.")
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        raise SourceError("That doesn't look like a valid link.")
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password or (p.port not in (None, 80, 443)):
        raise SourceError("Paste a normal https:// video link.")
    host = p.hostname.lower().rstrip(".")
    if not any(host == d or host.endswith("." + d) for d in config.SOURCE_DOMAINS):
        raise SourceError("This site isn't supported for links yet. Upload the file instead.")
    return urllib.parse.urlunsplit(("https", p.netloc, p.path, p.query, ""))


def _ydl_opts(dest_tmpl: str, hook: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
    o: Dict[str, Any] = {
        "outtmpl": dest_tmpl, "quiet": True, "no_warnings": True, "noplaylist": True,
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4", "retries": 3, "fragment_retries": 3, "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "restrictfilenames": True, "overwrites": True, "live_from_start": False,
    }
    if config.MAX_UPLOAD_MB:
        o["max_filesize"] = config.MAX_UPLOAD_MB * 1024 * 1024 * 3
    if config.COOKIES_FILE and os.path.isfile(config.COOKIES_FILE):
        o["cookiefile"] = config.COOKIES_FILE
    if hook:
        o["progress_hooks"] = [hook]
    try:
        import static_ffmpeg  # noqa: F401
        o["ffmpeg_location"] = os.path.dirname(bin_path("ffmpeg"))
    except Exception:
        pass
    return o


def fetch_url(url: str, workdir: str, progress: Optional[Callable[[float], None]] = None) -> Dict[str, Any]:
    """Download a link with yt-dlp. Returns {path, title, uploader, duration}."""
    import yt_dlp

    url = check_url(url)
    os.makedirs(workdir, exist_ok=True)
    tmpl = os.path.join(workdir, "source.%(ext)s")
    try:
        with yt_dlp.YoutubeDL(_ydl_opts(tmpl)) as y:
            info = y.extract_info(url, download=False)
    except Exception as e:
        raise SourceError(_friendly_ydl_error(e))
    if info.get("_type") == "playlist":
        raise SourceError("That is a playlist. Paste a single video link.")
    if info.get("is_live"):
        raise SourceError("Live streams aren't supported yet. Try again after the stream ends.")
    dur = float(info.get("duration") or 0)
    if dur and config.MAX_SOURCE_MINUTES and dur > config.MAX_SOURCE_MINUTES * 60:
        raise SourceError(f"Video is {dur / 60:.0f} min. The limit is {config.MAX_SOURCE_MINUTES} min.")

    def hook(d: Dict[str, Any]) -> None:
        if progress and d.get("status") == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if tot:
                progress(min(1.0, d.get("downloaded_bytes", 0) / tot))

    try:
        with yt_dlp.YoutubeDL(_ydl_opts(tmpl, hook)) as y:
            info = y.extract_info(url, download=True)
            path = info.get("requested_downloads", [{}])[0].get("filepath") or y.prepare_filename(info)
    except Exception as e:
        raise SourceError(_friendly_ydl_error(e))
    if not path or not os.path.exists(path):
        cands = [os.path.join(workdir, n) for n in os.listdir(workdir) if n.startswith("source.")]
        path = max(cands, key=os.path.getsize) if cands else ""
    if not path or not os.path.exists(path):
        raise SourceError("Could not download that video.")
    return {"path": path, "title": (info.get("title") or "")[:300], "uploader": (info.get("uploader") or "")[:120],
            "duration": dur}


def _friendly_ydl_error(e: Exception) -> str:
    t = str(e).lower()
    if "sign in" in t or "confirm you" in t or "bot" in t:
        return "The site blocked the download from our server. Upload the video file instead."
    if "private" in t:
        return "That video is private."
    if "unavailable" in t or "removed" in t or "404" in t:
        return "That video is unavailable."
    if "unsupported url" in t:
        return "That link isn't a video we can read."
    if "larger than max-filesize" in t or "file is larger" in t:
        return "That video file is too large."
    log.warning("yt-dlp error: %s", str(e)[:300])
    return "Could not download that video. Upload the file instead."


# --------------------------------------------------------------------------- #
# Audio analysis
# --------------------------------------------------------------------------- #

def loudness_per_second(wav16k: str) -> List[float]:
    """RMS level in dBFS for each second of a 16 kHz mono wav (streams, so long videos stay cheap)."""
    import soundfile as sf

    out: List[float] = []
    with sf.SoundFile(wav16k) as f:
        sr = f.samplerate
        while True:
            block = f.read(sr, dtype="float32", always_2d=False)
            if block is None or len(block) == 0:
                break
            if block.ndim > 1:
                block = block.mean(axis=1)
            rms = float(np.sqrt(np.mean(np.square(block)) + 1e-12))
            out.append(round(20 * math.log10(rms + 1e-9), 2))
    return out


def zscores(db: List[float]) -> List[float]:
    if not db:
        return []
    a = np.asarray(db, dtype=np.float64)
    voiced = a[a > -55]
    if len(voiced) < 5:
        return [0.0] * len(db)
    mu, sd = float(np.median(voiced)), float(np.std(voiced)) or 1.0
    # 3 s smoothing so one clap doesn't look like a moment
    k = np.ones(3) / 3
    sm = np.convolve(a, k, mode="same")
    return [round(float((x - mu) / sd), 2) for x in sm]


def grab_frame(src: str, t: float, dst: str, width: int = 640) -> Optional[str]:
    try:
        run([bin_path("ffmpeg"), "-v", "error", "-y", "-ss", f"{max(0.0, t):.2f}", "-i", src, "-frames:v", "1",
             "-vf", f"scale={width}:-2", "-q:v", "4", dst], 60)
        return dst if os.path.exists(dst) else None
    except RenderError:
        return None
