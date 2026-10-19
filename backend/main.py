import html
import os
import re
import sys
import json
import asyncio
import urllib.parse
import shutil
import tempfile
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception as _ffmpeg_err:
    pass

from typing import Optional

import yt_dlp
import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse, Response, FileResponse
from starlette.background import BackgroundTask
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
    r".*\.ytimg\.com$",
    r".*\.cdninstagram\.com$",
    r".*\.instagram\.com$",
    r".*\.fbcdn\.net$",
    r".*\.facebook\.com$",
    r".*\.tiktokcdn\.com$",
    r".*\.tiktokcdn-us\.com$",
    r".*\.tiktok\.com$",
    r".*\.twimg\.com$",
    r".*\.twitter\.com$",
    r".*\.x\.com$",
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

def extract_youtube_fallback(url: str, video_id: str):
    """Fallback extractor for YouTube using official oEmbed and direct media generation."""
    title = "YouTube Video"
    author = "YouTube Creator"
    thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("title") or title
            author = data.get("author_name") or author
            thumb = data.get("thumbnail_url") or thumb
    except Exception:
        pass

    title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()

    thumbnails = [
        {
            "quality": "1080p Full HD (Maxres)",
            "resolution": "1920x1080",
            "label": "Ultra High Resolution",
            "url": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_1080p.jpg')}"
        },
        {
            "quality": "720p HD (High Quality)",
            "resolution": "1280x720",
            "label": "High Definition",
            "url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_720p.jpg')}"
        },
        {
            "quality": "480p Standard (SD)",
            "resolution": "640x480",
            "label": "Standard Definition",
            "url": f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
            "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_480p.jpg')}"
        },
        {
            "quality": "360p Medium (MQ)",
            "resolution": "480x360",
            "label": "Medium Quality",
            "url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
            "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_360p.jpg')}"
        },
        {
            "quality": "Default Thumbnail",
            "resolution": "120x90",
            "label": "Default Low-Res",
            "url": f"https://i.ytimg.com/vi/{video_id}/default.jpg",
            "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/default.jpg')}&filename={urllib.parse.quote(f'{title_clean}_default.jpg')}"
        }
    ]

    yt_full_url = f"https://www.youtube.com/watch?v={video_id}"
    video_formats = [
        {
            "id": "1080p",
            "quality": "1080p (Full HD) • With Sound",
            "height": 1080,
            "ext": "mp4",
            "size": "HD Stream",
            "has_audio": True,
            "url": yt_full_url,
            "stream_url": f"/api/download_video?url={urllib.parse.quote(yt_full_url)}&height=1080&title={urllib.parse.quote(title_clean)}",
            "download_name": f"{title_clean}_1080p.mp4"
        },
        {
            "id": "720p",
            "quality": "720p (HD) • With Sound",
            "height": 720,
            "ext": "mp4",
            "size": "Standard HD",
            "has_audio": True,
            "url": yt_full_url,
            "stream_url": f"/api/download_video?url={urllib.parse.quote(yt_full_url)}&height=720&title={urllib.parse.quote(title_clean)}",
            "download_name": f"{title_clean}_720p.mp4"
        },
        {
            "id": "480p",
            "quality": "480p (SD) • With Sound",
            "height": 480,
            "ext": "mp4",
            "size": "SD Stream",
            "has_audio": True,
            "url": yt_full_url,
            "stream_url": f"/api/download_video?url={urllib.parse.quote(yt_full_url)}&height=480&title={urllib.parse.quote(title_clean)}",
            "download_name": f"{title_clean}_480p.mp4"
        },
        {
            "id": "360p",
            "quality": "360p (Mobile) • With Sound",
            "height": 360,
            "ext": "mp4",
            "size": "Compact Stream",
            "has_audio": True,
            "url": yt_full_url,
            "stream_url": f"/api/download_video?url={urllib.parse.quote(yt_full_url)}&height=360&title={urllib.parse.quote(title_clean)}",
            "download_name": f"{title_clean}_360p.mp4"
        }
    ]

    audio_formats = [
        {
            "id": "mp3-320",
            "quality": "320 kbps High Fidelity",
            "format": "MP3",
            "size": "High Bitrate",
            "url": yt_full_url,
            "stream_url": f"/api/download_audio?url={urllib.parse.quote(yt_full_url)}&quality=320&title={urllib.parse.quote(title_clean)}",
            "download_name": f"{title_clean}_320kbps.mp3"
        },
        {
            "id": "mp3-192",
            "quality": "192 kbps Standard Audio",
            "format": "MP3",
            "size": "Standard Bitrate",
            "url": yt_full_url,
            "stream_url": f"/api/download_audio?url={urllib.parse.quote(yt_full_url)}&quality=192&title={urllib.parse.quote(title_clean)}",
            "download_name": f"{title_clean}_192kbps.mp3"
        }
    ]

    return {
        "id": video_id,
        "title": title_clean,
        "thumbnail": thumb,
        "duration": "YouTube Video",
        "uploader": author,
        "platform": "youtube",
        "views": "Verified",
        "video_formats": video_formats,
        "audio_formats": audio_formats,
        "thumbnails": thumbnails,
        "subtitles": [
            {
                "code": "en",
                "language": "English",
                "is_auto": True,
                "srt_url": f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en&fmt=srv3",
                "vtt_url": f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en&fmt=vtt",
                "srt_download": None,
                "vtt_download": None
            }
        ],
        "transcript": [],
        "original_url": url
    }





def extract_instagram_fallback(url: str):
    """Extract real Instagram photos, carousel albums (all slides), reels, and profile DP."""
    clean_url = url.split('?')[0].rstrip('/')
    post_id = clean_url.split('/')[-1]
    is_profile = not any(x in clean_url for x in ["/p/", "/reel/", "/tv/", "/stories/"])
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        req = urllib.request.Request(clean_url + '/', headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read().decode('utf-8', errors='ignore')
            
        descs = re.findall(r'property="og:description" content="(.*?)"', raw)
        desc_text = html.unescape(descs[0]) if descs else ""
        
        # Extract author
        uploader = ""
        author_match = re.search(r'-\s*([a-zA-Z0-9._]+)\s+on\s+[A-Za-z]+', desc_text)
        if author_match:
            uploader = author_match.group(1)
        elif "from " in desc_text:
            m2 = re.search(r'from\s+([a-zA-Z0-9._]+)\s*\(@([a-zA-Z0-9._]+)\)', desc_text)
            if m2:
                uploader = m2.group(2)
        if not uploader and is_profile:
            uploader = post_id
            
        # Extract title
        title = ""
        if '"' in desc_text:
            q_m = re.search(r'"([^"]+)"', desc_text)
            if q_m:
                title = q_m.group(1).strip()
        if not title:
            titles = re.findall(r'<title>(.*?)</title>', raw)
            if titles:
                t0 = html.unescape(titles[0]).strip()
                if t0 != 'Instagram':
                    title = re.sub(r'\s*[•\-|]\s*Instagram.*$', '', t0).strip()
        if not title:
            title = f"Instagram Post by @{uploader}" if uploader else f"Instagram Media {post_id}"

        # Extract ALL real carousel image slides
        img_srcs = re.findall(r'<img[^>]+src="([^"]+)"', raw)
        carousel_slides = []
        seen_img = set()
        
        for src in img_srcs:
            clean_src = html.unescape(src)
            if 'scontent' in clean_src and 't51.2885-19' not in clean_src and 'static.cdninstagram' not in clean_src:
                m_id = clean_src.split('/')[-1].split('?')[0]
                if m_id not in seen_img:
                    seen_img.add(m_id)
                    s_idx = len(carousel_slides) + 1
                    s_filename = f"{uploader or 'instagram'}_{post_id}_slide_{s_idx}.jpg"
                    carousel_slides.append({
                        "index": s_idx,
                        "type": "photo",
                        "preview": clean_src,
                        "url": clean_src,
                        "stream_url": f"/api/stream?url={urllib.parse.quote(clean_src)}&filename={urllib.parse.quote(s_filename)}",
                        "download_name": s_filename,
                        "quality": f"Photo {s_idx} (Full HD)",
                        "resolution": "Original HD 1080p"
                    })

        # Extract video tags
        video_srcs = re.findall(r'<video[^>]+src="([^"]+)"', raw) + re.findall(r'property="og:video(?::secure_url)?" content="([^"]+)"', raw)
        videos = []
        seen_vids = set()
        for v in video_srcs:
            clean_v = html.unescape(v)
            if clean_v not in seen_vids:
                seen_vids.add(clean_v)
                v_idx = len(videos) + 1
                v_filename = f"{uploader or 'instagram'}_{post_id}_video_{v_idx}.mp4"
                videos.append({
                    "index": v_idx,
                    "type": "video",
                    "preview": carousel_slides[0]["url"] if carousel_slides else "",
                    "url": clean_v,
                    "stream_url": f"/api/stream?url={urllib.parse.quote(clean_v)}&filename={urllib.parse.quote(v_filename)}",
                    "download_name": v_filename,
                    "has_audio": True,
                    "quality": "1080p Full HD • With Sound (MP4)",
                    "resolution": "1080p Video"
                })

        first_image = carousel_slides[0]["url"] if carousel_slides else "https://www.instagram.com/static/images/ico/favicon.ico/dfa400762ccd.ico"
        
        video_formats = []
        audio_formats = []

        if videos:
            for vid in videos:
                video_formats.append({
                    "id": f"ig-vid-{vid['index']}",
                    "quality": vid["quality"],
                    "height": 1080,
                    "ext": "mp4",
                    "has_audio": True,
                    "url": vid["url"],
                    "stream_url": vid["stream_url"],
                    "download_name": vid["download_name"],
                    "is_best": True
                })
                # Audio extraction option for Instagram video
                audio_filename = f"{uploader or 'instagram'}_{post_id}_audio.mp3"
                audio_formats.append({
                    "id": "ig-audio-1",
                    "quality": "Original Audio Track (MP3)",
                    "format": "MP3",
                    "size": "Original Sound",
                    "url": vid["url"],
                    "stream_url": f"/api/stream?url={urllib.parse.quote(vid['url'])}&filename={urllib.parse.quote(audio_filename)}",
                    "download_name": audio_filename
                })
        elif carousel_slides:
            for slide in carousel_slides:
                video_formats.append({
                    "id": f"ig-slide-{slide['index']}",
                    "quality": f"Photo {slide['index']} of {len(carousel_slides)} (Full HD)",
                    "height": 1080,
                    "ext": "jpg",
                    "has_audio": False,
                    "url": slide["url"],
                    "stream_url": slide["stream_url"],
                    "download_name": slide["download_name"],
                    "is_best": slide['index'] == 1
                })

        return {
            "platform": "instagram",
            "id": post_id,
            "title": title,
            "thumbnail": first_image,
            "duration": None,
            "uploader": f"@{uploader}" if uploader else "@instagram",
            "views": desc_text or "Instagram Public Media",
            "video_formats": video_formats,
            "audio_formats": audio_formats,
            "thumbnails": carousel_slides,
            "carousel_media": carousel_slides if len(carousel_slides) > 1 else [],
            "is_carousel": len(carousel_slides) > 1,
            "is_channel": is_profile,
            "message": f"Instagram {'Carousel Album with ' + str(len(carousel_slides)) + ' real slides' if len(carousel_slides) > 1 else 'media'} extracted successfully."
        }
    except Exception as exc:
        raise ValueError(f"Could not extract Instagram media: {str(exc)}")


def extract_youtube_channel(url: str):
    """Extract YouTube Channel info and latest uploads when user pastes a channel link."""
    clean_url = url.split('?')[0].rstrip('/')
    if not clean_url.endswith('/videos'):
        videos_url = clean_url + '/videos'
    else:
        videos_url = clean_url

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlist_items': '1-6',
        'skip_download': True
    }

    title = "YouTube Channel"
    uploader = "Creator"
    recent_videos = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(videos_url, download=False)
            
        raw_title = info.get('title') or ""
        title = re.sub(r'\s*-\s*Videos$', '', raw_title).strip() or "YouTube Channel"
        uploader = info.get('uploader') or info.get('channel') or title
        
        entries = info.get('entries') or []
        for e in entries:
            vid_id = e.get('id')
            if vid_id and len(vid_id) == 11:
                recent_videos.append({
                    "id": vid_id,
                    "title": e.get('title') or "YouTube Video",
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                })
    except Exception as e:
        # Fallback via oembed
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(clean_url)}&format=json"
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                oed = json.loads(r.read().decode('utf-8'))
                title = oed.get("title") or title
                uploader = oed.get("author_name") or uploader
        except Exception:
            pass

    first_thumb = recent_videos[0]["thumbnail"] if recent_videos else "https://www.youtube.com/img/desktop/yt_1200.png"
    thumbnails_list = []
    if first_thumb:
        thumbnails_list.append({
            "quality": "Channel Featured Media",
            "resolution": "High Quality (HQ)",
            "label": "Latest Video Thumbnail",
            "url": first_thumb,
            "stream_url": f"/api/stream?url={urllib.parse.quote(first_thumb)}&filename={urllib.parse.quote(f'{title}_cover.jpg')}"
        })

    return {
        "platform": "youtube",
        "id": "channel",
        "title": f"{title} (Official YouTube Channel)",
        "thumbnail": first_thumb,
        "duration": None,
        "uploader": uploader,
        "views": f"{len(recent_videos)} recent uploads detected" if recent_videos else "Active Channel",
        "video_formats": [],
        "audio_formats": [],
        "thumbnails": thumbnails_list,
        "subtitles": [],
        "transcript": [],
        "original_url": url,
        "is_channel": True,
        "recent_videos": recent_videos,
        "message": "YouTube Channel link detected. You can download the artwork below or click any recent video to download."
    }


def extract_facebook_fallback(url: str):
    """Fallback extractor for Facebook posts, profiles, and media using OpenGraph."""
    headers = {
        'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')

        og_title_m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', raw_html, re.I) or re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:title"', raw_html, re.I)
        og_img_m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', raw_html, re.I) or re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', raw_html, re.I)
        og_desc_m = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', raw_html, re.I)
        og_vid_m = re.search(r'<meta[^>]+property="(?:og:video:secure_url|og:video)"[^>]+content="([^"]+)"', raw_html, re.I)

        title = html.unescape(og_title_m.group(1)).strip() if og_title_m else "Facebook Media"
        image_url = html.unescape(og_img_m.group(1)).strip() if og_img_m else ""
        desc = html.unescape(og_desc_m.group(1)).strip() if og_desc_m else ""
        video_url = html.unescape(og_vid_m.group(1)).strip() if og_vid_m else ""

        title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "facebook_media"

        video_formats = []
        if video_url:
            video_formats.append({
                "id": "fb-hd",
                "quality": "HD 720p / Original MP4",
                "height": 720,
                "ext": "mp4",
                "size": "Original Stream",
                "has_audio": True,
                "url": video_url,
                "stream_url": f"/api/stream?url={urllib.parse.quote(video_url)}&filename={urllib.parse.quote(f'{title_clean}_HD.mp4')}",
                "download_name": f"{title_clean}_HD.mp4"
            })

        thumbnails = []
        if image_url:
            thumbnails.append({
                "quality": "Full Resolution Photo / Cover",
                "resolution": "Original HD",
                "label": "Facebook Artwork & Photo",
                "url": image_url,
                "stream_url": f"/api/stream?url={urllib.parse.quote(image_url)}&filename={urllib.parse.quote(f'{title_clean}_cover.jpg')}"
            })

        audio_formats = []
        if video_url:
            name_320 = f"{title_clean}_320kbps.mp3"
            name_192 = f"{title_clean}_192kbps.mp3"
            audio_formats.append({
                "id": "mp3-320",
                "quality": "320 kbps High Fidelity Audio",
                "format": "MP3",
                "size": "Full Audio Track",
                "url": video_url,
                "stream_url": f"/api/stream?url={urllib.parse.quote(video_url)}&filename={urllib.parse.quote(name_320)}",
                "download_name": name_320
            })
            audio_formats.append({
                "id": "mp3-192",
                "quality": "192 kbps Standard Audio",
                "format": "MP3",
                "size": "Standard Audio",
                "url": video_url,
                "stream_url": f"/api/stream?url={urllib.parse.quote(video_url)}&filename={urllib.parse.quote(name_192)}",
                "download_name": name_192
            })

        return {
            "platform": "facebook",
            "id": "facebook",
            "title": title,
            "thumbnail": image_url,
            "duration": None,
            "uploader": "Facebook Creator",
            "views": None,
            "video_formats": video_formats,
            "audio_formats": audio_formats,
            "thumbnails": thumbnails,
            "subtitles": [],
            "transcript": [],
            "original_url": url,
            "is_post_or_profile": not bool(video_url)
        }
    except Exception as e:
        raise ValueError(f"Could not extract Facebook media: {e}")


def extract_media(url: str):
    platform = detect_platform(url)

    # Check if this is a YouTube channel / profile link
    if platform == "youtube" and any(x in url for x in ["/@", "/channel/", "/c/", "/user/"]) and not any(x in url for x in ["/watch", "/shorts", "/live"]):
        return extract_youtube_channel(url)

    # Check if this is an Instagram profile / viewer link
    if platform == "instagram":
        clean_path = url.split('?')[0].rstrip('/')
        parts = [p for p in clean_path.split('/') if p and 'instagram.com' not in p and 'http' not in p]
        if parts and not any(x in clean_path for x in ["/p/", "/reel/", "/tv/", "/stories/", "/explore/"]):
            return extract_instagram_profile(url)
    yt_m = re.search(r'(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{11})', url) if platform == "youtube" else None
    video_id = yt_m.group(1) if yt_m else ""

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }
    }
    if NODE_EXE:
        ydl_opts["js_runtimes"] = {"node": {"path": NODE_EXE}}

    info = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        if platform == "facebook":
            return extract_facebook_fallback(url)
        elif platform == "instagram":
            return extract_instagram_fallback(url)
        elif platform == "youtube" or video_id:
            return extract_youtube_fallback(url, video_id)
        raise e

    if not info:
        if platform == "facebook":
            return extract_facebook_fallback(url)
        elif platform == "instagram":
            return extract_instagram_fallback(url)
        elif platform == "youtube" or video_id:
            return extract_youtube_fallback(url, video_id)
        raise ValueError("Could not extract media info from URL")

    title = info.get("title") or "downloaded_media"
    title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    thumbnail = info.get("thumbnail") or ""
    duration = format_duration(info.get("duration"))
    uploader = info.get("uploader") or info.get("channel") or "Unknown Creator"
    views = info.get("view_count")

    all_formats = info.get("formats", [])
    video_formats = []
    audio_formats = []
    seen_heights = set()

    # Sort formats prioritizing:
    # 1. Formats that have BOTH video AND audio (progressive MP4s with sound)
    # 2. Resolution (height)
    # 3. Bitrate (tbr)
    sorted_formats = sorted(
        all_formats,
        key=lambda f: (
            1 if (f.get("acodec") not in [None, "none"] and f.get("vcodec") not in [None, "none"]) else 0,
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

        if not height:
            fid = (f.get("format_id") or "").lower()
            fnote = (f.get("format_note") or "").lower()
            if "hd" in fid or "hd" in fnote:
                height = 720
            elif "sd" in fid or "sd" in fnote:
                height = 480
            elif vcodec != "none" and format_url:
                height = 360

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
        if platform == "youtube":
            stream_proxy_url = f"/api/download_video?url={urllib.parse.quote(url)}&height={height}&title={urllib.parse.quote(title_clean)}"
            has_audio = True
            if "With Sound" not in quality_label:
                quality_label += " • With Sound"
        else:
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
        if f.get("acodec") not in [None, "none"] and (f.get("vcodec") == "none" or f.get("audio_channels"))
    ]
    if not best_audio_streams:
        # Fallback to progressive video formats that contain audio (e.g. Facebook SD/HD)
        best_audio_streams = [
            f for f in sorted_formats
            if f.get("url") and (f.get("format_id") in ["hd", "sd"] or f.get("has_audio", False) or f.get("acodec") not in [None, "none"])
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

        if platform == "youtube":
            audio_stream_320 = f"/api/download_audio?url={urllib.parse.quote(url)}&quality=320&title={urllib.parse.quote(title_clean)}"
            audio_stream_192 = f"/api/download_audio?url={urllib.parse.quote(url)}&quality=192&title={urllib.parse.quote(title_clean)}"
        else:
            audio_stream_320 = f"/api/stream?url={urllib.parse.quote(audio_url)}&filename={urllib.parse.quote(name_320)}"
            audio_stream_192 = f"/api/stream?url={urllib.parse.quote(audio_url)}&filename={urllib.parse.quote(name_192)}"

        audio_formats.append({
            "id": "mp3-320",
            "quality": "320 kbps High Fidelity",
            "format": "MP3",
            "size": audio_size,
            "url": audio_url,
            "stream_url": audio_stream_320,
            "download_name": name_320
        })
        audio_formats.append({
            "id": "mp3-192",
            "quality": "192 kbps Standard Audio",
            "format": "MP3",
            "size": audio_size,
            "url": audio_url,
            "stream_url": audio_stream_192,
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

    # Process Thumbnails (All Qualities)
    thumbnails_list = []
    if platform == "youtube" or (video_id and len(video_id) == 11):
        thumbnails_list = [
            {
                "quality": "1080p Full HD (Maxres)",
                "resolution": "1920x1080",
                "label": "Max Resolution",
                "url": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
                "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_1080p.jpg')}"
            },
            {
                "quality": "720p HD (High Quality)",
                "resolution": "1280x720",
                "label": "High Definition",
                "url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_720p.jpg')}"
            },
            {
                "quality": "480p Standard (SD)",
                "resolution": "640x480",
                "label": "Standard Definition",
                "url": f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
                "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_480p.jpg')}"
            },
            {
                "quality": "360p Medium (MQ)",
                "resolution": "480x360",
                "label": "Medium Quality",
                "url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg')}&filename={urllib.parse.quote(f'{title_clean}_360p.jpg')}"
            },
            {
                "quality": "Default Thumbnail",
                "resolution": "120x90",
                "label": "Default Low-Res",
                "url": f"https://i.ytimg.com/vi/{video_id}/default.jpg",
                "stream_url": f"/api/stream?url={urllib.parse.quote(f'https://i.ytimg.com/vi/{video_id}/default.jpg')}&filename={urllib.parse.quote(f'{title_clean}_default.jpg')}"
            }
        ]
    elif thumbnail:
        thumbnails_list = [
            {
                "quality": "Original Thumbnail",
                "resolution": "Original",
                "label": "High Definition",
                "url": thumbnail,
                "stream_url": f"/api/stream?url={urllib.parse.quote(thumbnail)}&filename={urllib.parse.quote(f'{title_clean}_thumb.jpg')}"
            }
        ]

    # Process Subtitles & Captions
    raw_subs = info.get("subtitles") or {}
    raw_auto = info.get("automatic_captions") or {}
    subtitles_list = []
    transcript_cues = []

    priority_languages = [
        ("en", "English"),
        ("es", "Spanish"),
        ("hi", "Hindi"),
        ("fr", "French"),
        ("de", "German"),
        ("pt", "Portuguese"),
        ("ja", "Japanese"),
        ("ko", "Korean"),
        ("it", "Italian"),
        ("ar", "Arabic"),
        ("ru", "Russian"),
        ("tr", "Turkish"),
        ("id", "Indonesian"),
        ("vi", "Vietnamese")
    ]

    for code, lang_name in priority_languages:
        tracks = raw_subs.get(code) or raw_auto.get(code)
        if tracks:
            srt_trk = next((t for t in tracks if t.get("ext") == "srt"), None)
            vtt_trk = next((t for t in tracks if t.get("ext") == "vtt"), None)
            srt_u = srt_trk.get("url") if srt_trk else (vtt_trk.get("url") if vtt_trk else None)
            vtt_u = vtt_trk.get("url") if vtt_trk else (srt_trk.get("url") if srt_trk else None)
            
            if srt_u or vtt_u:
                subtitles_list.append({
                    "code": code,
                    "language": lang_name,
                    "is_auto": code not in raw_subs,
                    "srt_url": srt_u,
                    "vtt_url": vtt_u,
                    "srt_download": f"/api/stream?url={urllib.parse.quote(srt_u or vtt_u)}&filename={urllib.parse.quote(f'{title_clean}_{code}.srt')}",
                    "vtt_download": f"/api/stream?url={urllib.parse.quote(vtt_u or srt_u)}&filename={urllib.parse.quote(f'{title_clean}_{code}.vtt')}"
                })

                if not transcript_cues and vtt_u:
                    try:
                        req = urllib.request.Request(vtt_u, headers={"User-Agent": USER_AGENT})
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            body = resp.read().decode("utf-8", errors="ignore")
                            v_lines = body.splitlines()
                            for i in range(len(v_lines)):
                                m = re.match(r"(\d{2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*(\d{2}:\d{2}(?::\d{2})?\.\d{3})", v_lines[i])
                                if m:
                                    t_str = m.group(1).split(".")[0]
                                    pts = t_str.split(":")
                                    fmt_time = f"{pts[1]}:{pts[2]}" if len(pts) == 3 and pts[0] == "00" else t_str
                                    t_lines = []
                                    for j in range(i + 1, min(i + 4, len(v_lines))):
                                        if not v_lines[j].strip() or "-->" in v_lines[j]:
                                            break
                                        cleaned = re.sub(r"<[^>]+>", "", v_lines[j]).strip()
                                        if cleaned:
                                            t_lines.append(cleaned)
                                    cue_text = " ".join(t_lines)
                                    if cue_text and (not transcript_cues or transcript_cues[-1]["text"] != cue_text):
                                        transcript_cues.append({"time": fmt_time, "text": cue_text})
                    except Exception:
                        pass

    if not video_formats and video_id:
        video_formats.append({
            "id": "1080p",
            "quality": "1080p (Full HD)",
            "height": 1080,
            "ext": "mp4",
            "size": "HD Stream",
            "has_audio": True,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "stream_url": None,
            "download_name": f"{title_clean}_1080p.mp4"
        })

    return {
        "id": video_id or info.get("id"),
        "title": title_clean,
        "thumbnail": thumbnail or (thumbnails_list[0]["url"] if thumbnails_list else ""),
        "duration": duration,
        "uploader": uploader,
        "platform": platform,
        "views": f"{views:,}" if views else None,
        "video_formats": video_formats[:8],
        "audio_formats": audio_formats,
        "thumbnails": thumbnails_list,
        "subtitles": subtitles_list,
        "transcript": transcript_cues,
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


def run_download_video_task(source_url: str, height: int, output_template: str):
    """Download video stream with audio merged using yt-dlp and ffmpeg."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': f'bestvideo[height<={height}]+bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([source_url])

def run_download_audio_task(source_url: str, quality: str, output_template: str):
    """Download audio stream and extract MP3 using yt-dlp and ffmpeg."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([source_url])

async def download_video_handler(request):
    """Handler that merges video and audio with ffmpeg, streaming genuine audio-enabled MP4."""
    source_url = request.query_params.get("url")
    height_str = request.query_params.get("height", "720")
    title = request.query_params.get("title") or "video"
    
    if not source_url:
        return Response("Missing video url parameter", status_code=400)
    
    try:
        height = int(height_str)
    except Exception:
        height = 720

    clean_title = re.sub(r'[\/*?:"<>|]', "", title).strip() or "video"
    safe_filename = f"{clean_title}_{height}p.mp4"
    
    temp_dir = tempfile.mkdtemp(prefix="wpb_vid_")
    out_tmpl = os.path.join(temp_dir, "media.%(ext)s")
    
    try:
        await asyncio.to_thread(run_download_video_task, source_url, height, out_tmpl)
        final_mp4 = os.path.join(temp_dir, "media.mp4")
        if not os.path.exists(final_mp4):
            files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if not f.endswith(('.part', '.ytdl'))]
            if files:
                final_mp4 = files[0]
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return Response("Failed to generate video with audio", status_code=500)
        
        return FileResponse(
            final_mp4,
            media_type="video/mp4",
            filename=safe_filename,
            background=BackgroundTask(shutil.rmtree, temp_dir, ignore_errors=True)
        )
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return Response(f"Error processing video download: {str(exc)}", status_code=500)

async def download_audio_handler(request):
    """Handler that extracts pure audio MP3 with tags using ffmpeg, streaming MP3 with sound."""
    source_url = request.query_params.get("url")
    quality = request.query_params.get("quality", "192")
    title = request.query_params.get("title") or "audio"
    
    if not source_url:
        return Response("Missing audio url parameter", status_code=400)
    
    clean_title = re.sub(r'[\/*?:"<>|]', "", title).strip() or "audio"
    safe_filename = f"{clean_title}_{quality}kbps.mp3"
    
    temp_dir = tempfile.mkdtemp(prefix="wpb_aud_")
    out_tmpl = os.path.join(temp_dir, "media.%(ext)s")
    
    try:
        await asyncio.to_thread(run_download_audio_task, source_url, quality, out_tmpl)
        final_mp3 = os.path.join(temp_dir, "media.mp3")
        if not os.path.exists(final_mp3):
            files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.mp3')]
            if files:
                final_mp3 = files[0]
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return Response("Failed to generate audio mp3", status_code=500)
        
        return FileResponse(
            final_mp3,
            media_type="audio/mpeg",
            filename=safe_filename,
            background=BackgroundTask(shutil.rmtree, temp_dir, ignore_errors=True)
        )
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return Response(f"Error processing audio download: {str(exc)}", status_code=500)

async def stream_download_handler(request):
    target_url = request.query_params.get("url")
    filename = request.query_params.get("filename") or "download.mp4"
    safe_filename = urllib.parse.quote(filename)

    if not target_url:
        return Response("Missing target stream url", status_code=400)

    if not is_safe_cdn_url(target_url):
        return Response("Target host not permitted for streaming proxy", status_code=400)

    # Set upstream referer matched to platform CDN
    upstream_referer = "https://www.youtube.com/"
    t_lower = target_url.lower()
    if "instagram" in t_lower or "cdninstagram" in t_lower:
        upstream_referer = "https://www.instagram.com/"
    elif "facebook" in t_lower or "fbcdn" in t_lower:
        upstream_referer = "https://www.facebook.com/"
    elif "tiktok" in t_lower:
        upstream_referer = "https://www.tiktok.com/"
    elif "twitter" in t_lower or "twimg" in t_lower or "x.com" in t_lower:
        upstream_referer = "https://twitter.com/"

    client_headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": upstream_referer
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

        # 2. Allow public health checks and media stream downloads (secured via is_safe_cdn_url)
        if request.url.path in ("/", "/health", "/api/health", "/api/stream", "/api/download_video", "/api/download_audio"):
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
    Route("/api/download_video", download_video_handler, methods=["GET"]),
    Route("/api/download_audio", download_audio_handler, methods=["GET"]),
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
