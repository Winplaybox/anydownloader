import httpx
from typing import AsyncIterator, Dict, Any, Optional, List

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode

class RedditEngine:
    id: str = "reddit_json"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        clean_url = url.split("?")[0].rstrip("/") + ".json"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; OVD-Downloader/3.0; +https://ovd.winplaybox.in)",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=ctx.timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(clean_url, headers=headers)
                if resp.status_code == 404:
                    raise AppError(ErrorCode.NOT_FOUND, "Reddit post not found or removed.")
                if resp.status_code != 200:
                    raise AppError(ErrorCode.UPSTREAM_FAILED, f"Reddit API returned {resp.status_code}")
                data = resp.json()
            except AppError:
                raise
            except Exception as e:
                raise AppError(ErrorCode.UPSTREAM_FAILED, f"Reddit request failed: {e}")

        try:
            post = data[0]["data"]["children"][0]["data"]
        except Exception:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "Unexpected Reddit JSON structure.")

        post_id = post.get("id") or "reddit_media"
        title = post.get("title") or "Reddit Post"
        author_name = post.get("author") or "redditor"
        subreddit = post.get("subreddit")

        author = {
            "username": f"u/{author_name}",
            "displayName": author_name,
            "profileUrl": f"https://www.reddit.com/user/{author_name}"
        }

        stats = {}
        if post.get("score") is not None:
            stats["likes"] = post["score"]
        if post.get("num_comments") is not None:
            stats["comments"] = post["num_comments"]

        raw_items: List[RawItem] = []

        # Check Video (v.redd.it)
        if post.get("is_video") and post.get("media") and post["media"].get("reddit_video"):
            rv = post["media"]["reddit_video"]
            vid_url = rv.get("fallback_url")
            if vid_url:
                h = rv.get("height") or 720
                raw_items.append(RawItem(
                    kind="video",
                    url=vid_url,
                    label=f"{h}p HD Video (Merge Recommended)",
                    ext="mp4",
                    width=rv.get("width"),
                    height=h,
                    has_audio=False,
                    needs_merge=True
                ))

        # Check Gallery
        elif post.get("is_gallery") and post.get("media_metadata"):
            meta = post["media_metadata"]
            for idx, (m_id, m_val) in enumerate(meta.items()):
                s = m_val.get("s", {})
                img_url = s.get("u") or s.get("gif")
                if img_url:
                    clean_img = img_url.replace("&amp;", "&")
                    raw_items.append(RawItem(
                        kind="image",
                        url=clean_img,
                        label=f"Gallery Photo {idx+1} (Full HD)",
                        ext="jpg" if "jpg" in clean_img else "png",
                        width=s.get("x"),
                        height=s.get("y")
                    ))

        # Check Single Image
        elif post.get("url_overridden_by_dest"):
            dest = post["url_overridden_by_dest"]
            if any(dest.lower().endswith(x) for x in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
                raw_items.append(RawItem(
                    kind="image",
                    url=dest,
                    label="Original Image",
                    ext="jpg" if ".jp" in dest else "png"
                ))

        if not raw_items:
            raise AppError(ErrorCode.NO_MEDIA, "This Reddit post does not contain downloadable media.")

        caption = post.get("selftext") or title
        return RawResult(
            engine_id=self.id,
            id=post_id,
            url=url,
            platform="reddit",
            title=title,
            description=caption,
            caption=caption,
            author=author,
            stats=stats if stats else None,
            context={"subreddit": f"r/{subreddit}" if subreddit else None},
            items=raw_items,
            raw_payload=post
        )

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
