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

class RedditExtractor(BaseExtractor):
    platform: str = "reddit"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return "reddit.com" in host or "redd.it" in host

    async def resolve(self, url: str) -> ResolveResult:
        canonical_source = url

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

        try:
            info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception as e:
            info = None

        if info:
            title = info.get("title") or "Reddit Post"
            uploader = info.get("uploader") or "Reddit User"
            thumb = info.get("thumbnail")
            
            variants: List[MediaVariant] = []
            formats = info.get("formats") or []
            video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("url")]
            
            if video_formats:
                best_vid = video_formats[-1]
                v_var = MediaVariant(
                    id="video_best",
                    kind="video",
                    ext=best_vid.get("ext") or "mp4",
                    url=best_vid["url"],
                    quality=f"{best_vid.get('height') or 720}p HD",
                    hasAudio=True
                )
                v_var.finalize("reddit_video")
                variants.append(v_var)
            elif thumb:
                i_var = MediaVariant(
                    id="image_main",
                    kind="image",
                    ext="jpg",
                    url=thumb,
                    quality="Original High-Res Photo"
                )
                i_var.finalize("reddit_image")
                variants.append(i_var)
                
            if variants:
                item = MediaItem(
                    index=1,
                    kind="video" if video_formats else "image",
                    variants=variants,
                    thumbnail=thumb,
                    durationSec=info.get("duration")
                )
                metrics_info = MetricsInfo(
                    likes=info.get("like_count"),
                    comments=info.get("comment_count"),
                )
                return ResolveResult(
                    platform="reddit",
                    sourceUrl=canonical_source,
                    title=title,
                    caption=info.get("description") or title,
                    author=AuthorInfo(name=uploader, handle=uploader),
                    metrics=metrics_info,
                    items=[item]
                )

        # Direct JSON fallback: Reddit allows .json URL suffix
        clean_url = canonical_source.split("?")[0].rstrip("/") + ".json"
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "Mozilla/5.0 OVD-Downloader/2.6"}) as client:
            try:
                resp = await client.get(clean_url)
                if resp.status_code == 200:
                    data = resp.json()
                    post_data = data[0]["data"]["children"][0]["data"]
                    title = post_data.get("title") or "Reddit Post"
                    author = post_data.get("author")
                    
                    media_items = []
                    # Check for video
                    if post_data.get("is_video") and post_data.get("media"):
                        vid_url = post_data["media"]["reddit_video"]["fallback_url"]
                        v_var = MediaVariant(id="video_hd", kind="video", ext="mp4", url=vid_url, quality="HD Video")
                        v_var.finalize("reddit_video", title=title)
                        media_items.append(MediaItem(index=1, kind="video", variants=[v_var], thumbnail=post_data.get("thumbnail")))
                    elif post_data.get("url_overridden_by_dest"):
                        dest = post_data["url_overridden_by_dest"]
                        if any(dest.lower().endswith(x) for x in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
                            ext = dest.split(".")[-1].split("?")[0]
                            i_var = MediaVariant(id="img_1", kind="image", ext=ext, url=dest, quality="Full Resolution Image")
                            i_var.finalize("reddit_image", title=title)
                            media_items.append(MediaItem(index=1, kind="image", variants=[i_var], thumbnail=dest))
                            
                    if media_items:
                        return ResolveResult(
                            platform="reddit",
                            sourceUrl=canonical_source,
                            title=title,
                            author=AuthorInfo(name=author, handle=f"u/{author}"),
                            items=media_items
                        )
            except Exception:
                pass

        raise AppError(ErrorCode.NO_MEDIA, "No downloadable video or photo was found in this Reddit post.")
