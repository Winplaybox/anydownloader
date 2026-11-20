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
MAX_UPLOAD_MB = _int("AUTOCLIP_MAX_UPLOAD_MB", 500, 0, 1_000_000)  # 0 = unlimited
MAX_SOURCE_MINUTES = _int("AUTOCLIP_MAX_SOURCE_MINUTES", 90, 0, 100_000)  # 0 = unlimited
MIN_FREE_GB = _int("AUTOCLIP_MIN_FREE_GB", 3, 0, 10_000)  # refuse new work below this much free disk (protects the server)
MAX_CLIPS = _int("AUTOCLIP_MAX_CLIPS", 12, 1, 50)
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

# Who pays for AI: users bring their own key (BYO). The server's shared key is only used for admins/automation
# unless the owner explicitly opens it to everyone with AUTOCLIP_SERVER_AI=1.
SERVER_AI_FOR_ALL = _e("AUTOCLIP_SERVER_AI", "0") == "1"
# Speech models users can install on the server (faster-whisper is multilingual: one model covers every language).
STT_MODELS = [
    {"id": "tiny", "name": "Fast", "size_mb": 75, "desc": "Fastest, fine for clear speech"},
    {"id": "base", "name": "Balanced", "size_mb": 145, "desc": "Good default for most videos"},
    {"id": "small", "name": "Accurate", "size_mb": 480, "desc": "Best for Indian languages and noisy audio (slower)"},
]
STT_IDS = {m["id"] for m in STT_MODELS}
MODEL_INSTALL_PER_DAY = _int("AUTOCLIP_MODEL_INSTALLS_PER_DAY", 3, 0, 50)

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
    {"id": "auto", "name": "Auto detect"},
    {"id": "hi", "name": "Hindi / Hinglish"}, {"id": "en", "name": "English"}, {"id": "mr", "name": "Marathi"},
    {"id": "gu", "name": "Gujarati"}, {"id": "bn", "name": "Bengali"}, {"id": "ta", "name": "Tamil"},
    {"id": "te", "name": "Telugu"}, {"id": "kn", "name": "Kannada"}, {"id": "ml", "name": "Malayalam"},
    {"id": "pa", "name": "Punjabi"}, {"id": "ur", "name": "Urdu"}, {"id": "ne", "name": "Nepali"},
    {"id": "si", "name": "Sinhala"}, {"id": "es", "name": "Spanish"}, {"id": "pt", "name": "Portuguese"},
    {"id": "fr", "name": "French"}, {"id": "de", "name": "German"}, {"id": "it", "name": "Italian"},
    {"id": "nl", "name": "Dutch"}, {"id": "sv", "name": "Swedish"}, {"id": "da", "name": "Danish"},
    {"id": "no", "name": "Norwegian"}, {"id": "fi", "name": "Finnish"}, {"id": "pl", "name": "Polish"},
    {"id": "cs", "name": "Czech"}, {"id": "ro", "name": "Romanian"}, {"id": "hu", "name": "Hungarian"},
    {"id": "el", "name": "Greek"}, {"id": "ru", "name": "Russian"}, {"id": "uk", "name": "Ukrainian"},
    {"id": "tr", "name": "Turkish"}, {"id": "ar", "name": "Arabic"}, {"id": "fa", "name": "Persian"},
    {"id": "he", "name": "Hebrew"}, {"id": "id", "name": "Indonesian"}, {"id": "ms", "name": "Malay"},
    {"id": "vi", "name": "Vietnamese"}, {"id": "th", "name": "Thai"}, {"id": "tl", "name": "Filipino"},
    {"id": "ja", "name": "Japanese"}, {"id": "ko", "name": "Korean"}, {"id": "zh", "name": "Chinese"},
    {"id": "sw", "name": "Swahili"}, {"id": "af", "name": "Afrikaans"},
]
STYLE_IDS = {s["id"] for s in CAPTION_STYLES}
LAYOUT_IDS = {s["id"] for s in LAYOUTS}
LANG_IDS = {s["id"] for s in LANGUAGES}
RESOLUTIONS = [720, 1080]

FONT_BY_LANG = {
    "hi": "Noto Sans Devanagari Black", "mr": "Noto Sans Devanagari Black", "ne": "Noto Sans Devanagari Black",
    "gu": "Noto Sans Gujarati Black", "bn": "Noto Sans Bengali Black", "ta": "Noto Sans Tamil Black",
    "te": "Noto Sans Telugu Black", "kn": "Noto Sans Kannada Black", "ml": "Noto Sans Malayalam Black",
    "pa": "Noto Sans Gurmukhi Black", "ur": "Noto Sans Arabic Black", "ar": "Noto Sans Arabic Black",
    "fa": "Noto Sans Arabic Black",
    # Not bundled: resolved by fontconfig on the server (apt: fonts-noto-core fonts-noto-cjk). Falls back safely.
    "ja": "Noto Sans CJK JP", "ko": "Noto Sans CJK KR", "zh": "Noto Sans CJK SC", "th": "Noto Sans Thai",
    "he": "Noto Sans Hebrew", "si": "Noto Sans Sinhala",
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
    stt = str(raw.get("stt_model", "auto")).strip().lower()
    focus = re.sub(r"\s+", " ", str(raw.get("focus", "") or "")).strip()[:300]
    return {
        "max_clips": int(num("max_clips", 5, 1, MAX_CLIPS)),
        "min_len": min_len,
        "max_len": max_len,
        "caption_style": style if style in STYLE_IDS else "pop",
        "layout": layout if layout in LAYOUT_IDS else "auto",
        "language": lang if lang in LANG_IDS else "auto",
        "accent": accent if _HEX.match(accent) else "#FFE500",
        "resolution": res if res in RESOLUTIONS else 1080,
        "hook": str(raw.get("hook", "1")).lower() not in ("0", "false", "no", "off"),
        "focus": focus,
        "stt_model": stt if stt in STT_IDS else "auto",
    }


def public_options() -> Dict[str, Any]:
    return {
        "caption_styles": CAPTION_STYLES, "layouts": LAYOUTS, "languages": LANGUAGES, "resolutions": RESOLUTIONS, "stt_models": STT_MODELS,
        "limits": {"daily": DAILY_LIMIT, "max_upload_mb": MAX_UPLOAD_MB, "max_source_minutes": MAX_SOURCE_MINUTES,
                   "max_clips": MAX_CLIPS, "retention_hours": RETENTION_HOURS},
        "source_domains": SOURCE_DOMAINS,
    }


def origin_allowed(origin: str) -> bool:
    o = (origin or "").strip().rstrip("/")
    if not o:
        return False
    if o in ALLOWED_ORIGINS or ORIGIN_RE.match(o):
        return True
    return bool(ALLOW_DEV and DEV_ORIGIN_RE.match(o))


def disk_ok() -> bool:
    """False when the data disk is nearly full, so we stop accepting work instead of crashing the box."""
    import shutil
    if not MIN_FREE_GB:
        return True
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        return shutil.disk_usage(DATA_DIR).free >= MIN_FREE_GB * 1e9
    except OSError:
        return True
