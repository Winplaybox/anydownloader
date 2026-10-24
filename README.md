# OVD Downloader (ovd.winplaybox.in) — Master v3 Architecture

OVD is a production-grade, highly resilient social video and image downloader built on Python 3.12, FastAPI, ffmpeg, and React 19 + Vite.

---

## 0. Core Architectural Principles

1. **Platform registry, not hardcoding:** Platforms live in `platforms.yaml`. No platform lists, regexes, chips, SEO pages or sitemap entries are hardcoded.
2. **Engines as plugins:** `yt-dlp`, `gallery-dl`, `tikwm`, `fxtwitter`, `reddit`, `pytubefix`, and paid APIs all implement one universal `Engine` protocol. A platform is an ordered fallback chain per content type.
3. **One Normalized Schema:** Every platform and engine returns a strictly typed schema with honest metadata (stats without fake 0s).
4. **Fail soft:** If one engine fails, the next engine in the fallback chain executes automatically.
5. **Self-healing & Health status:** Nightly self-tests run canonical public test URLs and automatically downgrade broken platforms to `degraded` so users see transparent status banners instead of silent errors.

---

## 1. Quick Start / Running Locally

### Backend (Python 3.12 + FastAPI)
```bash
# 1. Enter repository
cd backend

# 2. Install dependencies (requires ffmpeg installed on system)
pip install -r requirements.txt

# 3. Start API server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation (Swagger UI): `http://localhost:8000/docs`
Platform Capabilities: `http://localhost:8000/api/platforms`

### Frontend (React 19 + Tailwind + Vite)
```bash
# In repository root
npm install
npm run dev
```
Runs at `http://localhost:5173`.

---

## 2. How to Add a New Platform in 5 Minutes

To add a new platform, simply add an entry to `platforms.yaml`:

```yaml
- id: soundcloud
  name: SoundCloud
  tier: A                      # A = custom adapter + nightly self-test, B = generic/beta
  domains: [soundcloud.com, m.soundcloud.com]
  urlPatterns:
    - {type: audio, regex: "soundcloud\.com/([^/]+)/([^/?]+)"}
  routes:
    audio: [ytdlp]
  needsCookies: optional
  contentTypes: [audio, thumbnails]
  selfTestUrls: {audio: "https://soundcloud.com/user/track"}
  seo: {slug: soundcloud-audio-downloader, title: "SoundCloud Audio Downloader", description: "Download SoundCloud audio tracks in MP3."}
```

From this single YAML entry, OVD automatically:
- Generates URL detection and Auto-Detect pattern matching.
- Generates platform chips in the UI with dynamic status (`ok | degraded | down | beta`).
- Generates SEO routes and sitemap XML entries (`scripts/generate_seo_pages.py`).
- Configures automated self-test runs.

---

## 3. Endpoints

- `GET  /api/health` — Health status and server uptime
- `GET  /api/platforms` — Registry capabilities and real-time status (`ok|degraded|down|beta`)
- `POST /api/extract {url, allow_generic?}` — Normalized extraction schema
- `POST /api/resolve {url, allow_generic?}` — Direct resolution endpoint
- `GET  /api/download?token=` — Streamed proxy download with Range support & Content-Disposition
- `POST /api/jobs {tokens[], action: merge|mp3|zip}` — Asynchronous ffmpeg video+audio merge and audio conversion
- `GET  /api/jobs/{id}` — Job status and progress
- `GET  /api/jobs/{id}/file` — Download completed job output
- `POST /api/zip {tokens[]}` — Streamed multi-item ZIP archive
- `GET  /api/proxy-image?token=` — Secure image proxy (prevents CORS & hotlink blocking)
- `GET  /admin/engine-versions` — Inspect active yt-dlp, gallery-dl, and ffmpeg versions (Bearer token required)
- `POST /admin/update-engines` — Hot-update extraction engines without restarting container

---

## 4. Cookie Pool Setup

Place Netscape-format cookie files in the `COOKIE_POOL_PATH` directory (e.g., `./cookies/`):
- `youtube.txt`
- `instagram.txt`
- `facebook.txt`
- `twitter.txt`

Never commit cookie files to git. Rotation and burner account management should be configured via environment secrets.

---

## 5. Remote Worker Mode (Residential IP Bypass)

When hosting on public cloud providers (Render, AWS, DigitalOcean, Hetzner), social platforms like YouTube and Instagram may throttle or block datacenter IPs.

Set up an optional worker on a residential machine behind a Cloudflare Tunnel:
```env
WORKER_URL=https://worker.yourdomain.com
WORKER_SECRET=your_worker_shared_secret
```
The primary API will delegate extraction directly to the residential worker without requiring changes to the user interface or frontend.

---

## 6. Deployment

### Docker Compose
```bash
cp .env.example .env
docker compose up -d --build
```

### Static Frontend Build (for CDN / Hostinger)
```bash
npm run build
```
Generates production bundle in `dist/` and synchronizes assets to root `index.html` for Hostinger Apache hosting.

---

## 7. Known Platform Limitations & Policies

- **Private & DRM Content:** Out of scope. Netflix, Spotify, Prime Video, and password-protected accounts are denied with `UNSUPPORTED_URL` or `PRIVATE_CONTENT`.
- **Instagram Posts/Carousels:** Photo posts and multi-slide carousels require gallery-dl with session cookies; reels work via public yt-dlp.
- **YouTube 1080p+ Audio:** 1080p, 1440p, and 4K streams on YouTube are video-only; OVD merges them automatically with the best audio stream using ffmpeg via the background job manager.
- **Bandwidth & Rate Limits:** Cloudflare CDN caching is recommended in front of static and thumbnail assets.
