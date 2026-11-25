import re
import urllib.parse
import asyncio
from typing import Dict, Any, List, Optional
import yt_dlp

try:
    from backend.utils.ytdlp_opts import robust_opts as _ytdlp_opts
except (ModuleNotFoundError, ImportError):
    from utils.ytdlp_opts import robust_opts as _ytdlp_opts

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

class YouTubeExtractor(BaseExtractor):
    platform: str = "youtube"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return "youtube.com" in host or "youtu.be" in host

    async def resolve(self, url: str) -> ResolveResult:
        # Extract YouTube Video ID
        vid_m = re.search(r'(?:v=|youtu\.be\/|shorts\/|live\/)([a-zA-Z0-9_-]{11})', url)
        if not vid_m:
            # Check if channel or playlist without v=
            if any(x in url for x in ("/@", "/channel/", "/c/", "/user/")):
                raise AppError(
                    ErrorCode.NO_MEDIA,
                    "This post has no video or image to download. Please paste a video or shorts link."
                )
            raise AppError(ErrorCode.URL_INVALID, "That doesn't look like a valid link.")

        video_id = vid_m.group(1)
        canonical_source = f"https://www.youtube.com/watch?v={video_id}"

        loop = asyncio.get_running_loop()
        def _run_ytdlp():
            ydl_opts = _ytdlp_opts("extract")
            ydl_opts["skip_download"] = True
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(canonical_source, download=False)

        try:
            info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception as e:
            err_str = str(e).lower()
            if "private" in err_str or "login" in err_str or "age" in err_str or "restricted" in err_str:
                raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
            if "does not exist" in err_str or "unavailable" in err_str or "deleted" in err_str:
                raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
            raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

        if not info:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

        title = info.get("title") or f"YouTube Video {video_id}"
        caption = info.get("description") or title
        uploader = info.get("uploader") or info.get("channel")
        handle = info.get("uploader_id") or info.get("channel_id") or uploader
        author_info = AuthorInfo(
            name=uploader,
            handle=handle,
            avatar=info.get("thumbnail"),
        )
        metrics_info = MetricsInfo(
            likes=info.get("like_count"),
            comments=info.get("comment_count"),
            views=info.get("view_count"),
        )

        items: List[MediaItem] = []

        # 1. Video Item. Never expose raw googlevideo/HLS (m3u8) URLs: they are IP-bound
        # and an m3u8 manifest saved as ".mp4" is not a video. Every quality is served by
        # /api/download_video, which downloads and merges video+audio server-side.
        formats = info.get("formats", [])
        heights = sorted({
            min(int(f.get("height")), 1080)
            for f in formats
            if f.get("vcodec") not in (None, "none") and f.get("height")
            and int(f.get("height")) >= 144
        }, reverse=True)
        if not heights:
            heights = [1080, 720, 480, 360]

        title_q = urllib.parse.quote(re.sub(r'[\\/*?:"<>|]', "", title).strip() or "video")
        src_q = urllib.parse.quote(canonical_source, safe="")
        v_vars: List[MediaVariant] = []
        for h in heights:
            q_label = f"{h}p Full HD" if h >= 1080 else f"{h}p HD" if h >= 720 else f"{h}p SD"
            var = MediaVariant(
                id=f"yt-{video_id}-{h}p",
                kind="video",
                ext="mp4",
                url=f"/api/download_video?url={src_q}&height={h}&title={title_q}",
                quality=q_label,
                height=h,
                hasAudio=True,
            )
            var.finalize(f"youtube_{video_id}", title=title)
            v_vars.append(var)

        if v_vars:
            items.append(MediaItem(
                index=1,
                kind="video",
                thumbnail=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                durationSec=info.get("duration"),
                variants=v_vars
            ))

        # 2. Thumbnail Image Item (MaxRes + HQ)
        maxres_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        hq_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        var_maxres = MediaVariant(
            id=f"yt-{video_id}-thumb-maxres",
            kind="image",
            ext="jpg",
            url=maxres_url,
            quality="Max Resolution (1080p)",
        )
        var_maxres.finalize(f"youtube_{video_id}_thumbnail_maxres", title=title)

        var_hq = MediaVariant(
            id=f"yt-{video_id}-thumb-hq",
            kind="image",
            ext="jpg",
            url=hq_url,
            quality="Standard (480p)",
        )
        var_hq.finalize(f"youtube_{video_id}_thumbnail", title=title)

        items.append(MediaItem(
            index=2,
            kind="image",
            thumbnail=maxres_url,
            variants=[var_maxres, var_hq]
        ))

        return ResolveResult(
            platform=self.platform,
            sourceUrl=canonical_source,
            title=title,
            caption=caption or title,
            author=author_info,
            metrics=metrics_info,
            items=items
        )
