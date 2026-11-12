"""
/api/editor - AI Video Editor (public, website-only, 2 videos per IP per day).

  GET  /api/editor/options                     languages, voices, caption styles, modes + your quota
  GET  /api/editor/quota                       {limit, used, remaining, resets_at}
  GET  /api/editor/voice-preview?voice=ID      short sample of a voice (cached wav)
  POST /api/editor/jobs                        multipart: file + settings -> {job}
  GET  /api/editor/jobs/{id}                   status / progress / result
  GET  /api/editor/jobs/{id}/file/{kind}       kind = video | srt | voiceover | metadata

Quota: EDITOR_DAILY_LIMIT (default 2) successful-or-running jobs per client IP per
calendar day in IST. Failed jobs are refunded. Admins (X-Admin-Key) are unlimited.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import shutil
from typing import Any, Dict, Tuple

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

try:
    from backend.security.token_vault import store
    from backend.security.zero_trust import authenticate_admin, client_ip, error, rate_limit
    from backend.services.video_editor import options as opts
    from backend.services.video_editor import pipeline, render, transcribe, tts
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from security.token_vault import store  # type: ignore
    from security.zero_trust import authenticate_admin, client_ip, error, rate_limit  # type: ignore
    from services.video_editor import options as opts  # type: ignore
    from services.video_editor import pipeline, render, transcribe, tts  # type: ignore

DAILY_LIMIT = int(os.environ.get("EDITOR_DAILY_LIMIT", "2"))
MAX_UPLOAD_MB = int(os.environ.get("EDITOR_MAX_UPLOAD_MB", "100"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
_ALLOWED_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".3gp", ".avi"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
NO_STORE = {"Cache-Control": "no-store"}


# --------------------------------------------------------------------------- #
# Quota
# --------------------------------------------------------------------------- #
def _client_key(request: Request) -> str:
    return hashlib.sha256(("editor:" + client_ip(request)).encode()).hexdigest()[:24]


def _day_keys(ck: str) -> Tuple[str, str, dt.datetime]:
    now = dt.datetime.now(IST)
    day = now.strftime("%Y%m%d")
    reset = (now + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return f"wpb:editor:used:{day}:{ck}", f"wpb:editor:refund:{day}:{ck}", reset


def quota_status(request: Request) -> Dict[str, Any]:
    used_k, ref_k, reset = _day_keys(_client_key(request))
    unlimited = bool(authenticate_admin(request, allow_bearer_jwt=False))
    try:
        used = max(0, store.get(used_k) - store.get(ref_k))
    except Exception:
        used = 0
    return {"limit": None if unlimited else DAILY_LIMIT, "used": used,
            "remaining": None if unlimited else max(0, DAILY_LIMIT - used),
            "resets_at": reset.isoformat(), "unlimited": unlimited}


def _consume(request: Request) -> Tuple[bool, Dict[str, Any]]:
    q = quota_status(request)
    if q["unlimited"]:
        return True, q
    used_k, ref_k, _ = _day_keys(_client_key(request))
    n = store.incr(used_k, 2 * 86400) - store.get(ref_k)
    if n > DAILY_LIMIT:
        store.incr(ref_k, 2 * 86400)  # undo this attempt
        return False, quota_status(request)
    return True, quota_status(request)


def _refund_for(client_key: str, created_day: str) -> None:
    store.incr(f"wpb:editor:refund:{created_day}:{client_key}", 2 * 86400)


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #
async def options_handler(request: Request) -> Response:
    return JSONResponse({"ok": True, **opts.public_options(), "quota": quota_status(request),
                         "limits": {"max_seconds": pipeline.MAX_DURATION, "max_upload_mb": MAX_UPLOAD_MB}},
                        headers=NO_STORE)


async def quota_handler(request: Request) -> Response:
    return JSONResponse({"ok": True, "quota": quota_status(request)}, headers=NO_STORE)


_PREVIEW_TEXT = {
    "hi": "नमस्ते दोस्तों! आज की वीडियो में देखिए कुछ खास।",
    "en": "Hey everyone! Watch till the end, this one is special.",
    "es": "¡Hola a todos! Mira hasta el final.", "fr": "Salut tout le monde ! Regardez jusqu'à la fin.",
    "it": "Ciao a tutti! Guardate fino alla fine.", "pt": "Olá pessoal! Assistam até o final.",
    "mr": "नमस्कार मित्रांनो! हा व्हिडिओ शेवटपर्यंत पहा.", "gu": "નમસ્તે મિત્રો! આ વિડિયો અંત સુધી જુઓ.",
    "bn": "নমস্কার বন্ধুরা! ভিডিওটি শেষ পর্যন্ত দেখুন।", "ta": "வணக்கம் நண்பர்களே! இந்த வீடியோவை கடைசி வரை பாருங்கள்.",
    "te": "నమస్కారం మిత్రులారా! ఈ వీడియోను చివరి వరకు చూడండి.", "kn": "ನಮಸ್ಕಾರ ಸ್ನೇಹಿತರೇ! ಈ ವಿಡಿಯೋವನ್ನು ಕೊನೆಯವರೆಗೂ ನೋಡಿ.",
    "ml": "നമസ്കാരം സുഹൃത്തുക്കളെ! ഈ വീഡിയോ അവസാനം വരെ കാണൂ.", "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਦੋਸਤੋ! ਇਹ ਵੀਡੀਓ ਅਖੀਰ ਤੱਕ ਦੇਖੋ।",
    "ur": "السلام علیکم دوستو! یہ ویڈیو آخر تک دیکھیں۔", "ar": "مرحبا بالجميع! شاهدوا الفيديو حتى النهاية.",
    "de": "Hallo zusammen! Schaut bis zum Ende.", "ru": "Всем привет! Смотрите до конца.",
    "id": "Halo semuanya! Tonton sampai habis.",
}


async def voice_preview_handler(request: Request) -> Response:
    vid = request.query_params.get("voice", "")
    voice = opts.VOICE_BY_ID.get(vid)
    if not voice:
        return error(request, 400, "InvalidField", "Unknown voice.")
    path = os.path.join(tts.CACHE_DIR, "previews", f"{vid}.wav")
    if not os.path.exists(path):
        ok, _ = rate_limit("editorpv", client_ip(request), 20, 3600)
        if not ok:
            return error(request, 429, "RateLimited", "Too many voice previews, try again later.")
        lang = voice["lang"]
        text = _PREVIEW_TEXT.get(lang) or _PREVIEW_TEXT.get(lang.split("-")[0]) or _PREVIEW_TEXT["en"]
        try:
            samples, _ = await tts.speak(text, vid, lang, 1.0)
        except Exception:
            return error(request, 503, "VoiceUnavailable", "This voice is not available right now.")
        import soundfile as sf

        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + f".{os.getpid()}.tmp.wav"
        sf.write(tmp, samples, tts.SR)
        os.replace(tmp, path)
    return FileResponse(path, media_type="audio/wav", headers={"Cache-Control": "public, max-age=86400"})


def _field(form: Any, name: str, default: str = "", max_len: int = 200) -> str:
    v = form.get(name)
    if v is None or hasattr(v, "filename"):
        return default
    return str(v).strip()[:max_len]


def _settings_from_form(form: Any) -> Tuple[Dict[str, Any], str]:
    lang = _field(form, "language", "hi", 10)
    if lang not in opts.LANG_BY_ID:
        return {}, "Unsupported language."
    mode = _field(form, "mode", "ai_mix", 20)
    if mode not in opts.MODE_IDS:
        return {}, "Unsupported voiceover mode."
    style = _field(form, "caption_style", "pop", 20)
    if style not in opts.STYLE_IDS:
        return {}, "Unsupported caption style."
    voice = _field(form, "voice", "", 40) or (opts.default_voice(lang) or "")
    if mode != "original" and not opts.voice_ok_for(voice, lang):
        return {}, "Pick a voice that speaks the selected language."
    script_kind = _field(form, "caption_script", "roman" if opts.LANG_BY_ID[lang]["indic"] else "native", 10)
    if script_kind not in ("roman", "native"):
        script_kind = "native"
    if not opts.LANG_BY_ID[lang]["indic"]:
        script_kind = "native"
    accent = _field(form, "accent", "#FFE500", 7)
    if not _HEX.match(accent):
        accent = "#FFE500"
    fmt = _field(form, "format", "vertical", 10)
    if fmt not in ("vertical", "original"):
        fmt = "vertical"
    return {
        "language": lang, "mode": mode, "caption_style": style, "voice": voice if mode != "original" else None,
        "caption_script": script_kind, "accent": accent.upper(), "format": fmt,
        "overlays": _field(form, "overlays", "1", 5) not in ("0", "false", "off"),
        "channel": _field(form, "channel", "", 120),
        "brief": _field(form, "brief", "", 4000),
        "script": _field(form, "script", "", 4000),
    }, ""


async def create_job_handler(request: Request) -> Response:
    ct = request.headers.get("content-type", "")
    if "multipart/form-data" not in ct:
        return error(request, 400, "InvalidRequest", "Send the video as multipart/form-data.")
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > (MAX_UPLOAD_MB + 1) * 1024 * 1024:
        return error(request, 413, "PayloadTooLarge", f"Video must be under {MAX_UPLOAD_MB} MB.")
    ok, _ = rate_limit("editorpost", client_ip(request), 10, 3600)
    if not ok:
        return error(request, 429, "RateLimited", "Too many attempts, try again later.")

    q = quota_status(request)
    if not q["unlimited"] and q["remaining"] <= 0:
        return error(request, 429, "DailyLimitReached",
                     f"Free limit reached: {DAILY_LIMIT} videos per day. Resets at midnight IST.", quota=q)

    ck = _client_key(request)
    if not q["unlimited"] and _has_active_job(ck):
        return error(request, 409, "JobInProgress", "You already have a video being edited. Wait for it to finish.")

    try:
        form = await request.form(max_files=1, max_fields=30)
    except Exception:
        return error(request, 400, "InvalidRequest", "Could not read the upload.")
    upload = form.get("file")
    if upload is None or not hasattr(upload, "filename"):
        return error(request, 400, "InvalidField", "Attach a video file.")
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in _ALLOWED_EXT and not (upload.content_type or "").startswith("video/"):
        return error(request, 400, "InvalidField", "Upload a video file (MP4, MOV, WEBM, MKV).")

    settings, err = _settings_from_form(form)
    if err:
        return error(request, 400, "InvalidField", err)

    allowed, q = _consume(request)
    if not allowed:
        return error(request, 429, "DailyLimitReached",
                     f"Free limit reached: {DAILY_LIMIT} videos per day. Resets at midnight IST.", quota=q)

    job = pipeline.new_job(settings, ck)
    day = dt.datetime.now(IST).strftime("%Y%m%d")
    src_path = os.path.join(pipeline.job_dir(job["id"]), "source" + (ext if ext in _ALLOWED_EXT else ".mp4"))
    size = 0
    try:
        with open(src_path, "wb") as out:
            while True:
                chunk = await upload.read(1 << 20)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_MB * 1024 * 1024:
                    raise ValueError("too large")
                out.write(chunk)
    except ValueError:
        shutil.rmtree(pipeline.job_dir(job["id"]), ignore_errors=True)
        if not q["unlimited"]:
            _refund_for(ck, day)
        return error(request, 413, "PayloadTooLarge", f"Video must be under {MAX_UPLOAD_MB} MB.")
    finally:
        await upload.close()

    unlimited = q["unlimited"]

    async def on_finish(j: Dict[str, Any]) -> None:
        if j.get("status") == "failed" and not unlimited:
            _refund_for(ck, day)

    pipeline.start(job, src_path, on_finish)
    return JSONResponse({"ok": True, "job": pipeline.public_job(job), "quota": quota_status(request)},
                        status_code=202, headers=NO_STORE)


def _has_active_job(ck: str) -> bool:
    try:
        names = os.listdir(pipeline.WORK_DIR)
    except OSError:
        return False
    for name in names:
        j = pipeline.load_job(name)
        if j and j.get("client") == ck and j.get("status") in ("queued", "running"):
            return True
    return False


async def job_status_handler(request: Request) -> Response:
    job = pipeline.load_job(request.path_params["id"])
    if not job:
        return error(request, 404, "NotFound", "Job not found or expired.")
    return JSONResponse({"ok": True, "job": pipeline.public_job(job)}, headers=NO_STORE)


_DL = {"video": ("video/mp4", "mp4"), "srt": ("application/x-subrip", "srt"),
       "voiceover": ("audio/wav", "wav"), "metadata": ("text/plain; charset=utf-8", "txt")}


async def job_file_handler(request: Request) -> Response:
    jid, kind = request.path_params["id"], request.path_params["kind"]
    job = pipeline.load_job(jid)
    path = pipeline.file_path(jid, kind) if job else None
    if not path:
        return error(request, 404, "NotFound", "File not found or expired.")
    media, ext = _DL[kind]
    name = f"ovd-ai-edit-{jid[:8]}.{ext}"
    inline = request.query_params.get("inline") == "1"
    return FileResponse(path, media_type=media, filename=None if inline else name,
                        headers={"Cache-Control": "private, max-age=3600"})


async def health_handler(request: Request) -> Response:
    """Deployment self-check: can this server actually edit videos?"""
    import asyncio
    import subprocess

    def check() -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        try:
            ff = render._bin("ffmpeg")
            filters = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True, timeout=20).stdout
            out["ffmpeg"] = {"path": ff, "ass_filter": " ass " in filters, "loudnorm": "loudnorm" in filters,
                             "sidechaincompress": "sidechaincompress" in filters}
        except Exception as e:
            out["ffmpeg"] = {"error": str(e)}
        model = os.path.join(tts.CACHE_DIR, "kokoro", os.path.basename(tts._MODEL_URL))
        out["kokoro"] = {"model_cached": os.path.exists(model)}
        try:
            import kokoro_onnx  # noqa: F401
            out["kokoro"]["installed"] = True
        except Exception:
            out["kokoro"]["installed"] = False
        out["whisper_installed"] = transcribe.available()
        out["fonts"] = sorted(os.listdir(render.FONTS_DIR)) if os.path.isdir(render.FONTS_DIR) else []
        out["quota_store"] = getattr(store, "name", "?")
        out["gemini_configured"] = bool(os.environ.get("GEMINI_API_KEY"))
        out["concurrency"] = pipeline.CONCURRENCY
        return out

    return JSONResponse({"ok": True, **await asyncio.to_thread(check)}, headers=NO_STORE)


async def warmup_handler(request: Request) -> Response:
    """Admin: download the Kokoro model now instead of on the first job."""
    import asyncio

    if not authenticate_admin(request, allow_bearer_jwt=False):
        return error(request, 401, "AdminAuthRequired", "Admin authentication required.")
    err = await asyncio.to_thread(tts.warm_up)
    return JSONResponse({"ok": err is None, "error": err}, headers=NO_STORE)


routes_editor = [
    Route("/api/editor/health", health_handler, methods=["GET"]),
    Route("/api/editor/warmup", warmup_handler, methods=["POST"]),
    Route("/api/editor/options", options_handler, methods=["GET"]),
    Route("/api/editor/quota", quota_handler, methods=["GET"]),
    Route("/api/editor/voice-preview", voice_preview_handler, methods=["GET"]),
    Route("/api/editor/jobs", create_job_handler, methods=["POST"]),
    Route("/api/editor/jobs/{id}", job_status_handler, methods=["GET"]),
    Route("/api/editor/jobs/{id}/file/{kind}", job_file_handler, methods=["GET"]),
]
