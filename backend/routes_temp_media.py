"""Temporary public media hosting for automations (Make.com -> Instagram/Facebook).

Instagram's Graph API only accepts a public video URL, so an automation uploads
the MP4 here, gets a short-lived public link, publishes, then deletes it.

    POST   /api/temp-media        X-API-Key required. multipart field "file" (or raw body).
                                  -> {"ok", "id", "url", "expires_at", "bytes"}
    GET    /api/temp-media/{id}   public, Range-capable (Instagram/Facebook fetch it)
    DELETE /api/temp-media/{id}   X-API-Key required

Files auto-expire after TEMP_MEDIA_TTL_HOURS (default 6). A Render free instance
also wipes /tmp on every restart, so nothing piles up.
"""
import hmac
import os
import re
import shutil
import tempfile
import time
import uuid

from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

STORE_DIR = os.environ.get("TEMP_MEDIA_DIR") or os.path.join(tempfile.gettempdir(), "ovd_temp_media")
TTL_SECONDS = int(float(os.environ.get("TEMP_MEDIA_TTL_HOURS", "6")) * 3600)
MAX_BYTES = int(os.environ.get("TEMP_MEDIA_MAX_MB", "300")) * 1024 * 1024
ALLOWED_EXT = {
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "webm": "video/webm",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}
_ID_RE = re.compile(r"[0-9a-f]{32}\.(?:mp4|mov|webm|mp3|m4a|wav|jpg|jpeg|png|webp)")


def _authorized(request) -> bool:
    auto_key = os.environ.get("AUTOMATION_API_KEY", "wpb_auto_94de1a6c713962d8d9147c12fa32e0aa8bcccd43").strip()
    worker_key = os.environ.get("WORKER_KEY", "wpb_worker_3047a7d0cb90d81830e004fbc0e61f6428f7e3cb").strip()
    worker_secret = os.environ.get("WORKER_SECRET", "").strip()
    given = request.headers.get("x-api-key", "") or request.headers.get("x-worker-key", "")
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        given = given or auth[7:].strip()
    
    if not given:
        return False
    for expected in (auto_key, worker_key, worker_secret):
        if expected and hmac.compare_digest(given.encode(), expected.encode()):
            return True
    return False


def _purge_expired() -> None:
    if not os.path.isdir(STORE_DIR):
        return
    cutoff = time.time() - TTL_SECONDS
    for name in os.listdir(STORE_DIR):
        path = os.path.join(STORE_DIR, name)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass


def _public_base(request) -> str:
    base = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base:
        return base
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    return f"{proto}://{request.headers.get('host', request.url.netloc)}"


def _ext_for(filename: str, content_type: str) -> str:
    ext = (os.path.splitext(filename or "")[1].lstrip(".") or "").lower()
    if ext in ALLOWED_EXT:
        return ext
    for e, ct in ALLOWED_EXT.items():
        if (content_type or "").split(";")[0].strip().lower() == ct:
            return e
    return "mp4"


async def upload_handler(request):
    if not _authorized(request):
        return JSONResponse({"ok": False, "error": "X-API-Key required."}, status_code=401)
    _purge_expired()
    os.makedirs(STORE_DIR, exist_ok=True)

    tmp_path = os.path.join(STORE_DIR, f".upload_{uuid.uuid4().hex}")
    written = 0
    ctype = request.headers.get("content-type", "")
    filename = ""
    try:
        if ctype.startswith("multipart/form-data"):
            form = await request.form(max_files=1, max_fields=10)
            upload = form.get("file")
            if upload is None or not hasattr(upload, "read"):
                return JSONResponse({"ok": False, "error": "Send the video in a multipart field named 'file'."}, status_code=400)
            filename, file_ctype = upload.filename or "", upload.content_type or ""
            with open(tmp_path, "wb") as out:
                while chunk := await upload.read(1024 * 1024):
                    written += len(chunk)
                    if written > MAX_BYTES:
                        raise ValueError("too_large")
                    out.write(chunk)
            await upload.close()
        else:
            file_ctype = ctype
            with open(tmp_path, "wb") as out:
                async for chunk in request.stream():
                    written += len(chunk)
                    if written > MAX_BYTES:
                        raise ValueError("too_large")
                    out.write(chunk)
    except ValueError:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return JSONResponse({"ok": False, "error": f"File is larger than {MAX_BYTES // (1024 * 1024)} MB."}, status_code=413)

    if written == 0:
        os.remove(tmp_path)
        return JSONResponse({"ok": False, "error": "Empty file."}, status_code=400)

    media_id = f"{uuid.uuid4().hex}.{_ext_for(filename, file_ctype)}"
    shutil.move(tmp_path, os.path.join(STORE_DIR, media_id))
    return JSONResponse({
        "ok": True,
        "id": media_id,
        "url": f"{_public_base(request)}/api/temp-media/{media_id}",
        "bytes": written,
        "expires_at": int(time.time()) + TTL_SECONDS,
    })


async def serve_handler(request):
    media_id = request.path_params["media_id"]
    if not _ID_RE.fullmatch(media_id):
        return JSONResponse({"ok": False, "error": "Not found."}, status_code=404)
    path = os.path.join(STORE_DIR, media_id)
    if not os.path.isfile(path) or os.path.getmtime(path) < time.time() - TTL_SECONDS:
        return JSONResponse({"ok": False, "error": "Not found or expired."}, status_code=404)
    ext = media_id.rsplit(".", 1)[1]
    return FileResponse(path, media_type=ALLOWED_EXT[ext], headers={"Cache-Control": "no-store"})


async def delete_handler(request):
    if not _authorized(request):
        return JSONResponse({"ok": False, "error": "X-API-Key required."}, status_code=401)
    media_id = request.path_params["media_id"]
    if not _ID_RE.fullmatch(media_id):
        return JSONResponse({"ok": False, "error": "Not found."}, status_code=404)
    path = os.path.join(STORE_DIR, media_id)
    existed = os.path.isfile(path)
    if existed:
        os.remove(path)
    return JSONResponse({"ok": True, "deleted": existed})


routes_temp_media = [
    Route("/api/temp-media", upload_handler, methods=["POST"]),
    Route("/api/temp-media/{media_id}", serve_handler, methods=["GET", "HEAD"]),
    Route("/api/temp-media/{media_id}", delete_handler, methods=["DELETE"]),
]
