import re
import urllib.parse
import asyncio
from typing import Dict, Any, List, Optional
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
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "socket_timeout": 10,
            }
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
        uploader = info.get("uploader") or info.get("channel")
        author_info = AuthorInfo(
            name=uploader,
            handle=uploader,
            avatar=info.get("thumbnail"),
        )

        items: List[MediaItem] = []

        # 1. Video Item (Progressive MP4 variants)
        formats = info.get("formats", [])
        # Filter for video formats
        v_fmts = [
            f for f in formats
            if f.get("url") and f.get("vcodec") != "none" and (f.get("ext") == "mp4" or f.get("container") == "mp4_dash")
        ]
        # Prefer progressive (vcodec != none and acodec != none)
        prog_fmts = [f for f in v_fmts if f.get("acodec") != "none"]
        candidate_fmts = prog_fmts if prog_fmts else v_fmts
        candidate_fmts.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)

        v_vars: List[MediaVariant] = []
        seen_res = set()

        for idx, f in enumerate(candidate_fmts):
            h = f.get("height") or 720
            # Cap at 1080p for Phase 1 (no 4K claims)
            if h > 1080:
                h = 1080
            q_label = f"{h}p Full HD" if h >= 1080 else f"{h}p HD" if h >= 720 else f"{h}p SD"
            if q_label in seen_res:
                continue
            seen_res.add(q_label)

            var = MediaVariant(
                id=f"yt-{video_id}-{idx}-{h}p",
                kind="video",
                ext="mp4",
                url=f.get("url"),
                quality=q_label,
                width=f.get("width"),
                height=h,
                hasAudio=True
            )
            var.finalize(f"youtube_{video_id}")
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
        var_maxres.finalize(f"youtube_{video_id}_thumbnail_maxres")

        var_hq = MediaVariant(
            id=f"yt-{video_id}-thumb-hq",
            kind="image",
            ext="jpg",
            url=hq_url,
            quality="Standard (480p)",
        )
        var_hq.finalize(f"youtube_{video_id}_thumbnail")

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
            author=author_info,
            items=items
        )
