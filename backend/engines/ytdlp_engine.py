import asyncio
import os
import re
from typing import AsyncIterator, Dict, Any, Optional, List
import yt_dlp
import httpx

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode

class YtDlpEngine:
    id: str = "ytdlp"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        loop = asyncio.get_running_loop()

        def _run_ytdlp():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "noplaylist": True,
                "socket_timeout": ctx.timeout,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            }
            if ctx.cookies_path and os.path.exists(ctx.cookies_path):
                ydl_opts["cookiefile"] = ctx.cookies_path
            if ctx.proxy:
                ydl_opts["proxy"] = ctx.proxy

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception as e:
            err_str = str(e).lower()
            if "private" in err_str or "login" in err_str or "sign in" in err_str:
                raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private or requires login.")
            if "not found" in err_str or "deleted" in err_str or "unavailable" in err_str:
                raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or does not exist.")
            raise AppError(ErrorCode.UPSTREAM_FAILED, f"yt-dlp extraction failed: {e}")

        if not info:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "No info extracted.")

        # Build RawResult
        item_id = str(info.get("id") or "media")
        title = info.get("title") or "Media"
        desc = info.get("description") or title
        uploader = info.get("uploader") or info.get("channel") or "Creator"
        handle = info.get("uploader_id") or info.get("channel_id") or uploader
        thumb = info.get("thumbnail")

        author = {
            "username": handle,
            "displayName": uploader,
            "avatar": thumb,
            "profileUrl": info.get("uploader_url") or info.get("channel_url")
        }

        # Stats
        stats = {}
        if info.get("view_count") is not None:
            stats["views"] = info["view_count"]
        if info.get("like_count") is not None:
            stats["likes"] = info["like_count"]
        if info.get("comment_count") is not None:
            stats["comments"] = info["comment_count"]
        if info.get("repost_count") is not None:
            stats["shares"] = info["repost_count"]

        raw_items: List[RawItem] = []
        formats = info.get("formats", [])

        # Process Video / Audio formats
        seen_res = set()
        for f in formats:
            v_url = f.get("url")
            if not v_url or not v_url.startswith("http"):
                continue

            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            h = f.get("height")
            w = f.get("width")
            ext = f.get("ext") or "mp4"

            # Video streams
            if vcodec and vcodec != "none":
                has_audio = (acodec and acodec != "none")
                needs_merge = not has_audio
                q_label = f"{h}p" if h else "HD"
                if f.get("fps") and f["fps"] > 30:
                    q_label += f"{f['fps']}"

                key = (q_label, needs_merge)
                if key in seen_res:
                    continue
                seen_res.add(key)

                raw_items.append(RawItem(
                    kind="video",
                    url=v_url,
                    label=q_label,
                    ext=ext,
                    width=w,
                    height=h,
                    fps=f.get("fps"),
                    vcodec=vcodec,
                    acodec=acodec,
                    filesize=f.get("filesize") or f.get("filesize_approx"),
                    has_audio=has_audio,
                    needs_merge=needs_merge,
                    headers=f.get("http_headers")
                ))

            # Audio-only streams
            elif acodec and acodec != "none" and (not vcodec or vcodec == "none"):
                raw_items.append(RawItem(
                    kind="audio",
                    url=v_url,
                    label=f"{f.get('abr') or 128}kbps Audio",
                    ext=ext,
                    filesize=f.get("filesize") or f.get("filesize_approx"),
                    headers=f.get("http_headers")
                ))

        # Thumbnails
        for t in info.get("thumbnails", [])[:5]:
            t_url = t.get("url")
            if t_url:
                raw_items.append(RawItem(
                    kind="thumbnail",
                    url=t_url,
                    label=f"{t.get('height') or 'HQ'}p Thumbnail",
                    width=t.get("width"),
                    height=t.get("height")
                ))

        return RawResult(
            engine_id=self.id,
            id=item_id,
            url=url,
            platform=ctx.platform_id or "generic",
            title=title,
            description=desc,
            caption=desc,
            author=author,
            stats=stats if stats else None,
            duration=info.get("duration"),
            tags=info.get("tags") or [],
            items=raw_items,
            raw_payload=info
        )

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        headers = item.headers or {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
