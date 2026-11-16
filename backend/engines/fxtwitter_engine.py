import httpx
import re
from typing import AsyncIterator, Dict, Any, Optional, List

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode

class FxTwitterEngine:
    id: str = "fxtwitter"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        m = re.search(r'/(?:status|i/status)/(\d+)', url)
        if not m:
            raise AppError(ErrorCode.URL_INVALID, "Invalid Twitter status URL.")
        tweet_id = m.group(1)

        api_url = f"https://api.fxtwitter.com/status/{tweet_id}"
        headers = {
            "User-Agent": "TelegramBot (like TwitterBot)",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=ctx.timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 404:
                    raise AppError(ErrorCode.NOT_FOUND, "Tweet was deleted or does not exist.")
                if resp.status_code != 200:
                    raise AppError(ErrorCode.UPSTREAM_FAILED, f"FxTwitter status {resp.status_code}")
                data = resp.json()
            except AppError:
                raise
            except Exception as e:
                raise AppError(ErrorCode.UPSTREAM_FAILED, f"FxTwitter request failed: {e}")

        tweet = data.get("tweet")
        if not tweet:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "No tweet data in FxTwitter response.")

        author_data = tweet.get("author") or {}
        author = {
            "username": author_data.get("screen_name"),
            "displayName": author_data.get("name"),
            "avatar": author_data.get("avatar_url"),
            "profileUrl": f"https://x.com/{author_data.get('screen_name')}" if author_data.get("screen_name") else None
        }

        stats = {}
        if tweet.get("views") is not None:
            stats["views"] = tweet["views"]
        if tweet.get("likes") is not None:
            stats["likes"] = tweet["likes"]
        if tweet.get("replies") is not None:
            stats["comments"] = tweet["replies"]
        if tweet.get("retweets") is not None:
            stats["shares"] = tweet["retweets"]

        raw_items: List[RawItem] = []
        media = tweet.get("media") or {}
        videos = media.get("videos") or []
        photos = media.get("photos") or []

        for idx, v in enumerate(videos):
            variants_raw = v.get("variants") or []
            mp4_vars = [
                vr for vr in variants_raw
                if (vr.get("content_type") == "video/mp4" or (vr.get("url") and ".mp4" in vr.get("url"))) and vr.get("url")
            ]
            for vr in mp4_vars:
                raw_items.append(RawItem(
                    kind="video",
                    url=vr["url"],
                    label="HD Video" if not v.get("type") == "gif" else "Looping GIF (MP4)",
                    ext="mp4",
                    has_audio=v.get("type") != "gif"
                ))

        for idx, p in enumerate(photos):
            p_url = p.get("url")
            if p_url:
                raw_items.append(RawItem(
                    kind="image",
                    url=p_url,
                    label=f"Photo {idx+1} (Original ?name=orig)",
                    ext="jpg",
                    width=p.get("width"),
                    height=p.get("height")
                ))

        if not raw_items:
            raise AppError(ErrorCode.NO_MEDIA, "This post contains no video or photo media to download.")

        tweet_text = tweet.get("text") or "X Post"
        return RawResult(
            engine_id=self.id,
            id=tweet_id,
            url=url,
            platform="twitter",
            title=tweet_text,
            description=tweet_text,
            caption=tweet_text,
            author=author,
            stats=stats if stats else None,
            items=raw_items,
            raw_payload=tweet
        )

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
