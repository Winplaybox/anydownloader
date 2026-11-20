"""AutoClip AI - long video -> captioned vertical Shorts/Reels, as an isolated module of the Winplaybox API.

Isolation contract:
  * Everything lives in this package + `backend/routes_autoclip.py`. Routes are mounted under `/api/autoclip/*`.
  * Own data dir (AUTOCLIP_DATA_DIR), own SQLite DB, own env vars (AUTOCLIP_*), own rate-limit buckets.
  * Turning it off (AUTOCLIP_ENABLED=0) removes every route except /api/autoclip/health.
  * It only *reuses* shared infra read-only: llm_router (GEMINI_API_KEY), the faster-whisper model,
    the ASS caption renderer, ffmpeg helpers, zero_trust rate limiting / admin auth.

Compute runs either inline (inside the API process) or on a remote worker
(`python -m backend.autoclip.worker`) that talks to `/api/autoclip/workers/*` over HTTPS.
"""

__version__ = "1.0.0"
