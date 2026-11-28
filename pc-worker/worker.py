"""OVD PC Worker v2.0 — Universal media extraction & downloads from home connection.

Bypasses cloud datacenter IP blocks (YouTube, Instagram, TikTok, Facebook, Twitter, Reddit)
by running yt-dlp on your PC through a secure ngrok static tunnel.

Endpoints:
    GET  /health                     -> {"ok": true, ...}
    POST /extract   {"url": "..."}   -> {"ok": true, "items": [...], "title": "...", "duration": ...}
    POST /download  {"url": "...", "kind": "video"|"audio", "height": 1080}
         Headers: X-Worker-Key: <WORKER_KEY> or Authorization: Bearer <WORKER_KEY>
         Returns: {"ok": true, "url": "<signed file URL>"}
"""
import glob
import hmac
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_env(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_env(os.path.join(HERE, "worker.env"))

PORT = int(os.environ.get("PORT", "8787"))
WORKER_KEY = os.environ.get("WORKER_KEY", "").strip()
MAX_HEIGHT = int(os.environ.get("MAX_HEIGHT", "1080"))
DOWNLOAD_TIMEOUT_S = int(os.environ.get("DOWNLOAD_TIMEOUT_S", "240"))
COOKIES_FILE = os.environ.get("COOKIES_FILE", "").strip()

NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", "").strip()
PUBLIC_BASE = (
    os.environ.get("WORKER_PUBLIC_BASE_URL", "").strip()
    or (f"https://{NGROK_DOMAIN}" if NGROK_DOMAIN and "PASTE-YOUR" not in NGROK_DOMAIN else "https://worker.winplaybox.in")
).rstrip("/")
MEDIA_DIR = os.environ.get("WORKER_MEDIA_DIR") or os.path.join(tempfile.gettempdir(), "ovd-worker-media")
FILE_TTL_S = 900
_FILE_KEY = secrets.token_bytes(32)
_FILE_NAME = re.compile(r"[0-9a-f]{32}\.(?:mp4|mp3)")
_FILE_ROUTE = "/download-files/"
_FILE_TYPES = {"mp4": "video/mp4", "mp3": "audio/mpeg"}

_LOCK = threading.Lock()


def log(msg: str) -> None:
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


def log_event(event: str, **fields) -> None:
    print(json.dumps({"time": int(time.time()), "event": event, **fields}), flush=True)


def _file_signature(name: str, expires: int) -> str:
    return hmac.digest(_FILE_KEY, f"{name}:{expires}".encode("ascii"), "sha256").hex()


def _file_url(name: str, expires: int) -> str:
    return f"{PUBLIC_BASE}{_FILE_ROUTE}{name}?expires={expires}&sig={_file_signature(name, expires)}"


def _valid_file_link(name: str, query: str) -> bool:
    params = parse_qs(query, keep_blank_values=True)
    expires_values, sig_values = params.get("expires", []), params.get("sig", [])
    if len(expires_values) != 1 or len(sig_values) != 1:
        return False
    expires, signature = expires_values[0], sig_values[0]
    if not re.fullmatch(r"[0-9]{1,12}", expires) or not re.fullmatch(r"[0-9a-f]{64}", signature):
        return False
    expiry = int(expires)
    return expiry > time.time() and hmac.compare_digest(signature, _file_signature(name, expiry))


def _ffmpeg_dir() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        try:
            import static_ffmpeg

            static_ffmpeg.add_paths()
            path = shutil.which("ffmpeg")
        except Exception as exc:  # noqa: BLE001
            log(f"ffmpeg not found ({exc}); merged 1080p may fail")
    return os.path.dirname(path) if path else ""


def _priority_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": 0x00004000}  # BELOW_NORMAL_PRIORITY_CLASS
    return {"preexec_fn": lambda: os.nice(10)}


def extract_media_info(url: str) -> dict:
    """Extract metadata, formats, audios, and thumbnails using local yt-dlp."""
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--skip-download", "--no-playlist", "--no-progress",
        "--remote-components", "ejs:github",
        "-J",
    ]
    deno = shutil.which("deno")
    if deno:
        cmd += ["--js-runtimes", "deno"]
    ff = _ffmpeg_dir()
    if ff:
        cmd += ["--ffmpeg-location", ff]
    if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    px = os.environ.get("YTDLP_PROXY", "").strip() or os.environ.get("HTTP_PROXY", "").strip()
    if px:
        cmd += ["--proxy", px]
    cmd.append(url)

    log(f"extracting {url}")
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=35, **_priority_kwargs(),
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "yt-dlp extract failed").strip()
        log(f"extract failed: {err[:200]}")
        raise RuntimeError(err[-600:])

    try:
        info = json.loads(proc.stdout)
    except Exception as e:
        raise RuntimeError(f"Failed to parse yt-dlp output JSON: {e}")

    item_id = str(info.get("id") or "media")
    title = info.get("title") or "Extracted Media"
    description = info.get("description") or title
    author = {
        "username": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
        "displayName": info.get("uploader") or info.get("channel"),
        "avatar": info.get("thumbnail"),
    }
    duration = info.get("duration")

    items = []
    subtitles = []

    # 1. Handle playlist / carousel entries (Instagram carousel, TikTok photo mode, Reddit galleries)
    entries = info.get("entries") or []
    if entries:
        for idx, entry in enumerate(entries):
            e_formats = entry.get("formats", []) or []
            # Find best video format if present
            best_vid = None
            for f in sorted(e_formats, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True):
                if f.get("vcodec") and f.get("vcodec") != "none" and f.get("url"):
                    best_vid = f
                    break
            if best_vid:
                items.append({
                    "kind": "video",
                    "url": best_vid.get("url"),
                    "label": f"Slide {idx + 1} Video ({best_vid.get('height') or 'HD'}p)",
                    "ext": best_vid.get("ext") or "mp4",
                    "width": best_vid.get("width"),
                    "height": best_vid.get("height"),
                    "fps": best_vid.get("fps"),
                    "filesize": best_vid.get("filesize") or best_vid.get("filesize_approx"),
                    "has_audio": best_vid.get("acodec") not in (None, "none"),
                    "needs_merge": False
                })
            else:
                # Image / photo slide
                img_url = entry.get("url")
                if not img_url and entry.get("thumbnails"):
                    img_url = entry["thumbnails"][-1].get("url")
                if img_url:
                    items.append({
                        "kind": "image",
                        "url": img_url,
                        "label": f"Photo {idx + 1}",
                        "ext": "jpg",
                        "width": entry.get("width"),
                        "height": entry.get("height")
                    })

    # 2. Single media formats
    formats = info.get("formats", []) or []

    # Video formats
    heights_seen = set()
    for f in sorted(formats, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True):
        h = f.get("height")
        vcodec = f.get("vcodec")
        if h and h >= 144 and h not in heights_seen and vcodec and vcodec != "none" and f.get("url"):
            heights_seen.add(h)
            quality_tag = "4K UHD" if h >= 2160 else ("2K QHD" if h >= 1440 else ("Full HD" if h >= 1080 else ("HD" if h >= 720 else "SD")))
            items.append({
                "kind": "video",
                "url": f.get("url"),
                "label": f"{h}p ({quality_tag})",
                "ext": f.get("ext") or "mp4",
                "width": f.get("width"),
                "height": h,
                "fps": f.get("fps"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "has_audio": f.get("acodec") not in (None, "none"),
                "needs_merge": f.get("acodec") in (None, "none")
            })

    # Audio formats
    for f in sorted(formats, key=lambda x: (x.get("abr") or 0), reverse=True):
        if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none") and f.get("url"):
            abr = int(f.get("abr") or 192)
            items.append({
                "kind": "audio",
                "url": f.get("url"),
                "label": f"{abr} kbps Audio (MP3)",
                "ext": "mp3",
                "filesize": f.get("filesize") or f.get("filesize_approx")
            })
            break

    if not any(i["kind"] == "audio" for i in items) and formats:
        items.append({
            "kind": "audio",
            "url": url,
            "label": "Original Audio Track (MP3)",
            "ext": "mp3"
        })

    # 3. Photos / Images & Thumbnails
    thumbs = info.get("thumbnails", []) or []
    # If this is a photo-only post (e.g. Instagram photo, Pinterest, Reddit photo)
    if not any(i["kind"] == "video" for i in items) and thumbs:
        best_thumb = thumbs[-1]
        if best_thumb.get("url"):
            items.insert(0, {
                "kind": "image",
                "url": best_thumb.get("url"),
                "label": "Original Photo HD",
                "ext": "jpg",
                "width": best_thumb.get("width"),
                "height": best_thumb.get("height")
            })

    # Add thumbnails for video/audio previews
    for idx, t in enumerate(thumbs[:6]):
        if t.get("url"):
            items.append({
                "kind": "thumbnail",
                "url": t.get("url"),
                "label": f"Thumbnail {idx + 1}",
                "ext": "jpg",
                "width": t.get("width"),
                "height": t.get("height")
            })

    # 4. Subtitles (Native creator tracks + auto captions)
    raw_subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}
    seen_langs = set()

    # Creator-uploaded subtitles first
    for lang, tracks in list(raw_subs.items()):
        if lang in seen_langs:
            continue
        for tr in tracks:
            if tr.get("url") and tr.get("ext") in ("vtt", "srt"):
                sub_entry = {
                    "kind": "subtitle",
                    "url": tr.get("url"),
                    "label": f"Subtitles ({lang.upper()})",
                    "ext": tr.get("ext", "srt"),
                    "lang": lang
                }
                items.append(sub_entry)
                subtitles.append(sub_entry)
                seen_langs.add(lang)
                break
        if len(seen_langs) >= 8:
            break

    # Auto-generated captions for popular languages if not already present
    if len(seen_langs) < 6:
        for lang in ("en", "hi", "es", "fr", "de", "pt", "id", "ar", "ja", "ko"):
            if lang in auto_subs and lang not in seen_langs:
                for tr in auto_subs[lang]:
                    if tr.get("url") and tr.get("ext") in ("vtt", "srt"):
                        sub_entry = {
                            "kind": "subtitle",
                            "url": tr.get("url"),
                            "label": f"Auto Captions ({lang.upper()})",
                            "ext": tr.get("ext", "srt"),
                            "lang": lang
                        }
                        items.append(sub_entry)
                        subtitles.append(sub_entry)
                        seen_langs.add(lang)
                        break

    return {
        "ok": True,
        "id": item_id,
        "title": title,
        "description": description,
        "caption": description,
        "author": author,
        "duration": duration,
        "items": items,
        "subtitles": subtitles,
    }


def download(url: str, kind: str = "video", height: int = 1080, quality: str = "320") -> str:
    workdir = tempfile.mkdtemp(prefix="job-", dir=MEDIA_DIR)
    try:
        is_audio = kind == "audio"
        if is_audio:
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--no-playlist", "--no-progress", "--quiet", "--restrict-filenames",
                "--remote-components", "ejs:github",
                "-x", "--audio-format", "mp3", "--audio-quality", str(quality),
                "-o", os.path.join(workdir, "%(id)s.%(ext)s"),
            ]
            ext = "mp3"
        else:
            fmt = (
                f"bv*[height<={height}][vcodec^=avc1]+ba[ext=m4a]/"
                f"bv*[height<={height}]+ba/b[height<={height}]/b"
            )
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--no-playlist", "--no-progress", "--quiet", "--restrict-filenames",
                "--remote-components", "ejs:github",
                "-f", fmt, "--merge-output-format", "mp4",
                "-o", os.path.join(workdir, "%(id)s.%(ext)s"),
            ]
            ext = "mp4"

        deno = shutil.which("deno")
        if deno:
            cmd += ["--js-runtimes", "deno"]
        ff = _ffmpeg_dir()
        if ff:
            cmd += ["--ffmpeg-location", ff]
        if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        px = os.environ.get("YTDLP_PROXY", "").strip() or os.environ.get("HTTP_PROXY", "").strip()
        if px:
            cmd += ["--proxy", px]
        cmd.append(url)

        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=DOWNLOAD_TIMEOUT_S, **_priority_kwargs(),
        )
        if proc.returncode != 0:
            raise RuntimeError("yt-dlp failed")

        files = glob.glob(os.path.join(workdir, f"*.{ext}"))
        path = max(files, key=os.path.getsize, default=None)
        if not path or not os.path.getsize(path):
            raise RuntimeError("yt-dlp produced no media")
        name = f"{uuid.uuid4().hex}.{ext}"
        published = int(time.time())
        os.utime(path, (published, published))
        os.replace(path, os.path.join(MEDIA_DIR, name))
        return _file_url(name, published + FILE_TTL_S)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "OVDWorker/2.0"

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def log_message(self, fmt, *args):
        pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/health":
            return self._send(200, {"ok": True, "busy": _LOCK.locked(), "max_height": MAX_HEIGHT, "version": "2.0"})
        if path.startswith(_FILE_ROUTE):
            return self._serve_file(path[len(_FILE_ROUTE):], query)
        self._send(404, {"ok": False, "error": "not found"})

    def _serve_file(self, name: str, query: str) -> None:
        if not _FILE_NAME.fullmatch(name):
            return self._send(404, {"ok": False, "error": "not found"})
        if not _valid_file_link(name, query):
            return self._send(403, {"ok": False, "error": "invalid or expired file link"})
        path = os.path.join(MEDIA_DIR, name)
        try:
            if os.path.islink(path):
                raise FileNotFoundError
            stream = open(path, "rb")
        except OSError:
            return self._send(404, {"ok": False, "error": "not found"})
        with stream:
            self.send_response(200)
            self.send_header("Content-Type", _FILE_TYPES[name.rsplit(".", 1)[1]])
            self.send_header("Content-Length", str(os.fstat(stream.fileno()).st_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                shutil.copyfileobj(stream, self.wfile)

    def _check_auth(self) -> bool:
        scheme, _, token = self.headers.get("Authorization", "").partition(" ")
        keys = (self.headers.get("X-Worker-Key", ""), token.strip() if scheme.lower() == "bearer" else "")
        return bool(WORKER_KEY and any(hmac.compare_digest(key.encode(), WORKER_KEY.encode()) for key in keys))

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/download", "/extract"):
            return self._send(404, {"ok": False, "error": "not found"})

        if not self._check_auth():
            return self._send(401, {"ok": False, "error": "bad authentication key"})

        try:
            length = int(self.headers.get("Content-Length") or 0)
            if not 0 <= length <= 50_000:
                raise ValueError
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, RecursionError):
            return self._send(400, {"ok": False, "error": "invalid JSON body"})

        url = body.get("url")
        try:
            parsed = urlsplit(url.strip()) if isinstance(url, str) else None
            valid_url = parsed and parsed.scheme in ("http", "https") and parsed.hostname
        except ValueError:
            valid_url = False
        if not valid_url:
            return self._send(400, {"ok": False, "error": "valid http(s) URL required"})
        url = url.strip()

        if path == "/extract":
            try:
                result = extract_media_info(url)
                return self._send(200, result)
            except Exception as exc:
                log(f"EXTRACT ERROR: {exc}")
                return self._send(502, {"ok": False, "error": str(exc)[:600]})

        kind = body.get("kind", "video")
        try:
            height = int(body.get("height") or MAX_HEIGHT)
            if kind not in ("video", "audio") or height <= 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            return self._send(400, {"ok": False, "error": "invalid kind or height"})
        quality = str(body.get("quality") or "320")

        if not _LOCK.acquire(blocking=False):
            log_event("download_busy")
            return self._send(429, {"ok": False, "error": "busy with another download, retry shortly"})
        try:
            result_url = download(url, kind=kind, height=height, quality=quality)
        except subprocess.TimeoutExpired:
            log_event("download_timeout", kind=kind)
            return self._send(504, {"ok": False, "error": f"download took longer than {DOWNLOAD_TIMEOUT_S}s"})
        except Exception as exc:  # noqa: BLE001
            log_event("download_failed", kind=kind, error_type=type(exc).__name__)
            return self._send(502, {"ok": False, "error": "download failed"})
        finally:
            _LOCK.release()
        log_event("download_completed", kind=kind)
        return self._send(200, {"ok": True, "url": result_url})


def _find_ngrok() -> str:
    for name in ("ngrok.exe", "ngrok"):
        local = os.path.join(HERE, name)
        if os.path.isfile(local):
            return local
    return shutil.which("ngrok") or ""


def start_ngrok():
    if not NGROK_DOMAIN or "PASTE-YOUR" in NGROK_DOMAIN:
        log("NGROK_DOMAIN not set in worker.env -> tunnel NOT started")
        return None
    exe = _find_ngrok()
    if not exe:
        log("ngrok.exe not found")
        return None
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    proc = subprocess.Popen([exe, "http", f"--url={NGROK_DOMAIN}", str(PORT)], **kwargs)
    time.sleep(3)
    if proc.poll() is not None:
        log("ngrok exited immediately -> check NGROK_DOMAIN and auth token")
        return None
    log(f"ngrok tunnel: https://{NGROK_DOMAIN}  ->  http://127.0.0.1:{PORT}")
    log(f"check it:     https://{NGROK_DOMAIN}/health")
    return proc


def _purge_expired_files() -> None:
    cutoff = time.time() - FILE_TTL_S
    removed = 0
    with os.scandir(MEDIA_DIR) as entries:
        for entry in entries:
            if not _FILE_NAME.fullmatch(entry.name):
                continue
            try:
                if entry.is_file(follow_symlinks=False) and entry.stat().st_mtime <= cutoff:
                    os.unlink(entry.path)
                    removed += 1
            except OSError as exc:
                log_event("file_cleanup_failed", error_type=type(exc).__name__)
    if removed:
        log_event("files_expired", count=removed)


def _start_cleaner_thread() -> None:
    def _loop():
        while True:
            try:
                _purge_expired_files()
            except OSError as exc:
                log_event("file_cleanup_failed", error_type=type(exc).__name__)
            time.sleep(60)
    threading.Thread(target=_loop, daemon=True).start()


def main() -> None:
    if not WORKER_KEY:
        sys.exit("Missing in worker.env: WORKER_KEY")
    try:
        base = urlsplit(PUBLIC_BASE)
        _ = base.port
        if (
            not base.hostname or base.username is not None or base.password is not None
            or base.query or base.fragment
            or (base.scheme != "https" and not (base.scheme == "http" and base.hostname in ("localhost", "127.0.0.1", "::1")))
        ):
            raise ValueError
    except ValueError:
        sys.exit("WORKER_PUBLIC_BASE_URL must be HTTPS (HTTP is allowed on loopback).")
    os.makedirs(MEDIA_DIR, mode=0o700, exist_ok=True)
    if os.path.islink(MEDIA_DIR) or (hasattr(os, "getuid") and os.stat(MEDIA_DIR).st_uid != os.getuid()):
        sys.exit("WORKER_MEDIA_DIR must be a private directory owned by the worker.")
    os.chmod(MEDIA_DIR, 0o700)
    _ffmpeg_dir()
    _start_cleaner_thread()
    host = os.environ.get("WORKER_HOST", "0.0.0.0")
    log_event("worker_started", host=host, port=PORT, file_ttl_s=FILE_TTL_S)
    tunnel = start_ngrok()
    try:
        ThreadingHTTPServer((host, PORT), Handler).serve_forever()
    finally:
        if tunnel and tunnel.poll() is None:
            tunnel.terminate()


if __name__ == "__main__":
    main()
