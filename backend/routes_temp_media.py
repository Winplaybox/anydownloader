"""Temporary public media hosting with fail-closed public URL generation."""
import hmac
import os
import re
import shutil
import tempfile
import time
import uuid
from urllib.parse import urlsplit

from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

STORE_DIR = os.environ.get("TEMP_MEDIA_DIR") or os.path.join(tempfile.gettempdir(), "ovd_temp_media")
TTL_SECONDS = int(float(os.environ.get("TEMP_MEDIA_TTL_HOURS", "6")) * 3600)
MAX_BYTES = int(os.environ.get("TEMP_MEDIA_MAX_MB", "300")) * 1024 * 1024
IS_PRODUCTION = os.environ.get("WPB_ENV", "").lower() in ("prod", "production") or bool(os.environ.get("RENDER"))
ALLOWED_EXT = {
    "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
    "mp3": "audio/mpeg", "m4a": "audio/mp4", "wav": "audio/wav",
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp",
}
_ID_RE = re.compile(r"[0-9a-f]{32}\.(?:mp4|mov|webm|mp3|m4a|wav|jpg|jpeg|png|webp)")


def _authorized(request) -> bool:
    auto_key = os.environ.get("AUTOMATION_API_KEY", "").strip()
    worker_key = os.environ.get("WORKER_KEY", "").strip()
    worker_secret = os.environ.get("WORKER_SECRET", "").strip()
    given = request.headers.get("x-api-key", "") or request.headers.get("x-worker-key", "")
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        given = given or auth[7:].strip()
    if not given:
        return False
    return any(expected and hmac.compare_digest(given.encode(), expected.encode())
               for expected in (auto_key, worker_key, worker_secret))


def _ensure_store() -> None:
    """Create a private storage directory and reject symlinked storage roots."""
    os.makedirs(STORE_DIR, mode=0o700, exist_ok=True)
    if os.path.islink(STORE_DIR):
        raise RuntimeError("TEMP_MEDIA_DIR must not be a symlink.")
    try:
        os.chmod(STORE_DIR, 0o700)
    except OSError:
        # Permission enforcement is best-effort on platforms without chmod support;
        # production deployments must use a private writable volume.
        pass



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


def _validated_base_url(value: str, require_https: bool = False) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("PUBLIC_BASE_URL must be an absolute HTTP(S) URL without credentials.")
    if require_https and parsed.scheme != "https":
        raise ValueError("PUBLIC_BASE_URL must use HTTPS in production.")
    if parsed.query or parsed.fragment:
        raise ValueError("PUBLIC_BASE_URL must not contain a query or fragment.")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("PUBLIC_BASE_URL contains an invalid port.") from exc
    return value.strip().rstrip("/")


def _public_base(request) -> str:
    configured = os.environ.get("PUBLIC_BASE_URL", "").strip()
    if configured:
        return _validated_base_url(configured, require_https=IS_PRODUCTION)
    if IS_PRODUCTION:
        raise RuntimeError("PUBLIC_BASE_URL must be configured in production.")

    # Development fallback: never trust forwarded headers or accept a malformed Host.
    host = request.headers.get("host", "")
    if not host or any(ch in host for ch in ("@", "/", "\\", "\n", "\r")):
        raise ValueError("Invalid Host header.")
    parsed_host = urlsplit("//" + host)
    if not parsed_host.hostname or parsed_host.username or parsed_host.password:
        raise ValueError("Invalid Host header.")
    try:
        _ = parsed_host.port
    except ValueError as exc:
        raise ValueError("Invalid Host header.") from exc
    scheme = request.url.scheme if request.url.scheme in ("http", "https") else "http"
    return f"{scheme}://{host}"


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
    try:
        public_base = _public_base(request)
    except (ValueError, RuntimeError):
        return JSONResponse({"ok": False, "error": "Public media URL configuration is invalid."}, status_code=503)
    try:
        _ensure_store()
        _purge_expired()
    except (OSError, RuntimeError):
        return JSONResponse({"ok": False, "error": "Temporary media storage is unavailable."}, status_code=503)
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
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return JSONResponse({"ok": False, "error": "Temporary media upload failed."}, status_code=500)

    if written == 0:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return JSONResponse({"ok": False, "error": "Empty file."}, status_code=400)

    media_id = f"{uuid.uuid4().hex}.{_ext_for(filename, file_ctype)}"
    final_path = os.path.join(STORE_DIR, media_id)
    try:
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, final_path)
    except OSError:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return JSONResponse({"ok": False, "error": "Temporary media could not be stored."}, status_code=500)
    return JSONResponse({
        "ok": True, "id": media_id, "url": f"{public_base}/api/temp-media/{media_id}",
        "bytes": written, "expires_at": int(time.time()) + TTL_SECONDS,
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
