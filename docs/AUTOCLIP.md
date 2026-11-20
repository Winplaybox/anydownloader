# AutoClip AI — backend module

Long video (link or upload) → AI-picked moments → captioned 9:16 Shorts/Reels with hook text, SRT and
title/description/hashtags. Frontend: https://github.com/Winplaybox/AutoClip-AI (GitHub Pages).

No separate backend domain: it is an **isolated module inside the Winplaybox API** (`api.winplaybox.in`),
mounted at `/api/autoclip/*`.

| What | Where |
|---|---|
| Routes | `backend/routes_autoclip.py` |
| Engine | `backend/autoclip/` (config, store, media, speech, brain, reframe, clipper, pipeline, worker) |
| Data | `AUTOCLIP_DATA_DIR` (default `$JOBS_DIR/autoclip`): own SQLite DB + job folders |
| Tests | `python -m pytest backend/autoclip/tests -q` |

Shared infra it reuses (read-only): `llm_router` (Gemini via the existing `GEMINI_API_KEY`, Groq/OpenRouter
fallback), the faster-whisper model of the AI Video Editor, the editor's ASS caption styles + fonts,
ffmpeg helpers, `zero_trust` rate limits and admin auth. Turn it off with `AUTOCLIP_ENABLED=0`.

## How a job runs

1. `POST /api/autoclip/jobs` (link or multipart upload) → returns `job` + private `token`.
2. A worker claims it (lease + heartbeat, fenced so a stale worker can never overwrite a newer attempt).
3. Pipeline: download (yt-dlp) → probe → 16 kHz audio → loudness per second → word timestamps
   (faster-whisper) → Gemini reads the transcript in 10-min windows and returns clips (JSON) →
   clips snapped to sentence boundaries, de-duplicated, ranked → each clip rendered:
   face-centred / centre / blurred-fit 9:16, burned captions + hook, −14 LUFS audio, thumbnail, SRT.
4. Without any AI key the clips are picked by loudness + speech density (never fails silently).
5. Files expire after `AUTOCLIP_RETENTION_HOURS` (24 h). Sources are deleted as soon as a job finishes.

## Workers

* `AUTOCLIP_WORKER_MODE=inline` (default): the API process renders. Fine on the Hostinger VPS for light use.
* `AUTOCLIP_WORKER_MODE=remote`: the API only queues; one or more workers render:

```bash
# same VPS, private network (docker compose)
docker compose --profile autoclip up -d autoclip-worker

# any other box (workers.winplaybox.in, home PC, GPU machine)
pip install -r backend/requirements.txt   # needs ffmpeg on PATH
AUTOCLIP_API_BASE=https://api.winplaybox.in AUTOCLIP_WORKER_KEY=... GEMINI_API_KEY=... \
  python -m backend.autoclip.worker
```

The remote worker downloads links from its own IP (useful when YouTube blocks the server IP).

## Environment

| Variable | Default | |
|---|---|---|
| `AUTOCLIP_ENABLED` | `1` | `0` disables every route except health |
| `AUTOCLIP_WORKER_MODE` | `inline` | `inline` or `remote` |
| `AUTOCLIP_WORKER_KEY` | – | 32+ chars. Required for remote workers (`openssl rand -hex 32`) |
| `AUTOCLIP_SECRET` | `JOB_OWNER_SECRET` | HMAC key for job access tokens |
| `AUTOCLIP_DAILY_LIMIT` | `3` | videos per IP per day (`X-Admin-Key` = unlimited, `0` = off) |
| `AUTOCLIP_MAX_UPLOAD_MB` | `500` | |
| `AUTOCLIP_MAX_SOURCE_MINUTES` | `90` | |
| `AUTOCLIP_MAX_QUEUED` | `20` | queue cap before returning "busy" |
| `AUTOCLIP_CONCURRENCY` | `1` | inline renders per API process |
| `AUTOCLIP_RETENTION_HOURS` | `24` | |
| `AUTOCLIP_WHISPER_MODEL` | editor's model | e.g. `small` for better Hindi on a bigger box |
| `AUTOCLIP_ALLOWED_ORIGINS` | `https://winplaybox.github.io,https://clip.winplaybox.in,https://winplaybox.in` | plus any `*.winplaybox.in` |
| `AUTOCLIP_SOURCE_DOMAINS` | YouTube, Twitch, Kick, Vimeo, IG, FB, X, TikTok, … | link allowlist (SSRF guard) |
| `AUTOCLIP_COOKIES_FILE` | – | Netscape cookies for yt-dlp |
| `GEMINI_API_KEY` | – | shared with the rest of the API (never commit it) |

Reverse proxy: `deploy/Caddyfile` already allows 520 MB on `/api/autoclip/jobs` only (110 MB everywhere else).
Raise both if you raise `AUTOCLIP_MAX_UPLOAD_MB`.

## API

```
GET  /api/autoclip/health
GET  /api/autoclip/options
POST /api/autoclip/jobs                    JSON {url, settings{...}} | multipart file + settings(JSON)
GET  /api/autoclip/jobs/{id}               header X-Job-Token
POST /api/autoclip/jobs/{id}/cancel        header X-Job-Token
GET  /api/autoclip/jobs/{id}/files/{name}?t=TOKEN[&download=1]   clip_01.mp4|.jpg|.srt, clips.json
GET  /api/autoclip/jobs/{id}/zip?t=TOKEN
GET  /api/autoclip/admin/stats             X-Admin-Key
POST /api/autoclip/workers/claim | GET .../jobs/{id}/source | POST .../heartbeat|artifact|complete|fail   X-Worker-Key
```

Settings: `max_clips` 1–12, `min_len` 8–90 s, `max_len` 15–180 s, `caption_style`
pop|single|box|karaoke|minimal|none, `layout` auto|face|center|fit, `language` auto|hi|en|…,
`accent` #RRGGBB, `resolution` 720|1080, `hook` bool, `focus` free text (≤300 chars, e.g. "only funny moments").

Server-to-server (Make.com / n8n): send `X-API-Key: $AUTOMATION_API_KEY` instead of a browser Origin.
