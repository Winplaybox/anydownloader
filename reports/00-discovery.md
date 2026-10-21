# Discovery Report: ovd.winplaybox.in (Phase 1)

**Date**: 2026-10-21  
**Author**: Senior Full-Stack Engineering Agent  
**Target Repository**: `C:\Users\sagar\Desktop\Project\anydownloader`  
**Live Production URL**: `https://ovd.winplaybox.in`  
**Backend API**: `https://anydownloader-backend-vvbj.onrender.com`  

---

## 1. System Architecture & Tech Stack

### 1.1 Frontend
- **Framework**: React 19 (`react: ^19.0.0`, `react-dom: ^19.0.0`, `react-router-dom: ^7.18.4`)
- **Bundler & Tooling**: Vite 8.3.4, `@vitejs/plugin-react: ^6.1.2`
- **Styling**: Tailwind CSS v4 (`tailwindcss: ^4.3.3`, `@tailwindcss/vite: ^4.3.3`)
- **Iconography**: Lucide React (`lucide-react: ^1.16.0`)
- **Hosting**: Hostinger Static Web Hosting (`ovd.winplaybox.in`) using Apache HTTP Server with `.htaccess` fallback to `index.html`.

### 1.2 Backend
- **Language / Runtime**: Python 3.11.9
- **Framework**: Starlette (`starlette>=0.36.0`) + Uvicorn (`uvicorn>=0.27.0`)
- **Core Dependencies**: `yt-dlp>=2025.1.0`, `static-ffmpeg>=2.5`, `httpx>=0.27.0`
- **Hosting**: Render (`https://anydownloader-backend-vvbj.onrender.com`) via `render.yaml` (Free web service).

### 1.3 Media Extraction Strategy (Current)
- Monolithic `backend/main.py` (~2,500 lines) with per-platform extraction methods:
  - `extract_youtube`: calls `extract_media_base` via `yt-dlp` with custom options.
  - `extract_facebook`: tries `yt-dlp` then falls back to OpenGraph meta tag scraping.
  - `extract_instagram`: scrapes Instagram via public queries and fallback HTML scraping.
  - `extract_tiktok`: calls `yt-dlp` via `extract_media_base`.
  - `extract_twitter`: queries `https://api.fxtwitter.com/...` with fallback to `yt-dlp`.
  - `extract_pinterest`: scrapes Pinterest OpenGraph and JSON embeddings.

### 1.4 Download Proxy & Security (Current)
- `/api/stream`: Accepts raw CDN URL via query string `?url=...&filename=...`.
- Uses regex allowlist `is_safe_cdn_url` (fbcdn, cdninstagram, twimg, googlevideo, ytimg, tiktokcdn).
- **Vulnerabilities**: No HMAC cryptographic signing on stream URLs; token parameters are easily forged or stripped; no server-side IP resolution check against private/loopback CIDRs (SSRF risk).

---

## 2. Route & Endpoint Map

### 2.1 Backend Endpoints
| Method | Path | Purpose | Request Body | Current Response |
|---|---|---|---|---|
| `GET` | `/health` / `/api/health` | Healthcheck | None | `{"status": "ok", "app": "anydownloader-backend"}` |
| `POST` | `/api/extract` | Generic extractor | `{"url": "..."}` | `{"success": true, "data": {...}}` or `{"success": false, "error": "..."}` |
| `POST` | `/api/{platform}/extract` | Platform extractor | `{"url": "..."}` | `{"success": true, "platform": "...", "data": {...}}` |
| `POST` | `/api/{platform}/{feature}` | Feature extractor | `{"url": "..."}` | `{"success": true, "platform": "...", "feature": "...", "data": {...}}` |
| `GET` | `/api/stream` | CDN Stream proxy | Query `url`, `filename` | Raw binary streaming response with `Content-Disposition` |
| `GET` | `/api/download_video` | Server-side ffmpeg mux | Query `url`, `height`, `filename` | File stream (MP4) |
| `GET` | `/api/download_audio` | Server-side audio extraction | Query `url`, `filename` | File stream (MP3) |

### 2.2 Frontend Routes
- `/`: Home Page (generic input + platform showcases)
- `/youtube/*`: `/youtube/youtube-video-downloader`, `/youtube/youtube-mp4`, `/youtube/youtube-shorts`, `/youtube/youtube-mp3`, `/youtube/youtube-transcript`, `/youtube/youtube-subtitles`, `/youtube/youtube-thumbnails`, `/youtube/top-100-youtube-channels`
- `/facebook/*`: `/facebook/facebook-video-downloader`, `/facebook/facebook-reels`, `/facebook/facebook-posts`, `/facebook/facebook-transcript`, `/facebook/top-100-facebook-pages`
- `/instagram/*`: `/instagram/instagram-downloader`, `/instagram/instagram-reels`, `/instagram/instagram-photos`, `/instagram/instagram-stories`, `/instagram/top-100-instagram-accounts`
- `/twitter/*`: `/twitter/twitter-video-downloader`, `/twitter/twitter-mp3-downloader`, `/twitter/twitter-image-downloader`, `/twitter/twitter-gif-downloader`, `/twitter/twitter-profile-downloader`
- `/tiktok/*`: `/tiktok/tiktok-downloader`
- `/pinterest/*`: `/pinterest/pinterest-video-downloader`, `/pinterest/pinterest-photo-downloader`, `/pinterest/pinterest-gif-downloader`, `/pinterest/pinterest-story-downloader`, `/pinterest/pinterest-board-downloader`, `/pinterest/pinterest-profile-downloader`
- Info & Legal: `/blogs`, `/updates`, `/security`, `/terms-of-service`, `/privacy-policy`, `/contact`

---

## 3. Bug Reproduction: Twitter "URL is missing in input"

### 3.1 Exact Root Cause
1. **DOM Corruption in `HeroDownloader.jsx`**:
   In `src/components/HeroDownloader.jsx` lines 106–118:
   Inside the input field icon container `<span className="shrink-0">`, an accidental ternary branch for `activeCategory === 'twitter'` was injected:
   ```jsx
   <span className="shrink-0">
     {activeCategory === 'youtube' ? (
       <YoutubeIcon className="w-5 h-5 text-red-500" />
     ) : activeCategory === 'twitter' ? (
       <>
         <button onClick={() => setUrl('...')}>🚀 NASA Tweet (Video)</button>
         <button onClick={() => setUrl('...')}>🛰️ SpaceX (Clip)</button>
         <button onClick={() => setUrl('@NASA')}>👤 @NASA (Profile DP)</button>
       </>
     ) : ...}
   </span>
   ```
   This caused all quick sample buttons to render **inside the input box itself**, visually collapsing and hiding the actual `<input>` field. When a user visited any Twitter page and clicked the primary action button ("Fetch Media"), `url` was empty/blank.
2. **Raw Error Leakage**:
   When the empty payload `{ "url": "" }` hit the backend, the backend returned HTTP 400:
   `{"success": false, "error": "Please provide a valid media URL"}`.
   In `ToolPage.jsx` and `HomePage.jsx`, the client unconditionally ran:
   `setError(json.error)`
   This dumped raw backend/upstream exception strings straight into the user's interface without sanitization or mapped error codes.

---

## 4. Phase 1 Platform Gap Table

| Platform | Feature | Status | Notes |
|---|---|---|---|
| **Twitter / X** | Single Video (MP4) | ⚠️ Partial | Works via FxTwitter/yt-dlp, but UI was broken by input bar displacement |
| **Twitter / X** | Multi-Image Tweet (up to 4) | ⚠️ Partial | Supported in backend, but needs carousel/grid in UI |
| **Twitter / X** | Single Image (JPG/PNG) | ⚠️ Partial | Supported in backend, needs Phase 1 Base result card |
| **Twitter / X** | Looping GIF | ⚠️ Partial | Handled as MP4, needs proper tag/chip |
| **YouTube** | Video (MP4) | ✅ Works | Progressive streams work, separated streams need server-side mux |
| **YouTube** | Thumbnail (Image) | ✅ Works | High-res image available |
| **Facebook** | Video / Watch (MP4) | ✅ Works | Public videos work; login-gated videos need clear typed error `PRIVATE_OR_RESTRICTED` |
| **Facebook** | Photo (Single/Multi) | ✅ Works | Public photos extractable via OpenGraph |
| **Instagram** | Reel (MP4) | ✅ Works | Public reels extractable |
| **Instagram** | Photo / Carousel (Images) | ✅ Works | Public posts extractable |
| **TikTok** | Video (No Watermark MP4) | ✅ Works | Public videos extractable |
| **TikTok** | Photo Slideshow (Images) | ⚠️ Unknown | Needs explicit extractor handler |
| **Cross-Platform** | Audio/MP3 | 🚫 Out of Scope | Phase 1 strict scope: Video + Image only. Must be hidden. |
| **Cross-Platform** | Subtitles/Transcripts | 🚫 Out of Scope | Phase 1 strict scope: Must be hidden. |
| **Cross-Platform** | Browser Extension | 🚫 Out of Scope | Phase 1 strict scope: Must be hidden from main UI. |

---

## 5. Architectural Upgrade Requirements (Phase 2 Target)
1. **New Unified API**: `POST /api/resolve` with strict schema validation.
2. **Structured Error Contract**: Typed codes (`URL_MISSING`, `URL_INVALID`, `PLATFORM_UNSUPPORTED`, `NO_MEDIA`, `NOT_FOUND`, `PRIVATE_OR_RESTRICTED`, `RATE_LIMITED`, `UPSTREAM_FAILED`, `TIMEOUT`, `INTERNAL`) with friendly UI copy mapping.
3. **Signed Download Proxy**: `GET /api/download?token=<signed>` with HMAC token, 5-minute TTL, SSRF IP-level checks, and stream forwarding.
4. **Normalized URL Engine**: Unit-tested URL normalizer supporting tracking param stripping, redirect resolution, and canonical host mapping.
5. **Base Design System**: Rebuild all UI components to Uber's Base Web standards (black/white, high contrast, 8px grid, no colorful gradients).
