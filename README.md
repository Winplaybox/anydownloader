# AnyDownloader (anydownloader.winplaybox.in)

> High-speed Universal Media Downloader powered by Python (yt-dlp), Starlette/Uvicorn, and React 19 + Vite.

## Features
- **YouTube Video & Audio Extraction:** Supports 1080p, 720p, 480p, 360p video, and MP3 (320kbps / 192kbps) / M4A audio.
- **Multi-Platform Ready:** Architecture designed for YouTube (Videos & Shorts), Instagram (Reels & Stories), TikTok, Facebook, and Twitter/X.
- **Python yt-dlp Engine:** Direct extraction with real-time title, thumbnail, duration, view count, and direct downloadable stream links.
- **Safe Proxy Streaming:** Direct download initiation with clean filename headers (Content-Disposition: attachment).
- **Modern Responsive UI:** Glassmorphism, dark aesthetic, instant URL validation, and responsive mobile-first design.

## Architecture
- ackend/: Python API server using yt-dlp + uvicorn + starlette
  - POST /api/extract: Extracts formats, media info, and streams from any supported URL
  - GET /api/stream: Proxy media stream handler
  - GET /api/health: Health check endpoint
- src/: React 19 + Tailwind + Vite Frontend
  - HeroDownloader: Main search input with instant extraction
  - MediaResult: Shows media card, thumbnail, details, and video/audio download buttons
  - SupportedPlatforms: Grid of supported platforms and media formats

## Local Development

### 1. Backend (Python)
`ash
cd backend
pip install -r requirements.txt
python main.py
`
Backend runs on http://localhost:8000.

### 2. Frontend (React + Vite)
`ash
npm install
npm run dev
`
Frontend runs on http://localhost:5173 and proxies /api calls to http://localhost:8000.

### 3. Production Build
`ash
npm run build
`
Generates production assets in dist/.
