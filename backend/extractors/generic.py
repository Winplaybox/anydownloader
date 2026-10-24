import re
import urllib.parse
import asyncio
from typing import Dict, Any, List, Optional
import httpx
import yt_dlp

try:
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    try:
        from utils.errors import AppError, ErrorCode
    except (ModuleNotFoundError, ImportError):
        from ..utils.errors import AppError, ErrorCode
try:
    from backend.extractors.base import (
        BaseExtractor,
        ResolveResult,
        MediaItem,
        MediaVariant,
        AuthorInfo,
    )
except (ModuleNotFoundError, ImportError):
    try:
        from extractors.base import (
            BaseExtractor,
            ResolveResult,
            MediaItem,
            MediaVariant,
            AuthorInfo,
        )
    except (ModuleNotFoundError, ImportError):
        from .base import (
            BaseExtractor,
            ResolveResult,
            MediaItem,
            MediaVariant,
            AuthorInfo,
        )

class GenericExtractor(BaseExtractor):
    platform: str = "generic"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme in ("http", "https") and "." in parsed.netloc
        except Exception:
            return False

    async def resolve(self, url: str) -> ResolveResult:
        canonical_source = url
        
        # 1. First attempt yt-dlp generic engine (supports 1,000+ sites)
        loop = asyncio.get_running_loop()
        def _run_ytdlp():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "socket_timeout": 12,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(canonical_source, download=False)

        info = None
        try:
            info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception:
            info = None

        if info:
            title = info.get("title") or "Website Video / Media"
            uploader = info.get("uploader") or info.get("extractor") or "Web Creator"
            thumb = info.get("thumbnail")
            
            variants: List[MediaVariant] = []
            formats = info.get("formats") or []
            
            # Filter clean video formats
            video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("url")]
            if video_formats:
                # Add best and medium quality variants
                best_vid = video_formats[-1]
                v_var1 = MediaVariant(
                    id="video_best",
                    kind="video",
                    ext=best_vid.get("ext") or "mp4",
                    url=best_vid["url"],
                    quality=f"{best_vid.get('height') or 720}p HD Quality",
                    width=best_vid.get("width"),
                    height=best_vid.get("height"),
                    hasAudio=True
                )
                v_var1.finalize("web_video")
                variants.append(v_var1)
                
                if len(video_formats) > 1:
                    mid_vid = video_formats[len(video_formats)//2]
                    v_var2 = MediaVariant(
                        id="video_standard",
                        kind="video",
                        ext=mid_vid.get("ext") or "mp4",
                        url=mid_vid["url"],
                        quality=f"{mid_vid.get('height') or 480}p Standard",
                        width=mid_vid.get("width"),
                        height=mid_vid.get("height"),
                        hasAudio=True
                    )
                    v_var2.finalize("web_video_sd")
                    variants.append(v_var2)
            
            if thumb:
                i_var = MediaVariant(
                    id="image_main",
                    kind="image",
                    ext="jpg",
                    url=thumb,
                    quality="Cover Artwork / Image"
                )
                i_var.finalize("web_cover")
                variants.append(i_var)
                
            if variants:
                item = MediaItem(
                    index=1,
                    kind="video" if video_formats else "image",
                    variants=variants,
                    thumbnail=thumb,
                    durationSec=info.get("duration")
                )
                return ResolveResult(
                    platform="generic",
                    sourceUrl=canonical_source,
                    title=title,
                    author=AuthorInfo(name=uploader, handle=uploader),
                    items=[item]
                )

        # 2. Fallback: Direct HTML OpenGraph & Media Element Scraper
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
            try:
                resp = await client.get(canonical_source)
                html_text = resp.text
            except Exception:
                raise AppError(ErrorCode.UPSTREAM_FAILED, "Could not reach target website. Check the URL and try again.")

        title_m = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.IGNORECASE | re.DOTALL)
        title = title_m.group(1).strip() if title_m else "Extracted Web Media"
        title = re.sub(r'\s+', ' ', title)[:120]

        og_video = re.search(r'property="og:video(?::secure_url|:url)?"\s+content="([^"]+)"', html_text, re.I)
        og_image = re.search(r'property="og:image"\s+content="([^"]+)"', html_text, re.I)

        variants: List[MediaVariant] = []

        if og_video:
            v_url = og_video.group(1)
            v_var = MediaVariant(id="video_og", kind="video", ext="mp4", url=v_url, quality="Original Video Stream")
            v_var.finalize("extracted_video")
            variants.append(v_var)

        if og_image:
            i_url = og_image.group(1)
            i_var = MediaVariant(id="image_og", kind="image", ext="jpg", url=i_url, quality="High Resolution Artwork")
            i_var.finalize("extracted_image")
            variants.append(i_var)

        # Also search for HTML5 <video src="..."> tags
        if not variants:
            video_tags = re.findall(r'<video[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
            if not video_tags:
                source_tags = re.findall(r'<source[^>]+src=["\']([^"\']+)["\'][^>]+type=["\']video/mp4["\']', html_text, re.I)
                video_tags = source_tags
            if video_tags:
                v_url = urllib.parse.urljoin(canonical_source, video_tags[0])
                v_var = MediaVariant(id="video_html5", kind="video", ext="mp4", url=v_url, quality="Direct HTML5 Video")
                v_var.finalize("web_video")
                variants.append(v_var)

        if not variants:
            raise AppError(ErrorCode.NO_MEDIA, "No downloadable video or photo was found on this webpage.")

        item = MediaItem(
            index=1,
            kind="video" if any(v.kind == "video" for v in variants) else "image",
            variants=variants,
            thumbnail=og_image.group(1) if og_image else None
        )

        return ResolveResult(
            platform="generic",
            sourceUrl=canonical_source,
            title=title,
            items=[item]
        )
