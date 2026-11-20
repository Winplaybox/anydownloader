"""All AutoClip settings. Env only; nothing secret is ever logged or returned."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List

_e = os.environ.get


def _int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(_e(name, str(default)))))
    except ValueError:
        return default


ENABLED = _e("AUTOCLIP_ENABLED", "1") != "0"
DATA_DIR = os.path.abspath(_e("AUTOCLIP_DATA_DIR") or os.path.join(_e("JOBS_DIR", "/tmp/ovd_jobs"), "autoclip"))
DB_PATH = os.path.join(DATA_DIR, "autoclip.db")

# inline = the API process renders; remote = only workers (python -m backend.autoclip.worker) render.
WORKER_MODE = (_e("AUTOCLIP_WORKER_MODE", "inline") or "inline").strip().lower()
WORKER_KEY = (_e("AUTOCLIP_WORKER_KEY") or "").strip()
INLINE_CONCURRENCY = _int("AUTOCLIP_CONCURRENCY", 1, 1, 4)
LEASE_SECONDS = _int("AUTOCLIP_LEASE_SECONDS", 180, 60, 1800)
MAX_ATTEMPTS = _int("AUTOCLIP_MAX_ATTEMPTS", 2, 1, 5)

# Abuse limits (admins via X-Admin-Key are unlimited)
DAILY_LIMIT = _int("AUTOCLIP_DAILY_LIMIT", 3, 0, 1000)
MAX_UPLOAD_MB = _int("AUTOCLIP_MAX_UPLOAD_MB", 500, 10, 4096)
MAX_SOURCE_MINUTES = _int("AUTOCLIP_MAX_SOURCE_MINUTES", 90, 1, 600)
MAX_QUEUED = _int("AUTOCLIP_MAX_QUEUED", 20, 1, 500)
RETENTION_HOURS = _int("AUTOCLIP_RETENTION_HOURS", 24, 1, 24 * 30)

# Rendering
WHISPER_MODEL = _e("AUTOCLIP_WHISPER_MODEL", "")  # empty -> reuse the editor's shared model (EDITOR_WHISPER_MODEL)
X264_PRESET = _e("AUTOCLIP_X264_PRESET", "veryfast")
X264_CRF = _e("AUTOCLIP_X264_CRF", "21")
FFMPEG_THREADS = _e("AUTOCLIP_FFMPEG_THREADS", "0")
COOKIES_FILE = _e("AUTOCLIP_COOKIES_FILE", "")

# AI. Gemini key is the shared GEMINI_API_KEY used by llm_router; this only picks the budget.
LLM_BUDGET_S = _int("AUTOCLIP_LLM_BUDGET_S", 90, 10, 600)
WINDOW_SECONDS = _int("AUTOCLIP_WINDOW_SECONDS", 600, 120, 1800)

# Job access tokens: HMAC(secret, job_id). Falls back to the API-wide JOB_OWNER_SECRET.
SECRET = (_e("AUTOCLIP_SECRET") or _e("JOB_OWNER_SECRET") or "").strip()

# Browser origins allowed to call /api/autoclip (GitHub Pages + winplaybox.in subdomains).
_DEFAULT_ORIGINS = "https://winplaybox.github.io,https://clip.winplaybox.in,https://winplaybox.in"
ALLOWED_ORIGINS: List[str] = [o.strip().rstrip("/") for o in _e("AUTOCLIP_ALLOWED_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()]
ORIGIN_RE = re.compile(r"^https://([a-z0-9-]+\.)*winplaybox\.in$")
DEV_ORIGIN_RE = re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$")
ALLOW_DEV = _e("WPB_ENV", "").lower() not in ("prod", "production") or _e("AUTOCLIP_ALLOW_DEV_ORIGINS") == "1"

# Source sites accepted for links (yt-dlp). Anything else is refused to avoid SSRF through the generic extractor.
SOURCE_DOMAINS = [d.strip().lower() for d in _e(
    "AUTOCLIP_SOURCE_DOMAINS",
    "youtube.com,youtu.be,twitch.tv,kick.com,vimeo.com,dailymotion.com,rumble.com,facebook.com,fb.watch,"
    "instagram.com,x.com,twitter.com,tiktok.com,reddit.com,streamable.com,drive.google.com",
).split(",") if d.strip()]

# --------------------------------------------------------------------------- #
# User-facing options
# --------------------------------------------------------------------------- #
CAPTION_STYLES = [
    {"id": "pop", "name": "Pop Highlight", "desc": "3 words, spoken word pops in the accent colour"},
    {"id": "single", "name": "One Word Punch", "desc": "One big word at a time, fast"},
    {"id": "box", "name": "Boxed Phrase", "desc": "Phrase on a dark box, clean news look"},
    {"id": "karaoke", "name": "Karaoke Fill", "desc": "Words fill with colour as spoken"},
    {"id": "minimal", "name": "Minimal", "desc": "Full sentence, soft shadow"},
    {"id": "none", "name": "No captions", "desc": "Clean clip, no burned-in text"},
]
LAYOUTS = [
    {"id": "auto", "name": "Auto", "desc": "Follows the face when there is one, else blurred fit for wide shots"},
    {"id": "face", "name": "Face crop", "desc": "Full-height 9:16 crop centred on the speaker"},
    {"id": "center", "name": "Center crop", "desc": "Full-height 9:16 crop from the middle"},
    {"id": "fit", "name": "Fit + blur", "desc": "Whole frame, blurred background (slides, gameplay, screens)"},
]
LANGUAGES = [
    {"id": "auto", "name": "Auto detect"}, {"id": "hi", "name": "Hindi / Hinglish"}, {"id": "en", "name": "English"},
    {"id": "mr", "name": "Marathi"}, {"id": "gu", "name": "Gujarati"}, {"id": "bn", "name": "Bengali"},
    {"id": "ta", "name": "Tamil"}, {"id": "te", "name": "Telugu"}, {"id": "kn", "name": "Kannada"},
    {"id": "ml", "name": "Malayalam"}, {"id": "pa", "name": "Punjabi"}, {"id": "ur", "name": "Urdu"},
    {"id": "es", "name": "Spanish"}, {"id": "pt", "name": "Portuguese"}, {"id": "fr", "name": "French"},
    {"id": "de", "name": "German"}, {"id": "ar", "name": "Arabic"}, {"id": "id", "name": "Indonesian"},
]
STYLE_IDS = {s["id"] for s in CAPTION_STYLES}
LAYOUT_IDS = {s["id"] for s in LAYOUTS}
LANG_IDS = {s["id"] for s in LANGUAGES}
RESOLUTIONS = [720, 1080]

FONT_BY_LANG = {
    "hi": "Noto Sans Devanagari Black", "mr": "Noto Sans Devanagari Black", "gu": "Noto Sans Gujarati Black",
    "bn": "Noto Sans Bengali Black", "ta": "Noto Sans Tamil Black", "te": "Noto Sans Telugu Black",
    "kn": "Noto Sans Kannada Black", "ml": "Noto Sans Malayalam Black", "pa": "Noto Sans Gurmukhi Black",
    "ur": "Noto Sans Arabic Black", "ar": "Noto Sans Arabic Black",
}
DEFAULT_FONT = "Inter Black"

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def clean_settings(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate/normalise user settings. Never trusts the client; unknown keys are dropped."""
    def num(key: str, default: float, lo: float, hi: float) -> float:
        try:
            return max(lo, min(hi, float(raw.get(key, default))))
        except (TypeError, ValueError):
            return default

    min_len = int(num("min_len", 20, 8, 90))
    max_len = int(num("max_len", 60, 15, 180))
    if max_len < min_len + 5:
        max_len = min_len + 5
    style = str(raw.get("caption_style", "pop")).strip().lower()
    layout = str(raw.get("layout", "auto")).strip().lower()
    lang = str(raw.get("language", "auto")).strip().lower()
    accent = str(raw.get("accent", "#FFE500")).strip()
    try:
        res = int(str(raw.get("resolution", 1080)).lower().replace("p", ""))
    except ValueError:
        res = 1080
    focus = re.sub(r"\s+", " ", str(raw.get("focus", "") or "")).strip()[:300]
    return {
        "max_clips": int(num("max_clips", 5, 1, 12)),
        "min_len": min_len,
        "max_len": max_len,
        "caption_style": style if style in STYLE_IDS else "pop",
        "layout": layout if layout in LAYOUT_IDS else "auto",
        "language": lang if lang in LANG_IDS else "auto",
        "accent": accent if _HEX.match(accent) else "#FFE500",
        "resolution": res if res in RESOLUTIONS else 1080,
        "hook": str(raw.get("hook", "1")).lower() not in ("0", "false", "no", "off"),
        "focus": focus,
    }


def public_options() -> Dict[str, Any]:
    return {
        "caption_styles": CAPTION_STYLES, "layouts": LAYOUTS, "languages": LANGUAGES, "resolutions": RESOLUTIONS,
        "limits": {"daily": DAILY_LIMIT, "max_upload_mb": MAX_UPLOAD_MB, "max_source_minutes": MAX_SOURCE_MINUTES,
                   "max_clips": 12, "retention_hours": RETENTION_HOURS},
        "source_domains": SOURCE_DOMAINS,
    }


def origin_allowed(origin: str) -> bool:
    o = (origin or "").strip().rstrip("/")
    if not o:
        return False
    if o in ALLOWED_ORIGINS or ORIGIN_RE.match(o):
        return True
    return bool(ALLOW_DEV and DEV_ORIGIN_RE.match(o))
