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

class TikTokExtractor(BaseExtractor):
    platform: str = "tiktok"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return "tiktok.com" in host

    async def resolve(self, url: str) -> ResolveResult:
        canonical_source = url

        # Primary Method: TikWM Public API (Extracts No-Watermark MP4 and Photo slides)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        data = None
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.post("https://www.tikwm.com/api/", data={"url": canonical_source}, headers=headers)
                if resp.status_code == 200:
                    json_data = resp.json()
                    if json_data.get("code") == 0:
                        data = json_data.get("data")
                    elif json_data.get("code") in (-1, 404):
                        raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
                    elif json_data.get("code") in (401, 403):
                        raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
            except AppError:
                raise
            except Exception:
                data = None

        items: List[MediaItem] = []
        author_info = None
        title = ""

        if data:
            title = data.get("title") or "TikTok Post"
            author_data = data.get("author") or {}
            author_info = AuthorInfo(
                name=author_data.get("nickname"),
                handle=author_data.get("unique_id"),
                avatar=author_data.get("avatar"),
            )

            # Check if Photo Mode
            images = data.get("images") or []
            if images:
                for idx, img_url in enumerate(images):
                    var = MediaVariant(
                        id=f"tt-img-{idx}-orig",
                        kind="image",
                        ext="jpg",
                        url=img_url,
                        quality="orig",
                    )
                    var.finalize(f"tiktok_photo_{idx+1}")
                    items.append(MediaItem(
                        index=idx + 1,
                        kind="image",
                        thumbnail=img_url,
                        variants=[var]
                    ))

            # Video: No watermark & watermark variants
            v_vars: List[MediaVariant] = []
            hd_url = data.get("hdplay")
            play_url = data.get("play")
            wm_url = data.get("wmplay")

            if hd_url:
                var_hd = MediaVariant(
                    id="tt-vid-hd",
                    kind="video",
                    ext="mp4",
                    url=hd_url,
                    quality="HD (No Watermark)",
                    hasAudio=True
                )
                var_hd.finalize("tiktok_video_hd_nowatermark")
                v_vars.append(var_hd)

            if play_url and play_url != hd_url:
                var_nowm = MediaVariant(
                    id="tt-vid-nowm",
                    kind="video",
                    ext="mp4",
                    url=play_url,
                    quality="No Watermark (MP4)",
                    hasAudio=True
                )
                var_nowm.finalize("tiktok_video_nowatermark")
                v_vars.append(var_nowm)

            if wm_url:
                var_wm = MediaVariant(
                    id="tt-vid-wm",
                    kind="video",
                    ext="mp4",
                    url=wm_url,
                    quality="With Watermark (MP4)",
                    hasAudio=True
                )
                var_wm.finalize("tiktok_video_watermark")
                v_vars.append(var_wm)

            if v_vars:
                items.insert(0, MediaItem(
                    index=1 if not images else len(items) + 1,
                    kind="video",
                    thumbnail=data.get("cover"),
                    durationSec=data.get("duration"),
                    variants=v_vars
                ))

        # Secondary Fallback: yt-dlp
        if not items:
            try:
                loop = asyncio.get_running_loop()
                def _run_ytdlp():
                    ydl_opts = {
                        "quiet": True,
                        "no_warnings": True,
                        "skip_download": True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(canonical_source, download=False)
                ytdlp_info = await loop.run_in_executor(None, _run_ytdlp)
            except Exception as e:
                err_str = str(e).lower()
                if "does not exist" in err_str or "deleted" in err_str or "not found" in err_str:
                    raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
                if "private" in err_str or "restricted" in err_str:
                    raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
                raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

            if ytdlp_info:
                title = ytdlp_info.get("title") or "TikTok Post"
                author_info = AuthorInfo(
                    name=ytdlp_info.get("uploader"),
                    handle=ytdlp_info.get("uploader_id"),
                    avatar=ytdlp_info.get("thumbnail"),
                )

                fmts = [f for f in ytdlp_info.get("formats", []) if f.get("url") and f.get("vcodec") != "none"]
                fmts.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)

                v_vars = []
                for idx, f in enumerate(fmts):
                    h = f.get("height") or 720
                    var = MediaVariant(
                        id=f"tt-vid-yt-{idx}",
                        kind="video",
                        ext="mp4",
                        url=f.get("url"),
                        quality=f"{h}p HD",
                        hasAudio=True
                    )
                    var.finalize("tiktok_video")
                    v_vars.append(var)

                if v_vars:
                    items.append(MediaItem(
                        index=1,
                        kind="video",
                        thumbnail=ytdlp_info.get("thumbnail"),
                        durationSec=ytdlp_info.get("duration"),
                        variants=v_vars
                    ))

        if not items:
            raise AppError(ErrorCode.NO_MEDIA, "This post has no video or image to download.")

        return ResolveResult(
            platform=self.platform,
            sourceUrl=canonical_source,
            title=title,
            author=author_info,
            items=items
        )
