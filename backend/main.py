import os
import re
import sys
import json
import asyncio
import urllib.parse
import shutil
from typing import Optional

import yt_dlp
import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse, Response
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# Security & Origin Configuration
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        "ALLOWED_ORIGINS",
        "https://ovd.winplaybox.in,https://winplaybox.in,http://localhost:5173,http://localhost:3000"
    ).split(",") if o.strip()
]
EXTENSION_SECRET_KEY = os.environ.get("EXTENSION_SECRET_KEY", "wpb_ext_9f83e2a74c1048b9ad51f63cb7e90812")
ALLOWED_EXTENSION_IDS = [
    ext_id.strip() for ext_id in os.environ.get("ALLOWED_EXTENSION_IDS", "").split(",") if ext_id.strip()
]

# Strict Whitelist for /api/stream proxy to prevent SSRF and open proxy abuse
ALLOWED_CDN_DOMAINS = [
    r".*\.googlevideo\.com$",
    r".*\.youtube\.com$",
    r".*\.cdninstagram\.com$",
    r".*\.fbcdn\.net$",
    r".*\.tiktokcdn\.com$",
    r".*\.tiktokcdn-us\.com$",
    r".*\.twimg\.com$",
    r".*\.pinimg\.com$",
    r".*\.vimeocdn\.com$",
    r".*\.sndcdn\.com$",
    r".*\.redd\.it$",
    r".*\.reddit\.com$",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

def find_node_path() -> Optional[str]:
    candidates = [
        shutil.which("node"),
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

NODE_EXE = find_node_path()

def is_safe_cdn_url(target_url: str) -> bool:
    """Validates target URL against permitted media CDN domains to prevent SSRF."""
    try:
        parsed = urllib.parse.urlparse(target_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False
        hostname = parsed.netloc.split(":")[0].lower()
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"):
            return False
        for pattern in ALLOWED_CDN_DOMAINS:
            if re.match(pattern, hostname):
                return True
        return False
    except Exception:
        return False

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "Live / Unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_size(bytes_num: Optional[int]) -> str:
    if not bytes_num or bytes_num <= 0:
        return "Unknown Size"
    mb = bytes_num / (1024 * 1024)
    if mb > 1024:
        return f"{mb / 1024:.2f} GB"
    return f"{mb:.1f} MB"

def detect_platform(url: str) -> str:
    lower = url.lower()
    if "youtube.com" in lower or "youtu.be" in lower:
        return "youtube"
    if "instagram.com" in lower:
        return "instagram"
    if "tiktok.com" in lower:
        return "tiktok"
    if "facebook.com" in lower or "fb.watch" in lower:
        return "facebook"
    if "twitter.com" in lower or "x.com" in lower:
        return "twitter"
    if "reddit.com" in lower:
        return "reddit"
    if "pinterest.com" in lower or "pin.it" in lower:
        return "pinterest"
    if "soundcloud.com" in lower:
        return "soundcloud"
    return "generic"

def extract_media(url: str):
    platform = detect_platform(url)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
        "socket_timeout": 15,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }
    }
    if NODE_EXE:
        ydl_opts["js_runtimes"] = {"node": {"path": NODE_EXE}}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not extract media info from URL")

    title = info.get("title") or "downloaded_media"
    title_clean = re.sub(r'[\\/*?:\"<>|]', "", title).strip()
    thumbnail = info.get("thumbnail") or ""
    duration = format_duration(info.get("duration"))
    uploader = info.get("uploader") or info.get("channel") or "Unknown Creator"
    views = info.get("view_count")

    all_formats = info.get("formats", [])
    video_formats = []
    audio_formats = []
    seen_heights = set()

    sorted_formats = sorted(
        all_formats,
        key=lambda f: (
            f.get("height") or 0,
            f.get("tbr") or 0,
            f.get("filesize") or 0
        ),
        reverse=True
    )

    for f in sorted_formats:
        height = f.get("height")
        vcodec = f.get("vcodec")
        ext = f.get("ext") or "mp4"
        format_url = f.get("url")

        if not height or not format_url or height < 144:
            continue
        if vcodec == "none":
            continue

        if height in seen_heights:
            continue
        seen_heights.add(height)

        fps = f.get("fps")
        fps_label = f" {fps}fps" if fps and fps > 30 else ""
        quality_label = f"{height}p{fps_label}"
        if height >= 1080:
            quality_label += " (Full HD)"
        elif height >= 720:
            quality_label += " (HD)"

        size_bytes = f.get("filesize") or f.get("filesize_approx")
        size_str = format_size(size_bytes)
        has_audio = f.get("acodec") != "none"

        safe_filename = f"{title_clean}_{height}p.{ext}"
        stream_proxy_url = f"/api/stream?url={urllib.parse.quote(format_url)}&filename={urllib.parse.quote(safe_filename)}"

        video_formats.append({
            "id": f.get("format_id"),
            "quality": quality_label,
            "height": height,
            "ext": ext,
            "size": size_str,
            "has_audio": has_audio,
            "url": format_url,
            "stream_url": stream_proxy_url,
            "download_name": safe_filename
        })

    best_audio_streams = [
        f for f in all_formats
        if f.get("acodec") != "none" and (f.get("vcodec") == "none" or f.get("audio_channels"))
    ]
    best_audio_streams = sorted(
        best_audio_streams,
        key=lambda f: (f.get("abr") or 0, f.get("filesize") or 0),
        reverse=True
    )

    if best_audio_streams:
        primary_audio = best_audio_streams[0]
        audio_url = primary_audio.get("url")
        audio_size = format_size(primary_audio.get("filesize") or primary_audio.get("filesize_approx"))

        name_320 = f"{title_clean}_320kbps.mp3"
        name_192 = f"{title_clean}_192kbps.mp3"
        name_orig = f"{title_clean}.{primary_audio.get('ext') or 'm4a'}"

        audio_formats.append({
            "id": "mp3-320",
            "quality": "320 kbps High Fidelity",
            "format": "MP3",
            "size": audio_size,
            "url": audio_url,
            "stream_url": f"/api/stream?url={urllib.parse.quote(audio_url)}&filename={urllib.parse.quote(name_320)}",
            "download_name": name_320
        })
        audio_formats.append({
            "id": "mp3-192",
            "quality": "192 kbps Standard Audio",
            "format": "MP3",
            "size": audio_size,
            "url": audio_url,
            "stream_url": f"/api/stream?url={urllib.parse.quote(audio_url)}&filename={urllib.parse.quote(name_192)}",
            "download_name": name_192
        })
        audio_formats.append({
            "id": "m4a-hq",
            "quality": "Original Stream (M4A)",
            "format": primary_audio.get("ext") or "m4a",
            "size": audio_size,
            "url": audio_url,
            "stream_url": f"/api/stream?url={urllib.parse.quote(audio_url)}&filename={urllib.parse.quote(name_orig)}",
            "download_name": name_orig
        })

    if not video_formats and info.get("url"):
        direct_name = f"{title_clean}_HD.mp4"
        direct_url = info.get("url")
        video_formats.append({
            "id": "best",
            "quality": "Original HD Video",
            "height": 1080,
            "ext": "mp4",
            "size": format_size(info.get("filesize")),
            "has_audio": True,
            "url": direct_url,
            "stream_url": f"/api/stream?url={urllib.parse.quote(direct_url)}&filename={urllib.parse.quote(direct_name)}",
            "download_name": direct_name
        })

    return {
        "title": title_clean,
        "thumbnail": thumbnail,
        "duration": duration,
        "uploader": uploader,
        "platform": platform,
        "views": f"{views:,}" if views else None,
        "video_formats": video_formats[:6],
        "audio_formats": audio_formats,
        "original_url": url
    }

async def extract_handler(request):
    try:
        data = await request.json()
        url = data.get("url", "").strip()

        if not url:
            return JSONResponse({"success": False, "error": "Please provide a valid media URL"}, status_code=400)

        loop = asyncio.get_event_loop()
        media_info = await loop.run_in_executor(None, extract_media, url)

        return JSONResponse({"success": True, "data": media_info})
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg:
            error_msg = "YouTube requested verification for this video. Try another link or video format."
        elif "Private video" in error_msg:
            error_msg = "This video is private or restricted by the author."
        return JSONResponse({"success": False, "error": error_msg}, status_code=500)

async def stream_download_handler(request):
    target_url = request.query_params.get("url")
    filename = request.query_params.get("filename") or "download.mp4"
    safe_filename = urllib.parse.quote(filename)

    if not target_url:
        return Response("Missing target stream url", status_code=400)

    if not is_safe_cdn_url(target_url):
        return Response("Target host not permitted for streaming proxy", status_code=400)

    client_headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.youtube.com/"
    }

    client = httpx.AsyncClient(headers=client_headers, follow_redirects=True, timeout=90.0)

    async def stream_chunks():
        try:
            async with client.stream("GET", target_url) as resp:
                async for chunk in resp.aiter_bytes(chunk_size=1024 * 64):
                    yield chunk
        finally:
            await client.aclose()

    headers = {
        "Content-Disposition": f'attachment; filename="{safe_filename}"; filename*=UTF-8''{safe_filename}',
        "Content-Type": "application/octet-stream"
    }

    return StreamingResponse(stream_chunks(), headers=headers)

async def health_handler(request):
    return JSONResponse({
        "status": "online",
        "service": "AnyDownloader Python Engine",
        "yt_dlp_version": yt_dlp.version.__version__,
        "node_exe": NODE_EXE
    })

class ClientAccessAuthMiddleware(BaseHTTPMiddleware):
    """
    Ensures ONLY your authorized website (via Origin/Referer) 
    or your browser extension (via X-Extension-Key or chrome-extension origin) 
    can invoke the API endpoints.
    """
    async def dispatch(self, request, call_next):
        # 1. Allow preflight OPTIONS requests for CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. Allow public health check endpoints
        if request.url.path in ("/", "/health", "/api/health"):
            return await call_next(request)

        # 3. Verify origin, referer, or extension secret key
        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        ext_key = request.headers.get("x-extension-key", "")

        # A. Browser Extension Key check
        if ext_key and ext_key == EXTENSION_SECRET_KEY:
            return await call_next(request)

        # B. Browser Extension Origin check
        if ALLOWED_EXTENSION_IDS:
            if any(origin == f"chrome-extension://{ext_id}" or origin == f"moz-extension://{ext_id}" for ext_id in ALLOWED_EXTENSION_IDS):
                return await call_next(request)
        elif origin.startswith("chrome-extension://") or origin.startswith("moz-extension://"):
            return await call_next(request)

        # C. Website Origin or Referer check
        origin_match = any(origin.startswith(ao) for ao in ALLOWED_ORIGINS)
        referer_match = any(referer.startswith(ao) for ao in ALLOWED_ORIGINS)

        if origin_match or referer_match:
            return await call_next(request)

        return JSONResponse(
            {"success": False, "error": "Access denied: Unauthorized origin or missing extension authentication."},
            status_code=403
        )

routes = [
    Route("/", health_handler, methods=["GET"]),
    Route("/health", health_handler, methods=["GET"]),
    Route("/api/extract", extract_handler, methods=["POST"]),
    Route("/api/stream", stream_download_handler, methods=["GET"]),
    Route("/api/health", health_handler, methods=["GET"])
]

middleware = [
    Middleware(ClientAccessAuthMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"]
    )
]

app = Starlette(debug=False, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"AnyDownloader Python Engine starting on http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, app_dir="backend")
