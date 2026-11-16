"""OVD PC Worker — downloads YouTube videos from a home connection.

YouTube blocks Render's datacenter IP, so Make.com calls this worker (through an
ngrok static URL) instead. The worker downloads with yt-dlp on your PC, uploads
the MP4 to OVD's temporary media endpoint, and returns the public link that
Instagram/Facebook fetch.

    GET  /health                     -> {"ok": true, ...}
    POST /download  {"url": "..."}   -> {"ok": true, "url": "...", "id": "...", "bytes": n, "title": "..."}
         header X-Worker-Key: <WORKER_KEY>

Light on the PC: one download at a time, yt-dlp runs at below-normal priority,
temp files are deleted right after upload.
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

_LOCK = threading.Lock()  # one download at a time keeps the PC responsive


def log(msg: str) -> None:
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


def _ffmpeg_dir() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        try:
            import static_ffmpeg  # downloads a portable ffmpeg once

            static_ffmpeg.add_paths()
            path = shutil.which("ffmpeg")
        except Exception as exc:  # noqa: BLE001
            log(f"ffmpeg not found ({exc}); merged 1080p may fail")
    return os.path.dirname(path) if path else ""


def _priority_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": 0x00004000}  # BELOW_NORMAL_PRIORITY_CLASS
    return {"preexec_fn": lambda: os.nice(10)}


def download(url: str) -> dict:
    workdir = tempfile.mkdtemp(prefix="ovd_worker_")
    try:
        fmt = (
            f"bv*[height<={MAX_HEIGHT}][vcodec^=avc1]+ba[ext=m4a]/"
            f"bv*[height<={MAX_HEIGHT}]+ba/b[height<={MAX_HEIGHT}]/b"
        )
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-playlist", "--no-progress", "--restrict-filenames",
            "-f", fmt, "--merge-output-format", "mp4",
            "--js-runtimes", "deno",
            "-o", os.path.join(workdir, "%(id)s.%(ext)s"),
            "--print", "after_move:%(title)s",
        ]
        ff = _ffmpeg_dir()
        if ff:
            cmd += ["--ffmpeg-location", ff]
        if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        cmd.append(url)

        log(f"downloading {url}")
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=DOWNLOAD_TIMEOUT_S, **_priority_kwargs(),
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "yt-dlp failed").strip()[-600:])
        title = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout.strip() else ""

        files = sorted(glob.glob(os.path.join(workdir, "*.mp4")), key=os.path.getsize, reverse=True)
        if not files:
            raise RuntimeError("yt-dlp finished but no MP4 was produced")
        path = files[0]
        size = os.path.getsize(path)
        log(f"downloaded {size // 1024} KB, uploading to OVD")

        with open(path, "rb") as fh:
            resp = requests.post(
                f"{OVD_BASE}/api/temp-media",
                headers={"X-API-Key": OVD_API_KEY},
                files={"file": (os.path.basename(path), fh, "video/mp4")},
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
    server_version = "OVDWorker/1.0"

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):  # quieter console
        pass

    def do_GET(self):
        if self.path.split("?")[0] == "/health":
            return self._send(200, {"ok": True, "busy": _LOCK.locked(), "max_height": MAX_HEIGHT})
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if self.path.split("?")[0] != "/download":
            return self._send(404, {"ok": False, "error": "not found"})
        given = self.headers.get("X-Worker-Key", "")
        if not (WORKER_KEY and given and hmac.compare_digest(given.encode(), WORKER_KEY.encode())):
            return self._send(401, {"ok": False, "error": "bad X-Worker-Key"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(min(length, 10_000)) or b"{}")
        except Exception:  # noqa: BLE001
            return self._send(400, {"ok": False, "error": "send JSON {\"url\": ...}"})
        url = str(body.get("url", "")).strip()
        if not url.startswith(("https://www.youtube.com/", "https://youtube.com/", "https://youtu.be/", "https://m.youtube.com/")):
            return self._send(400, {"ok": False, "error": "only YouTube URLs are allowed"})
        if not _LOCK.acquire(timeout=5):
            return self._send(429, {"ok": False, "error": "busy with another download, retry shortly"})
        try:
            return self._send(200, {"ok": True, **download(url)})
        except subprocess.TimeoutExpired:
            return self._send(504, {"ok": False, "error": f"download took longer than {DOWNLOAD_TIMEOUT_S}s"})
        except Exception as exc:  # noqa: BLE001
            log(f"ERROR {exc}")
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
    """Start the ngrok tunnel ourselves so one double-click runs everything."""
    if not NGROK_DOMAIN or "PASTE-YOUR" in NGROK_DOMAIN:
        log("NGROK_DOMAIN not set in worker.env -> tunnel NOT started (Make cannot reach this PC)")
        return None
    exe = _find_ngrok()
    if not exe:
        log("ngrok.exe not found -> put ngrok.exe in this folder (https://ngrok.com/download)")
        return None
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    proc = subprocess.Popen([exe, "http", f"--url={NGROK_DOMAIN}", str(PORT)], **kwargs)
    time.sleep(3)
    if proc.poll() is not None:
        log("ngrok exited immediately -> run once: ngrok.exe config add-authtoken <token>, and check NGROK_DOMAIN")
        return None
    log(f"ngrok tunnel: https://{NGROK_DOMAIN}  ->  http://127.0.0.1:{PORT}")
    log(f"check it:     https://{NGROK_DOMAIN}/health")
    return proc


def main() -> None:
    missing = [k for k, v in {"WORKER_KEY": WORKER_KEY, "OVD_API_KEY": OVD_API_KEY}.items() if not v]
    if missing:
        sys.exit(f"Missing in worker.env: {', '.join(missing)}")
    _ffmpeg_dir()
    log(f"OVD PC worker on http://127.0.0.1:{PORT}  (max {MAX_HEIGHT}p, uploads to {OVD_BASE})")
    tunnel = start_ngrok()
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    finally:
        if tunnel and tunnel.poll() is None:
            tunnel.terminate()


if __name__ == "__main__":
    main()
