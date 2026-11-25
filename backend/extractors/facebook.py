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

class FacebookExtractor(BaseExtractor):
    platform: str = "facebook"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return "facebook.com" in host or "fb.watch" in host

    async def resolve(self, url: str) -> ResolveResult:
        canonical_source = url

        # 1. Primary Extraction: yt-dlp
        ytdlp_info = None
        try:
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
            ytdlp_info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception as e:
            err_str = str(e).lower()
            if "login" in err_str or "private" in err_str or "group" in err_str:
                raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
            if "does not exist" in err_str or "deleted" in err_str or "not found" in err_str:
                raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")

        # 2. Secondary Fallback: Direct HTML OpenGraph & Regex Scraping
        if not ytdlp_info:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                try:
                    resp = await client.get(canonical_source, headers=headers)
                    if resp.status_code == 200:
                        html_text = resp.text
                        hd_m = re.search(r'hd_src:"([^"]+)"', html_text) or re.search(r'"playable_url_quality_hd":"([^"]+)"', html_text)
                        sd_m = re.search(r'sd_src:"([^"]+)"', html_text) or re.search(r'"playable_url":"([^"]+)"', html_text)

                        v_vars = []
                        if hd_m:
                            hd_url = hd_m.group(1).replace(r'\/', '/')
                            v_hd = MediaVariant(id="fb-hd", kind="video", ext="mp4", url=hd_url, quality="HD 720p", hasAudio=True)
                            v_hd.finalize("facebook_video_hd")
                            v_vars.append(v_hd)
                        if sd_m:
                            sd_url = sd_m.group(1).replace(r'\/', '/')
                            v_sd = MediaVariant(id="fb-sd", kind="video", ext="mp4", url=sd_url, quality="SD 360p", hasAudio=True)
                            v_sd.finalize("facebook_video_sd")
                            v_vars.append(v_sd)

                        if v_vars:
                            return ResolveResult(
                                platform=self.platform,
                                sourceUrl=canonical_source,
                                title="Facebook Video",
                                items=[MediaItem(index=1, kind="video", variants=v_vars)]
                            )
                except Exception:
                    pass
            raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

        # Process yt-dlp formats (SD & HD)
        title = ytdlp_info.get("title") or "Facebook Media"
        author_info = AuthorInfo(
            name=ytdlp_info.get("uploader") or ytdlp_info.get("channel"),
            handle=ytdlp_info.get("uploader_id"),
            avatar=ytdlp_info.get("thumbnail"),
        )

        fmts = [
            f for f in ytdlp_info.get("formats", [])
            if f.get("url") and f.get("vcodec") != "none"
        ]
        fmts.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)

        v_vars: List[MediaVariant] = []
        seen_res = set()

        for idx, f in enumerate(fmts):
            h = f.get("height") or 720
            q_label = f"HD {h}p" if h >= 720 else f"SD {h}p"
            if q_label in seen_res:
                continue
            seen_res.add(q_label)

            var = MediaVariant(
                id=f"fb-vid-{idx}-{h}p",
                kind="video",
                ext="mp4",
                url=f.get("url"),
                quality=q_label,
                width=f.get("width"),
                height=h,
                hasAudio=True
            )
            var.finalize("facebook_video", title=title)
            v_vars.append(var)

        items = []
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

        metrics_info = MetricsInfo(
            likes=ytdlp_info.get("like_count"),
            comments=ytdlp_info.get("comment_count"),
            views=ytdlp_info.get("view_count"),
        )
        return ResolveResult(
            platform=self.platform,
            sourceUrl=canonical_source,
            title=title,
            caption=ytdlp_info.get("description") or title,
            author=author_info,
            metrics=metrics_info,
            items=items
        )
