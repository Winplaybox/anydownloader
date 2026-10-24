import httpx
from typing import AsyncIterator, Dict, Any, Optional, List

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode

class TikWmEngine:
    id: str = "tikwm"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient(timeout=ctx.timeout, follow_redirects=True) as client:
            try:
                resp = await client.post("https://www.tikwm.com/api/", data={"url": url}, headers=headers)
                if resp.status_code != 200:
                    raise AppError(ErrorCode.UPSTREAM_FAILED, "TikWM API returned non-200.")
                data_json = resp.json()
            except Exception as e:
                raise AppError(ErrorCode.UPSTREAM_FAILED, f"TikWM request failed: {e}")

        code = data_json.get("code")
        if code != 0:
            msg = data_json.get("msg", "").lower()
            if "not found" in msg or "deleted" in msg:
                raise AppError(ErrorCode.NOT_FOUND, "TikTok post deleted or not found.")
            if "private" in msg:
                raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "TikTok video is private.")
            raise AppError(ErrorCode.UPSTREAM_FAILED, f"TikWM error: {data_json.get('msg')}")

        d = data_json.get("data", {})
        item_id = str(d.get("id") or "tiktok_media")
        title = d.get("title") or "TikTok Post"
        author_data = d.get("author", {})

        author = {
            "username": author_data.get("unique_id"),
            "displayName": author_data.get("nickname"),
            "avatar": author_data.get("avatar"),
            "profileUrl": f"https://www.tiktok.com/@{author_data.get('unique_id')}" if author_data.get("unique_id") else None
        }

        stats = {}
        if d.get("play_count") is not None:
            stats["views"] = d["play_count"]
        if d.get("digg_count") is not None:
            stats["likes"] = d["digg_count"]
        if d.get("comment_count") is not None:
            stats["comments"] = d["comment_count"]
        if d.get("share_count") is not None:
            stats["shares"] = d["share_count"]

        raw_items: List[RawItem] = []

        # Slideshow images
        images = d.get("images") or []
        if images:
            for idx, img_url in enumerate(images):
                raw_items.append(RawItem(
                    kind="image",
                    url=img_url,
                    label=f"Photo {idx+1} (Full HD)",
                    ext="jpg"
                ))

        # Videos: HD & Standard (No Watermark)
        hdplay = d.get("hdplay")
        play = d.get("play")
        wmplay = d.get("wmplay")

        if hdplay:
            raw_items.append(RawItem(
                kind="video",
                url=hdplay,
                label="1080p HD (No Watermark)",
                ext="mp4",
                has_audio=True
            ))
        if play and play != hdplay:
            raw_items.append(RawItem(
                kind="video",
                url=play,
                label="720p (No Watermark)",
                ext="mp4",
                has_audio=True
            ))
        if wmplay and not hdplay and not play:
            raw_items.append(RawItem(
                kind="video",
                url=wmplay,
                label="Standard (Watermarked)",
                ext="mp4",
                has_audio=True
            ))

        # Audio
        music_url = d.get("music")
        music_info = d.get("music_info", {})
        if music_url:
            raw_items.append(RawItem(
                kind="audio",
                url=music_url,
                label="Original Sound (MP3)",
                ext="mp3"
            ))

        return RawResult(
            engine_id=self.id,
            id=item_id,
            url=url,
            platform="tiktok",
            title=title,
            description=title,
            caption=title,
            author=author,
            stats=stats if stats else None,
            duration=d.get("duration"),
            music={"title": music_info.get("title"), "author": music_info.get("author")},
            items=raw_items,
            raw_payload=d
        )

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
