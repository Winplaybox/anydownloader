"""/api/autoclip - AutoClip AI (long video -> vertical clips). Isolated module; see backend/autoclip/__init__.py.

Browser (frontend on GitHub Pages / *.winplaybox.in):
  GET  /api/autoclip/health
  GET  /api/autoclip/options
  POST /api/autoclip/jobs                         multipart(file, settings...) | JSON {url, settings}
  GET  /api/autoclip/jobs/{id}                    X-Job-Token
  POST /api/autoclip/jobs/{id}/cancel             X-Job-Token
  GET  /api/autoclip/jobs/{id}/files/{name}?t=    clip_01.mp4 | clip_01.jpg | clip_01.srt | clips.json
  GET  /api/autoclip/jobs/{id}/zip?t=             every clip + captions + metadata
Workers (X-Worker-Key = AUTOCLIP_WORKER_KEY):
  POST /api/autoclip/workers/claim
  GET  /api/autoclip/workers/jobs/{id}/source
  POST /api/autoclip/workers/jobs/{id}/heartbeat | artifact | complete | fail
Admin (X-Admin-Key):
  GET  /api/autoclip/admin/stats
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import re
import tempfile
import zipfile
from typing import Any, Dict, Optional

from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

try:
    from backend.autoclip import __version__, byo, config, media, models, speech, store
    from backend.autoclip.worker import inline_worker
    from backend.security.zero_trust import authenticate_admin, client_ip, rate_limit
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from autoclip import __version__, byo, config, media, models, speech, store  # type: ignore
    from autoclip.worker import inline_worker  # type: ignore
    from security.zero_trust import authenticate_admin, client_ip, rate_limit  # type: ignore

NO_STORE = {"Cache-Control": "no-store"}
_UPLOAD_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".3gp", ".ts", ".flv"}
_MEDIA_TYPES = {".mp4": "video/mp4", ".jpg": "image/jpeg", ".srt": "application/x-subrip; charset=utf-8",
                ".json": "application/json"}


def _err(status: int, code: str, message: str, **extra: Any) -> JSONResponse:
    return JSONResponse({"ok": False, "code": code, "error": message, **extra}, status_code=status, headers=NO_STORE)


def _client(request: Request) -> str:
    guest = re.sub(r"[^A-Za-z0-9_-]", "", request.headers.get("x-guest-id", ""))[:64]
    return hashlib.sha256(f"autoclip:{client_ip(request)}:{guest}".encode()).hexdigest()[:24]


def _browser_ok(request: Request) -> bool:
    if authenticate_admin(request, allow_bearer_jwt=False):
        return True
    api_key = request.headers.get("x-api-key", "")
    auto = os.environ.get("AUTOMATION_API_KEY", "").strip()
    if auto and api_key and hmac.compare_digest(api_key.encode(), auto.encode()):
        return True
    origin = request.headers.get("origin", "")
    if origin:
        return config.origin_allowed(origin)
    ref = request.headers.get("referer", "")
    m = re.match(r"^(https?://[^/]+)", ref)
    return bool(m and config.origin_allowed(m.group(1)))


def _token(request: Request) -> str:
    return request.headers.get("x-job-token", "") or request.query_params.get("t", "")


def _job_or_error(request: Request) -> tuple[Optional[Dict[str, Any]], Optional[JSONResponse]]:
    job_id = request.path_params["id"]
    if not store.valid_id(job_id) or not store.token_ok(job_id, _token(request)):
        return None, _err(404, "NotFound", "Job not found or link expired.")
    job = store.get(job_id)
    if not job:
        return None, _err(404, "NotFound", "Job not found or link expired.")
    return job, None


def _disabled() -> Optional[JSONResponse]:
    return None if config.ENABLED else _err(503, "Disabled", "AutoClip is switched off on this server.")


# --------------------------------------------------------------------------- #
# Public
# --------------------------------------------------------------------------- #

async def health(request: Request) -> Response:
    try:
        ff = bool(media.bin_path("ffmpeg"))
    except Exception:
        ff = False
    from backend.autoclip import reframe  # noqa: WPS433
    cv = await asyncio.to_thread(reframe.face_tracking_available)
    return JSONResponse({
        "ok": True, "service": "autoclip", "version": __version__, "enabled": config.ENABLED,
        "worker": inline_worker.status(), "ffmpeg": ff, "speech": speech.available(), "face_tracking": cv, "byo_ai": sorted(byo.PROVIDERS),
        "ai": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")
                   or os.environ.get("OPENROUTER_API_KEY")),
    }, headers=NO_STORE)


async def options(request: Request) -> Response:
    if (d := _disabled()):
        return d
    unlimited = bool(authenticate_admin(request, allow_bearer_jwt=False))
    return JSONResponse({"ok": True, **config.public_options(), "unlimited": unlimited},
                        headers={"Cache-Control": "public, max-age=300"})


async def create_job(request: Request) -> Response:
    if (d := _disabled()):
        return d
    if not _browser_ok(request):
        return _err(403, "Forbidden", "Open AutoClip from the official site.")
    admin = bool(authenticate_admin(request, allow_bearer_jwt=False))
    if not admin:
        if await asyncio.to_thread(store.queued_count) >= config.MAX_QUEUED:
            return _err(503, "Busy", "AutoClip is busy right now. Try again in a few minutes.", retry_after=120)
        ok, _ = await asyncio.to_thread(rate_limit, "autoclip:burst", client_ip(request), 6, 600)
        if not ok:
            return _err(429, "RateLimited", "Too many requests. Wait a few minutes.")

    ctype = request.headers.get("content-type", "")
    upload = None
    if ctype.startswith("multipart/form-data"):
        try:
            form = await request.form(max_files=1, max_fields=30)
        except Exception:
            return _err(400, "BadRequest", "Could not read the upload.")
        raw = {k: v for k, v in form.items() if isinstance(v, str)}
        if raw.get("settings"):
            try:
                raw.update(json.loads(raw["settings"]))
            except (ValueError, TypeError):
                pass
        upload = form.get("file")
        url = (raw.get("url") or "").strip()
    else:
        try:
            raw = await request.json()
        except Exception:
            return _err(400, "BadRequest", "Send JSON {url, settings} or a multipart upload.")
        if not isinstance(raw, dict):
            return _err(400, "BadRequest", "Invalid body.")
        if isinstance(raw.get("settings"), dict):
            raw = {**raw["settings"], **{k: v for k, v in raw.items() if k != "settings"}}
        url = str(raw.get("url") or "").strip()

    settings = config.clean_settings(raw)
    try:
        ai = byo.build(raw.get("ai_provider"), raw.get("ai_key"), raw.get("ai_model"))
    except byo.KeyError_ as e:
        return _err(400, "BadKey", str(e))
    if admin:
        settings["server_ai"] = True  # admins/automation may use the server's shared key
    has_file = upload is not None and not isinstance(upload, str) and getattr(upload, "filename", "")
    if not has_file and not url:
        return _err(400, "SourceMissing", "Paste a video link or upload a video file.")
    if has_file:
        ext = os.path.splitext(upload.filename or "")[1].lower()
        if ext not in _UPLOAD_EXT:
            return _err(400, "BadFile", "Upload a video file (mp4, mov, mkv, webm).")
    else:
        try:
            url = media.check_url(url)
        except media.SourceError as e:
            return _err(400, "BadLink", str(e))

    if not admin and config.DAILY_LIMIT:
        ok, remaining = await asyncio.to_thread(rate_limit, "autoclip:day", client_ip(request), config.DAILY_LIMIT, 86400)
        if not ok:
            return _err(429, "DailyLimit", f"Free limit is {config.DAILY_LIMIT} videos per day. Come back tomorrow.")

    name = (os.path.basename(upload.filename or "video")[:120] if has_file else None)
    job = await asyncio.to_thread(store.create, source_kind="upload" if has_file else "url",
                                  source_url=None if has_file else url, source_name=name,
                                  settings=settings, client=_client(request),
                                  status="uploading" if has_file else "queued")
    if ai is not None:
        byo.put(job["id"], ai)  # RAM only; dropped when the job ends
    if has_file:
        dest = os.path.join(store.job_dir(job["id"]), "source" + ext)
        limit = config.MAX_UPLOAD_MB * 1024 * 1024
        size = 0
        try:
            with open(dest, "wb") as f:
                while True:
                    chunk = await upload.read(1 << 20)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > limit:
                        raise ValueError("too big")
                    f.write(chunk)
        except ValueError:
            await asyncio.to_thread(store.request_cancel, job["id"])
            store._unlink(dest)
            byo.drop(job["id"])
            return _err(413, "TooLarge", f"File is larger than {config.MAX_UPLOAD_MB} MB.")
        finally:
            await upload.close()
        if size < 10_000:
            byo.drop(job["id"])
            await asyncio.to_thread(store.request_cancel, job["id"])
            return _err(400, "BadFile", "That file is empty or broken.")
        await asyncio.to_thread(store.mark_queued, job["id"])
        job = await asyncio.to_thread(store.get, job["id"])
    return JSONResponse({"ok": True, "job": store.public(job), "token": store.job_token(job["id"])},
                        status_code=201, headers=NO_STORE)


async def test_key(request: Request) -> Response:
    """Checks a user's AI key with one tiny request. The key is never stored or echoed."""
    if (d := _disabled()):
        return d
    if not _browser_ok(request):
        return _err(403, "Forbidden", "Open AutoClip from the official site.")
    ok, _ = await asyncio.to_thread(rate_limit, "autoclip:keytest", client_ip(request), 20, 600)
    if not ok:
        return _err(429, "RateLimited", "Too many key checks. Wait a few minutes.")
    try:
        body = await request.json()
        ai = byo.build(body.get("provider"), body.get("key"), body.get("model"))
    except byo.KeyError_ as e:
        return _err(400, "BadKey", str(e))
    except Exception:
        return _err(400, "BadRequest", "Send JSON {provider, key}.")
    if ai is None:
        return _err(400, "BadKey", "Paste your API key first.")
    try:
        res = await byo.test(ai)
    except Exception as e:  # noqa: BLE001 - message is already provider-safe; never include the key
        return _err(422, "KeyRejected", str(e)[:200] or "That key did not work.")
    return JSONResponse(res, headers=NO_STORE)


async def stt_models(request: Request) -> Response:
    if (d := _disabled()):
        return d
    return JSONResponse({"ok": True, **await asyncio.to_thread(models.listing)}, headers=NO_STORE)


async def stt_install(request: Request) -> Response:
    if (d := _disabled()):
        return d
    if not _browser_ok(request):
        return _err(403, "Forbidden", "Open AutoClip from the official site.")
    if not authenticate_admin(request, allow_bearer_jwt=False):
        ok, _ = await asyncio.to_thread(rate_limit, "autoclip:modelinstall", client_ip(request),
                                        config.MODEL_INSTALL_PER_DAY, 86400)
        if not ok:
            return _err(429, "RateLimited", "Model install limit reached for today.")
    try:
        body = await request.json()
        res = await asyncio.to_thread(models.install, str(body.get("id", "")).strip().lower())
    except ValueError as e:
        return _err(400, "BadRequest", str(e))
    except Exception:
        return _err(400, "BadRequest", "Send JSON {id}.")
    return JSONResponse({"ok": True, **res}, status_code=202, headers=NO_STORE)


async def get_job(request: Request) -> Response:
    job, e = _job_or_error(request)
    if e:
        return e
    return JSONResponse({"ok": True, "job": store.public(job)}, headers=NO_STORE)


async def cancel_job(request: Request) -> Response:
    job, e = _job_or_error(request)
    if e:
        return e
    job = await asyncio.to_thread(store.request_cancel, job["id"])
    return JSONResponse({"ok": True, "job": store.public(job)}, headers=NO_STORE)


async def job_file(request: Request) -> Response:
    job, e = _job_or_error(request)
    if e:
        return e
    name = request.path_params["name"]
    if not store.valid_artifact(name):
        return _err(404, "NotFound", "No such file.")
    path = os.path.join(store.clips_dir(job["id"]), name)
    if not os.path.isfile(path):
        return _err(404, "NotFound", "File not ready.")
    ext = os.path.splitext(name)[1]
    dl = request.query_params.get("download") == "1"
    nice = _nice_name(job, name)
    return FileResponse(path, media_type=_MEDIA_TYPES.get(ext, "application/octet-stream"),
                        filename=nice if dl else None,
                        headers={"Cache-Control": "private, max-age=3600"},
                        content_disposition_type="attachment" if dl else "inline")


def _nice_name(job: Dict[str, Any], name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9 _-]", "", (job.get("title") or "autoclip"))[:40].strip().replace(" ", "_") or "autoclip"
    return f"{base}_{name}"


async def job_zip(request: Request) -> Response:
    job, e = _job_or_error(request)
    if e:
        return e
    if job["status"] != "done":
        return _err(409, "NotReady", "Clips are not ready yet.")
    names = store.list_artifacts(job["id"])
    fd, tmp = tempfile.mkstemp(prefix="autoclip_", suffix=".zip")
    os.close(fd)

    def build() -> None:
        with zipfile.ZipFile(tmp, "w") as z:
            for n in names:
                p = os.path.join(store.clips_dir(job["id"]), n)
                z.write(p, n, compress_type=zipfile.ZIP_STORED if n.endswith(".mp4") else zipfile.ZIP_DEFLATED)

    await asyncio.to_thread(build)
    return FileResponse(tmp, media_type="application/zip", filename=_nice_name(job, "clips.zip"),
                        background=BackgroundTask(store._unlink, tmp), headers=NO_STORE)


# --------------------------------------------------------------------------- #
# Workers
# --------------------------------------------------------------------------- #

def _worker_ok(request: Request) -> bool:
    key = config.WORKER_KEY
    given = request.headers.get("x-worker-key", "")
    return len(key) >= 32 and bool(given) and hmac.compare_digest(given.encode(), key.encode())


def _wid(v: Any) -> str:
    return re.sub(r"[^A-Za-z0-9:._-]", "", str(v or ""))[:120]


async def w_claim(request: Request) -> Response:
    if not _worker_ok(request):
        return _err(401, "WorkerAuth", "Worker key required.")
    try:
        body = await request.json()
    except Exception:
        body = {}
    wid = _wid(body.get("worker_id"))
    if not wid:
        return _err(400, "BadRequest", "worker_id required.")
    job = await asyncio.to_thread(store.claim, wid)
    if not job:
        return Response(status_code=204)
    src = store.source_path(job["id"])
    return JSONResponse({"ok": True, "job": {
        "id": job["id"], "settings": job["settings"], "source_kind": job["source_kind"],
        "source_url": job.get("source_url"), "source_name": job.get("source_name"),
        "source_ext": os.path.splitext(src)[1] if src else None, "lease_seconds": config.LEASE_SECONDS}},
        headers=NO_STORE)


def _lease_ok(job_id: str, wid: str) -> bool:
    j = store.get(job_id)
    return bool(j and j["status"] == "running" and j.get("lease_owner") == wid)


async def w_source(request: Request) -> Response:
    if not _worker_ok(request):
        return _err(401, "WorkerAuth", "Worker key required.")
    job_id, wid = request.path_params["id"], _wid(request.query_params.get("worker_id"))
    if not store.valid_id(job_id) or not await asyncio.to_thread(_lease_ok, job_id, wid):
        return _err(409, "LeaseLost", "Not your job.")
    src = store.source_path(job_id)
    if not src:
        return _err(404, "NotFound", "No uploaded source.")
    return FileResponse(src, media_type="application/octet-stream")


async def w_heartbeat(request: Request) -> Response:
    if not _worker_ok(request):
        return _err(401, "WorkerAuth", "Worker key required.")
    body = await request.json()
    job_id = request.path_params["id"]
    if not store.valid_id(job_id):
        return _err(404, "NotFound", "No such job.")
    r = await asyncio.to_thread(store.heartbeat, job_id, _wid(body.get("worker_id")),
                                stage=str(body.get("stage") or "")[:40] or None,
                                progress=int(body.get("progress") or 0),
                                title=(str(body["title"])[:300] if body.get("title") else None),
                                duration=float(body["duration"]) if body.get("duration") else None)
    return JSONResponse(r, headers=NO_STORE)


async def w_artifact(request: Request) -> Response:
    if not _worker_ok(request):
        return _err(401, "WorkerAuth", "Worker key required.")
    job_id = request.path_params["id"]
    wid, name = _wid(request.query_params.get("worker_id")), request.query_params.get("name", "")
    if not store.valid_id(job_id) or not store.valid_artifact(name):
        return _err(400, "BadRequest", "Bad job or file name.")
    if not await asyncio.to_thread(_lease_ok, job_id, wid):
        return _err(409, "LeaseLost", "Not your job.")
    d = store.clips_dir(job_id)
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, f".{name}.{wid[-6:]}.part")
    limit, size = 2 * 1024 * 1024 * 1024, 0
    with open(tmp, "wb") as f:
        async for chunk in request.stream():
            size += len(chunk)
            if size > limit:
                f.close()
                store._unlink(tmp)
                return _err(413, "TooLarge", "Artifact too large.")
            f.write(chunk)
    os.replace(tmp, os.path.join(d, name))
    return JSONResponse({"ok": True, "bytes": size}, headers=NO_STORE)


async def w_complete(request: Request) -> Response:
    if not _worker_ok(request):
        return _err(401, "WorkerAuth", "Worker key required.")
    body = await request.json()
    job_id = request.path_params["id"]
    result = body.get("result") if isinstance(body.get("result"), dict) else None
    if not store.valid_id(job_id) or not result or not isinstance(result.get("clips"), list):
        return _err(400, "BadRequest", "result.clips required.")
    have = set(store.list_artifacts(job_id))
    for c in result["clips"]:
        if (c.get("files") or {}).get("video") not in have:
            return _err(409, "MissingArtifact", "Upload every clip before completing.")
    if result.get("title"):
        await asyncio.to_thread(store.heartbeat, job_id, _wid(body.get("worker_id")), title=str(result["title"])[:300],
                                duration=float(result.get("duration") or 0) or None)
    ok = await asyncio.to_thread(store.complete, job_id, _wid(body.get("worker_id")), result)
    return JSONResponse({"ok": ok}, status_code=200 if ok else 409, headers=NO_STORE)


async def w_fail(request: Request) -> Response:
    if not _worker_ok(request):
        return _err(401, "WorkerAuth", "Worker key required.")
    body = await request.json()
    job_id = request.path_params["id"]
    if not store.valid_id(job_id):
        return _err(404, "NotFound", "No such job.")
    ok = await asyncio.to_thread(store.fail, job_id, _wid(body.get("worker_id")), str(body.get("error") or "")[:500],
                                 retry=bool(body.get("retry")), cancelled=bool(body.get("cancelled")))
    return JSONResponse({"ok": ok}, headers=NO_STORE)


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #

async def admin_stats(request: Request) -> Response:
    if not authenticate_admin(request):
        return _err(401, "AdminAuthRequired", "Admin authentication required.")
    return JSONResponse({"ok": True, "jobs": await asyncio.to_thread(store.stats), "worker": inline_worker.status(),
                         "mode": config.WORKER_MODE}, headers=NO_STORE)


async def startup() -> None:
    inline_worker.start()


_P = "/api/autoclip"
routes_autoclip = [
    Route(f"{_P}/health", health, methods=["GET"]),
    Route(f"{_P}/options", options, methods=["GET"]),
    Route(f"{_P}/jobs", create_job, methods=["POST"]),
    Route(f"{_P}/keys/test", test_key, methods=["POST"]),
    Route(f"{_P}/models", stt_models, methods=["GET"]),
    Route(f"{_P}/models/install", stt_install, methods=["POST"]),
    Route(f"{_P}/jobs/{{id}}", get_job, methods=["GET"]),
    Route(f"{_P}/jobs/{{id}}/cancel", cancel_job, methods=["POST"]),
    Route(f"{_P}/jobs/{{id}}/files/{{name}}", job_file, methods=["GET", "HEAD"]),
    Route(f"{_P}/jobs/{{id}}/zip", job_zip, methods=["GET"]),
    Route(f"{_P}/workers/claim", w_claim, methods=["POST"]),
    Route(f"{_P}/workers/jobs/{{id}}/source", w_source, methods=["GET"]),
    Route(f"{_P}/workers/jobs/{{id}}/heartbeat", w_heartbeat, methods=["POST"]),
    Route(f"{_P}/workers/jobs/{{id}}/artifact", w_artifact, methods=["POST"]),
    Route(f"{_P}/workers/jobs/{{id}}/complete", w_complete, methods=["POST"]),
    Route(f"{_P}/workers/jobs/{{id}}/fail", w_fail, methods=["POST"]),
    Route(f"{_P}/admin/stats", admin_stats, methods=["GET"]),
]
