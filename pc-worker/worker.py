"""OVD PC Worker v2.0 — Universal media extraction & downloads from home connection.

Bypasses cloud datacenter IP blocks (YouTube, Instagram, TikTok, Facebook, Twitter, Reddit)
by running yt-dlp on your PC through a secure ngrok static tunnel.

Endpoints:
    GET  /health                     -> {"ok": true, ...}
    POST /extract   {"url": "..."}   -> {"ok": true, "items": [...], "title": "...", "duration": ...}
    POST /download  {"url": "...", "kind": "video"|"audio", "height": 1080}
         Headers: X-Worker-Key: <WORKER_KEY> or Authorization: Bearer <WORKER_KEY>
"""
import glob
import hmac
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

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
OVD_BASE = os.environ.get("OVD_BASE", "https://anydownloader-backend-vvbj.onrender.com").rstrip("/")
OVD_API_KEY = os.environ.get("OVD_API_KEY", "").strip()
MAX_HEIGHT = int(os.environ.get("MAX_HEIGHT", "1080"))
DOWNLOAD_TIMEOUT_S = int(os.environ.get("DOWNLOAD_TIMEOUT_S", "240"))
COOKIES_FILE = os.environ.get("COOKIES_FILE", "").strip()

NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", "").strip()

_LOCK = threading.Lock()


def log(msg: str) -> None:
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


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


def download(url: str, kind: str = "video", height: int = 1080, quality: str = "320") -> dict:
    workdir = tempfile.mkdtemp(prefix="ovd_worker_")
    try:
        is_audio = kind == "audio"
        if is_audio:
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--no-playlist", "--no-progress", "--restrict-filenames",
                "-x", "--audio-format", "mp3", "--audio-quality", str(quality),
                "-o", os.path.join(workdir, "%(id)s.%(ext)s"),
                "--print", "after_move:%(title)s",
            ]
            file_pattern = "*.mp3"
            mime_type = "audio/mpeg"
        else:
            fmt = (
                f"bv*[height<={height}][vcodec^=avc1]+ba[ext=m4a]/"
                f"bv*[height<={height}]+ba/b[height<={height}]/b"
            )
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--no-playlist", "--no-progress", "--restrict-filenames",
                "-f", fmt, "--merge-output-format", "mp4",
                "-o", os.path.join(workdir, "%(id)s.%(ext)s"),
                "--print", "after_move:%(title)s",
            ]
            file_pattern = "*.mp4"
            mime_type = "video/mp4"

        deno = shutil.which("deno")
        if deno:
            cmd += ["--js-runtimes", "deno"]
        ff = _ffmpeg_dir()
        if ff:
            cmd += ["--ffmpeg-location", ff]
        if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        cmd.append(url)

        log(f"downloading ({kind}) {url}")
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=DOWNLOAD_TIMEOUT_S, **_priority_kwargs(),
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "yt-dlp failed").strip()[-600:])
        title = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout.strip() else ""

        files = sorted(glob.glob(os.path.join(workdir, file_pattern)), key=os.path.getsize, reverse=True)
        if not files:
            raise RuntimeError(f"yt-dlp finished but no {file_pattern} was produced")
        path = files[0]
        size = os.path.getsize(path)
        log(f"downloaded {size // 1024} KB, uploading to OVD")

        with open(path, "rb") as fh:
            headers = {
                "X-API-Key": OVD_API_KEY,
                "X-Worker-Key": WORKER_KEY,
                "Authorization": f"Bearer {WORKER_KEY}",
            }
            resp = requests.post(
                f"{OVD_BASE}/api/temp-media",
                headers=headers,
                files={"file": (os.path.basename(path), fh, mime_type)},
                timeout=240,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"OVD upload failed {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        data["title"] = title
        log(f"uploaded -> {data.get('url')}")
        return data
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "OVDWorker/2.0"

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):
        pass

    def do_HEAD(self):
        if self.path.split("?")[0] == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/health":
            return self._send(200, {"ok": True, "busy": _LOCK.locked(), "max_height": MAX_HEIGHT, "version": "2.0"})
        self._send(404, {"ok": False, "error": "not found"})

    def _check_auth(self) -> bool:
        given = self.headers.get("X-Worker-Key", "")
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            given = auth[7:].strip()
        return bool(WORKER_KEY and given and hmac.compare_digest(given.encode(), WORKER_KEY.encode()))

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/download", "/extract"):
            return self._send(404, {"ok": False, "error": "not found"})

        if not self._check_auth():
            return self._send(401, {"ok": False, "error": "bad authentication key"})

        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(min(length, 50_000)) or b"{}")
        except Exception:  # noqa: BLE001
            return self._send(400, {"ok": False, "error": "invalid JSON body"})

        url = str(body.get("url", "")).strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return self._send(400, {"ok": False, "error": "valid http(s) URL required"})

        if path == "/extract":
            try:
                result = extract_media_info(url)
                return self._send(200, result)
            except Exception as exc:
                log(f"EXTRACT ERROR: {exc}")
                return self._send(502, {"ok": False, "error": str(exc)[:600]})

        # /download
        if not _LOCK.acquire(timeout=5):
            return self._send(429, {"ok": False, "error": "busy with another download, retry shortly"})
        try:
            kind = body.get("kind", "video")
            height = int(body.get("height") or MAX_HEIGHT)
            quality = str(body.get("quality") or "320")
            return self._send(200, {"ok": True, **download(url, kind=kind, height=height, quality=quality)})
        except subprocess.TimeoutExpired:
            return self._send(504, {"ok": False, "error": f"download took longer than {DOWNLOAD_TIMEOUT_S}s"})
        except Exception as exc:  # noqa: BLE001
            log(f"DOWNLOAD ERROR {exc}")
            return self._send(502, {"ok": False, "error": str(exc)[:600]})
        finally:
            _LOCK.release()


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


def main() -> None:
    missing = [k for k, v in {"WORKER_KEY": WORKER_KEY, "OVD_API_KEY": OVD_API_KEY}.items() if not v]
    if missing:
        sys.exit(f"Missing in worker.env: {', '.join(missing)}")
    _ffmpeg_dir()
    log(f"OVD PC worker v2.0 on http://127.0.0.1:{PORT} (uploads to {OVD_BASE})")
    tunnel = start_ngrok()
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    finally:
        if tunnel and tunnel.poll() is None:
            tunnel.terminate()


if __name__ == "__main__":
    main()
