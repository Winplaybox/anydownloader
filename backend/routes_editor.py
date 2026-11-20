"""/api/editor - AI Video Editor (metered, credit-ledger backed, production-safe).

Endpoints:
  GET  /api/editor/options                   languages, voices, caption styles, modes + identity & limits
  GET  /api/editor/quota                     user identity and remaining credits
  GET  /api/editor/quote                     pre-action credit cost breakdown & balance preview
  POST /api/editor/quote                     pre-action credit cost breakdown
  GET  /api/editor/voice-preview?voice=ID    voice sample (static cache <20ms / generated wav)
  POST /api/editor/jobs                      multipart: file + settings -> credit debit -> job
  GET  /api/editor/jobs/{id}                 status / progress / result
  GET  /api/editor/jobs/{id}/file/{kind}     kind = video | srt | voiceover | metadata
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import shutil
import time
import uuid
from typing import Any, Dict, Tuple

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

try:
    from backend.security.token_vault import store
    from backend.security.zero_trust import authenticate_admin, client_ip, error, rate_limit
    from backend.services.video_editor import options as opts
    from backend.services.video_editor import pipeline, render, transcribe, tts
    from backend.services.auth_service import (
        deduct_credit_for_job,
        get_plan,
        refund_credit_for_job,
        resolve_request_identity,
    )
    from backend.utils.job_access import job_owner_matches
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from security.token_vault import store  # type: ignore
    from security.zero_trust import authenticate_admin, client_ip, error, rate_limit  # type: ignore
    from services.video_editor import options as opts  # type: ignore
    from services.video_editor import pipeline, render, transcribe, tts  # type: ignore
    from services.auth_service import (  # type: ignore
        deduct_credit_for_job,
        get_plan,
        refund_credit_for_job,
        resolve_request_identity,
    )
    from utils.job_access import job_owner_matches

DAILY_LIMIT = int(os.environ.get("EDITOR_DAILY_LIMIT", "2"))
MAX_UPLOAD_MB = int(os.environ.get("EDITOR_MAX_UPLOAD_MB", "100"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
_ALLOWED_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".3gp", ".avi"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
NO_STORE = {"Cache-Control": "no-store"}


def _client_key(request: Request) -> str:
    ip = client_ip(request)
    return hashlib.sha256(f"wpb:editor:{ip}".encode("utf-8")).hexdigest()[:16]


def _day_keys(client_key: str, now: Optional[dt.datetime] = None) -> Tuple[str, str, dt.datetime]:
    t = now or dt.datetime.now(IST)
    day = t.strftime("%Y%m%d")
    next_day = (t + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return f"wpb:editor:count:{day}:{client_key}", f"wpb:editor:refund:{day}:{client_key}", next_day


def quota_status(request: Request) -> Dict[str, Any]:
    identity = resolve_request_identity(request)
    unlimited = authenticate_admin(request, allow_bearer_jwt=False)
    _, _, reset = _day_keys(_client_key(request))
    return {
        "limit": None if unlimited else identity.get("credits", DAILY_LIMIT),
        "used": 0,
        "remaining": None if unlimited else identity.get("credits", 0),
        "resets_at": reset.isoformat(),
        "unlimited": unlimited,
        "identity": identity
    }


def calculate_quote(settings: Dict[str, Any], identity: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates upfront itemized feature-based credit cost and verifies plan entitlements."""
    res_str = str(settings.get("resolution", settings.get("height", 480))).lower().replace("p", "").strip()
    try:
        height = int(res_str)
    except ValueError:
        height = 480

    # 1. Base resolution export cost
    if height <= 480:
        base_cost = 1
        res_label = "480p SD Video Render"
    elif height <= 720:
        base_cost = 1
        res_label = "720p HD Video Render"
    elif height <= 1080:
        base_cost = 1
        res_label = "1080p Full HD Video Render"
    elif height <= 1440:
        base_cost = 2
        res_label = "2K QHD (1440p) Cinema Render"
    elif height <= 1800:
        base_cost = 2
        res_label = "3K Ultra (1800p) Cinema Render"
    elif height <= 2160:
        base_cost = 3
        res_label = "4K UHD Cinema Render"
    else:
        base_cost = 5
        res_label = "8K Ultra Cinema Render"

    breakdown = [
        {"key": "resolution", "name": res_label, "credits": base_cost, "icon": "video"}
    ]

    # 2. Voiceover & Audio Engine
    mode = str(settings.get("mode", "original")).lower().strip()
    voice = str(settings.get("voice", "") or "").strip()
    if mode in ("ai_voiceover", "ai_mix"):
        voice_cost = 1
        voice_label = f"AI Neural Voiceover ({voice or 'Standard'})"
    else:
        voice_cost = 0
        voice_label = "Original Video Audio (No AI Voice)"
    breakdown.append({"key": "voice", "name": voice_label, "credits": voice_cost, "icon": "mic"})

    # 3. AI Scriptwriting vs User Custom Script
    own_script = str(settings.get("script", "") or "").strip()
    brief = str(settings.get("brief", "") or "").strip()
    if own_script:
        script_cost = 0
        script_label = "Custom User Script (Zero AI Script Fee)"
    elif mode in ("ai_voiceover", "ai_mix") and brief:
        if len(brief) > 250:
            script_cost = 1
            script_label = "Longform Viral AI Script & Prompting"
        else:
            script_cost = 1
            script_label = "AI Auto-Script Generation from Brief"
    else:
        script_cost = 0
        script_label = "Standard Script / No Generation"
    breakdown.append({"key": "script", "name": script_label, "credits": script_cost, "icon": "wand"})

    # 4. Animated Captions Style
    cap_style = str(settings.get("caption_style", "pop")).lower().strip()
    if cap_style in ("none", "off", "no"):
        caption_cost = 0
        cap_label = "No Captions"
    else:
        caption_cost = 1
        cap_label = f"Animated Word-by-Word Captions ({cap_style.title()})"
    breakdown.append({"key": "captions", "name": cap_label, "credits": caption_cost, "icon": "captions"})

    # 5. Motion Graphics & Hook/CTA Overlays
    overlays = settings.get("overlays", True)
    if isinstance(overlays, str):
        overlays = overlays.lower() not in ("0", "false", "off", "no")
    overlay_cost = 1 if overlays else 0
    overlay_label = "Viral Hook Title + End CTA Graphics" if overlays else "No Hook/CTA Overlays"
    breakdown.append({"key": "overlays", "name": overlay_label, "credits": overlay_cost, "icon": "sparkles"})

    total_cost = base_cost + voice_cost + script_cost + caption_cost + overlay_cost
    addon_cost = total_cost - base_cost

    current_credits = identity.get("credits", 0)
    user_max_res = identity.get("max_resolution", 480)

    can_render = True
    reason = None
    if current_credits < total_cost:
        can_render = False
        reason = f"Insufficient credits. This render with selected features requires {total_cost} credit(s), you have {current_credits}."
    elif height > user_max_res:
        can_render = False
        reason = f"Your current plan ({identity.get('plan_name', 'Free')}) supports up to {user_max_res}p. Free trial gives up to 480p SD. Upgrade to unlock {height}p."

    return {
        "ok": True,
        "base_cost": base_cost,
        "addon_cost": addon_cost,
        "total_cost": total_cost,
        "breakdown": breakdown,
        "current_credits": current_credits,
        "balance_after": max(0, current_credits - total_cost),
        "can_render": can_render,
        "reason": reason,
        "plan": identity.get("plan", "free"),
        "user_max_resolution": user_max_res
    }


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #
async def options_handler(request: Request) -> Response:
    identity = resolve_request_identity(request)
    return JSONResponse({
        "ok": True,
        **opts.public_options(),
        "identity": identity,
        "quota": quota_status(request),
        "limits": {"max_seconds": identity.get("max_duration", pipeline.MAX_DURATION), "max_upload_mb": MAX_UPLOAD_MB}
    }, headers=NO_STORE)


async def quota_handler(request: Request) -> Response:
    identity = resolve_request_identity(request)
    return JSONResponse({"ok": True, "quota": quota_status(request), "identity": identity}, headers=NO_STORE)


async def quote_handler(request: Request) -> Response:
    """Pre-action credit cost quote."""
    identity = resolve_request_identity(request)
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
    else:
        body = dict(request.query_params)
    quote = calculate_quote(body, identity)
    return JSONResponse(quote, headers=NO_STORE)


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

    # 1. Fast static pre-baked cache on VPS
    static_dirs = [os.environ.get("PREVIEWS_DIR"), "/var/www/ovd-voice-previews", "/var/tmp/ovd-voice-previews"]
    for sdir in static_dirs:
        if sdir and os.path.exists(sdir):
            for ext in ("mp3", "wav"):
                static_p = os.path.join(sdir, f"{vid}.{ext}")
                if os.path.exists(static_p) and os.path.getsize(static_p) > 1000:
                    media_type = "audio/mpeg" if ext == "mp3" else "audio/wav"
                    return FileResponse(static_p, media_type=media_type, headers={
                        "Cache-Control": "public, max-age=31536000, immutable",
                        "Access-Control-Allow-Origin": "*"
                    })

    # 2. Dynamic cache
    path = os.path.join(tts.CACHE_DIR, "previews", f"{vid}.wav")
    if not os.path.exists(path):
        ok, _ = rate_limit("editorpv", client_ip(request), 30, 3600)
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
    return FileResponse(path, media_type="audio/wav", headers={
        "Cache-Control": "public, max-age=86400",
        "Access-Control-Allow-Origin": "*"
    })


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
    res = _field(form, "resolution", "480", 10)
    return {
        "language": lang, "mode": mode, "caption_style": style, "voice": voice if mode != "original" else None,
        "caption_script": script_kind, "accent": accent.upper(), "format": fmt, "resolution": res,
        "overlays": _field(form, "overlays", "1", 5) not in ("0", "false", "off"),
        "channel": _field(form, "channel", "", 120),
        "brief": _field(form, "brief", "", 4000),
        "script": _field(form, "script", "", 4000),
        "has_hook": _field(form, "has_hook", "0", 5) in ("1", "true", "yes"),
        "has_cta": _field(form, "has_cta", "0", 5) in ("1", "true", "yes"),
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

    identity = resolve_request_identity(request)
    ck = identity.get("user_id") or identity.get("guest_id") or _client_key(request)

    if _has_active_job(ck):
        return error(request, 409, "JobInProgress", "You already have a video being edited. Please wait for it to finish.")

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

    # Pre-action quote & balance validation
    quote = calculate_quote(settings, identity)
    if not quote["can_render"]:
        return JSONResponse({
            "ok": False,
            "error": quote["reason"],
            "quote": quote,
            "upgrade_required": True
        }, status_code=402)

    # Initialize job
    job = pipeline.new_job(settings, ck)
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
        return error(request, 413, "PayloadTooLarge", f"Video must be under {MAX_UPLOAD_MB} MB.")
    finally:
        await upload.close()

    # Deduct credit atomically
    cost = quote["total_cost"]
    deducted = deduct_credit_for_job(identity, cost=cost, job_id=job["id"])
    if not deducted:
        shutil.rmtree(pipeline.job_dir(job["id"]), ignore_errors=True)
        return JSONResponse({
            "ok": False,
            "error": "Insufficient credits to start render.",
            "upgrade_required": True
        }, status_code=402)

    async def on_finish(j: Dict[str, Any]) -> None:
        if j.get("status") == "failed":
            refund_credit_for_job(identity, amount=cost, job_id=j["id"], reason="Pipeline render failed")

    pipeline.start(job, src_path, on_finish)
    return JSONResponse({
        "ok": True,
        "job": pipeline.public_job(job),
        "quote": quote,
        "identity": identity
    }, status_code=202, headers=NO_STORE)


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


def _job_access_allowed(request: Request, job: Dict[str, Any]) -> bool:
    identity = resolve_request_identity(request)
    if job_owner_matches(job, identity, fallback_key=_client_key(request)):
        return True
    return bool(authenticate_admin(request, allow_bearer_jwt=False))


async def job_status_handler(request: Request) -> Response:
    jid = request.path_params.get("id", "")
    job = pipeline.load_job(jid)
    if not job or not _job_access_allowed(request, job):
        return error(request, 404, "NotFound", "Job not found or expired.")
    return JSONResponse({"ok": True, "job": pipeline.public_job(job)}, headers=NO_STORE)


async def job_file_handler(request: Request) -> Response:
    jid = request.path_params.get("id", "")
    kind = request.path_params.get("kind", "")
    job = pipeline.load_job(jid)
    if not job or not _job_access_allowed(request, job) or job.get("status") != "done":
        return error(request, 404, "NotFound", "Job is not ready.")
    p = pipeline.file_path(jid, kind)
    if not p:
        return error(request, 404, "NotFound", "Requested file is missing.")
    mime = {"video": "video/mp4", "srt": "text/plain; charset=utf-8",
            "voiceover": "audio/wav", "metadata": "text/plain; charset=utf-8"}.get(kind, "application/octet-stream")
    dl_name = f"ovd_ai_editor_{jid[:8]}.{'mp4' if kind == 'video' else 'srt' if kind == 'srt' else 'wav' if kind == 'voiceover' else 'txt'}"
    return FileResponse(p, media_type=mime, filename=dl_name,
                        headers={"Cache-Control": "private, no-store"})


async def health_handler(request: Request) -> Response:
    return JSONResponse({
        "ok": True,
        "service": "ai_video_editor",
        "concurrency": pipeline.CONCURRENCY,
        "timestamp": time.time()
    }, headers=NO_STORE)


async def warmup_handler(request: Request) -> Response:
    if not authenticate_admin(request, allow_bearer_jwt=False):
        return error(request, 401, "AdminAuthRequired", "Admin authentication required.")
    import asyncio
    err = await asyncio.to_thread(tts.warm_up)
    return JSONResponse({"ok": err is None, "error": err}, headers=NO_STORE)


routes_editor = [
    Route("/api/editor/health", health_handler, methods=["GET"]),
    Route("/api/editor/warmup", warmup_handler, methods=["POST"]),
    Route("/api/editor/options", options_handler, methods=["GET"]),
    Route("/api/editor/quota", quota_handler, methods=["GET"]),
    Route("/api/editor/quote", quote_handler, methods=["GET", "POST"]),
    Route("/api/editor/voice-preview", voice_preview_handler, methods=["GET"]),
    Route("/api/editor/jobs", create_job_handler, methods=["POST"]),
    Route("/api/editor/jobs/{id}", job_status_handler, methods=["GET"]),
    Route("/api/editor/jobs/{id}/file/{kind}", job_file_handler, methods=["GET"]),
]
