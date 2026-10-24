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
        MetricsInfo,
    )
except (ModuleNotFoundError, ImportError):
    try:
        from extractors.base import (
            BaseExtractor,
            ResolveResult,
            MediaItem,
            MediaVariant,
            AuthorInfo,
        MetricsInfo,
        )
    except (ModuleNotFoundError, ImportError):
        from .base import (
            BaseExtractor,
            ResolveResult,
            MediaItem,
            MediaVariant,
            AuthorInfo,
        MetricsInfo,
        )

class PinterestExtractor(BaseExtractor):
    platform: str = "pinterest"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return "pinterest.com" in host or "pin.it" in host

    async def resolve(self, url: str) -> ResolveResult:
        canonical_source = url
        
        # Follow redirects if pin.it
        if "pin.it" in url:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                try:
                    resp = await client.head(url)
                    canonical_source = str(resp.url)
                except Exception:
                    pass

        # 1. Try yt-dlp first
        ytdlp_info = None
        try:
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
            ytdlp_info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception:
            ytdlp_info = None

        if ytdlp_info:
            title = ytdlp_info.get("title") or "Pinterest Media"
            uploader = ytdlp_info.get("uploader") or "Pinterest Creator"
            thumb = ytdlp_info.get("thumbnail")
            
            variants: List[MediaVariant] = []
            
            # If video formats found
            formats = ytdlp_info.get("formats") or []
            video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("url")]
            
            if video_formats:
                best_vid = video_formats[-1]
                vid_var = MediaVariant(
                    id="video_hd",
                    kind="video",
                    ext=best_vid.get("ext") or "mp4",
                    url=best_vid["url"],
                    quality=f"{best_vid.get('height') or 720}p HD",
                    width=best_vid.get("width"),
                    height=best_vid.get("height"),
                    sizeBytes=best_vid.get("filesize"),
                    hasAudio=True
                )
                vid_var.finalize("pinterest_video")
                variants.append(vid_var)
                
            # If image or thumbnail
            if thumb:
                img_var = MediaVariant(
                    id="image_orig",
                    kind="image",
                    ext="jpg",
                    url=thumb,
                    quality="Original High-Res Photo",
                )
                img_var.finalize("pinterest_image")
                variants.append(img_var)
                
            if variants:
                item = MediaItem(
                    index=1,
                    kind="video" if video_formats else "image",
                    variants=variants,
                    thumbnail=thumb,
                    durationSec=ytdlp_info.get("duration")
                )
                metrics_info = MetricsInfo(
                    likes=ytdlp_info.get("like_count") or ytdlp_info.get("repost_count"),
                    comments=ytdlp_info.get("comment_count"),
                )
                return ResolveResult(
                    platform="pinterest",
                    sourceUrl=canonical_source,
                    title=title,
                    caption=ytdlp_info.get("description") or title,
                    author=AuthorInfo(name=uploader, handle=uploader),
                    metrics=metrics_info,
                    items=[item]
                )

        # 2. Fallback: Direct OpenGraph / HTML Scraping
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"}) as client:
            try:
                resp = await client.get(canonical_source)
                html_text = resp.text
            except Exception:
                raise AppError(ErrorCode.UPSTREAM_FAILED, "Could not reach Pinterest. Please try again.")

        og_img_m = re.search(r'property="og:image"\s+content="([^"]+)"', html_text)
        og_video_m = re.search(r'property="og:video"\s+content="([^"]+)"', html_text)
        og_title_m = re.search(r'property="og:title"\s+content="([^"]+)"', html_text)

        title = og_title_m.group(1) if og_title_m else "Pinterest Media"
        variants: List[MediaVariant] = []

        if og_video_m:
            v_url = og_video_m.group(1)
            v_var = MediaVariant(id="video_main", kind="video", ext="mp4", url=v_url, quality="HD Video")
            v_var.finalize("pinterest_video")
            variants.append(v_var)

        if og_img_m:
            i_url = og_img_m.group(1).replace("236x", "originals").replace("474x", "originals").replace("736x", "originals")
            i_var = MediaVariant(id="image_orig", kind="image", ext="jpg", url=i_url, quality="Original High-Res Image")
            i_var.finalize("pinterest_image")
            variants.append(i_var)

        if not variants:
            raise AppError(ErrorCode.NO_MEDIA, "No downloadable image or video was found in this Pin.")

        item = MediaItem(
            index=1,
            kind="video" if og_video_m else "image",
            variants=variants,
            thumbnail=og_img_m.group(1) if og_img_m else None
        )

        return ResolveResult(
            platform="pinterest",
            sourceUrl=canonical_source,
            title=title,
            items=[item]
        )
