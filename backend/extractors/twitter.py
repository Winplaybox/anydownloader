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

class TwitterExtractor(BaseExtractor):
    platform: str = "twitter"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return any(h in host for h in ("twitter.com", "x.com", "fxtwitter.com", "vxtwitter.com", "fixupx.com"))

    async def resolve(self, url: str) -> ResolveResult:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or ""

        # T21: Spaces / Lists / profile URLs -> NO_MEDIA with hint
        if any(keyword in path for keyword in ("/spaces/", "/lists/", "/i/lists/")):
            raise AppError(
                ErrorCode.NO_MEDIA,
                "This post has no video or image to download. Please paste a post link."
            )

        status_m = re.search(r'/(?:i/web/status|i/status|[\w-]+/status)/(\d+)', path)
        if not status_m:
            # Check if it is a profile link (e.g. /username)
            if re.match(r'^/[\w]{1,15}/?$', path) and not path.startswith(("/home", "/explore", "/messages")):
                raise AppError(
                    ErrorCode.NO_MEDIA,
                    "This post has no video or image to download. Please paste a post link."
                )
            raise AppError(
                ErrorCode.URL_INVALID,
                "That doesn't look like a valid link."
            )

        tweet_id = status_m.group(1)
        canonical_source = f"https://x.com/i/status/{tweet_id}"

        # 1. Primary Resolution: FxTwitter API
        api_url = f"https://api.fxtwitter.com/i/status/{tweet_id}"
        data = None

        headers = {
            "User-Agent": "TelegramBot (like TwitterBot)",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                elif resp.status_code == 404:
                    # Check if deleted or suspended
                    err_msg = resp.text.lower()
                    if "suspended" in err_msg or "deleted" in err_msg or "not found" in err_msg:
                        raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
                    raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
                elif resp.status_code in (401, 403):
                    raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
            except AppError:
                raise
            except Exception:
                data = None

        tweet = None
        if data and isinstance(data, dict):
            tweet = data.get("tweet")

        # 2. Secondary Fallback: yt-dlp
        ytdlp_info = None
        if not tweet:
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
                if "private" in err_str or "protected" in err_str or "login" in err_str:
                    raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
                raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

        if not tweet and not ytdlp_info:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

        # Build Media from FxTwitter or yt-dlp
        author_info = None
        title = ""
        caption = ""
        metrics_info = None
        items: List[MediaItem] = []

        if tweet:
            author_data = tweet.get("author") or {}
            author_info = AuthorInfo(
                name=author_data.get("name"),
                handle=author_data.get("screen_name"),
                avatar=author_data.get("avatar_url"),
            )
            title = tweet.get("text") or f"X (Twitter) Post {tweet_id}"
            caption = tweet.get("text") or title
            metrics_info = MetricsInfo(
                likes=tweet.get("likes"),
                comments=tweet.get("replies"),
                shares=tweet.get("retweets"),
                views=tweet.get("views"),
            )

            media = tweet.get("media") or {}
            videos = media.get("videos") or []
            photos = media.get("photos") or []

            # T13 / T14: If no media directly on tweet, check quote tweet or retweet
            if not videos and not photos:
                if tweet.get("quote") and tweet["quote"].get("media"):
                    quoted = tweet["quote"]
                    videos = quoted.get("media", {}).get("videos") or []
                    photos = quoted.get("media", {}).get("photos") or []
                    title = f"[Quote: @{quoted.get('author', {}).get('screen_name')}] " + title
                elif tweet.get("retweet") and tweet["retweet"].get("media"):
                    retweeted = tweet["retweet"]
                    videos = retweeted.get("media", {}).get("videos") or []
                    photos = retweeted.get("media", {}).get("photos") or []

            # T15: Text-only tweet
            if not videos and not photos:
                raise AppError(
                    ErrorCode.NO_MEDIA,
                    "This post has no video or image to download."
                )

            # Process Videos (including GIFs)
            for v_idx, v in enumerate(videos):
                is_gif = (v.get("type") == "gif")
                variants_raw = v.get("variants") or []
                mp4_vars = [
                    vr for vr in variants_raw
                    if (vr.get("content_type") == "video/mp4" or (vr.get("url") and ".mp4" in vr.get("url"))) and vr.get("url")
                ]
                mp4_vars.sort(key=lambda x: x.get("bitrate") or 0, reverse=True)

                parsed_variants: List[MediaVariant] = []
                seen_urls = set()

                for var in mp4_vars:
                    v_url = var.get("url")
                    if not v_url or v_url in seen_urls:
                        continue
                    seen_urls.add(v_url)

                    dim_m = re.search(r'/vid/(?:avc1/)?(\d+)x(\d+)/', v_url)
                    if dim_m:
                        w, h = int(dim_m.group(1)), int(dim_m.group(2))
                        res_dim = min(w, h)
                    else:
                        w, h = None, None
                        res_dim = 720

                    quality_label = "GIF" if is_gif else (f"{res_dim}p" if res_dim else "HD")
                    variant = MediaVariant(
                        id=f"tw-{tweet_id}-v{v_idx}-{res_dim}p",
                        kind="video",
                        ext="mp4",
                        url=v_url,
                        quality=quality_label,
                        width=w,
                        height=h,
                        hasAudio=False if is_gif else True
                    )
                    variant.finalize(f"twitter_{tweet_id}")
                    parsed_variants.append(variant)

                if parsed_variants:
                    items.append(MediaItem(
                        index=len(items) + 1,
                        kind="video",
                        thumbnail=v.get("thumbnail_url"),
                        durationSec=v.get("duration"),
                        variants=parsed_variants,
                    ))

            # Process Photos (T11 single image, T12 4-image tweet)
            for p_idx, p in enumerate(photos):
                p_url = p.get("url")
                if not p_url:
                    continue

                # Format original & large URLs from pbs.twimg.com
                base_img_url = p_url.split("?")[0]
                ext_match = re.search(r'\.(jpg|jpeg|png|webp)', base_img_url, re.IGNORECASE)
                ext = ext_match.group(1).lower() if ext_match else "jpg"
                if ext == "jpeg":
                    ext = "jpg"

                orig_url = f"{base_img_url}?format={ext}&name=orig"
                large_url = f"{base_img_url}?format={ext}&name=large"

                orig_var = MediaVariant(
                    id=f"tw-{tweet_id}-img{p_idx}-orig",
                    kind="image",
                    ext=ext,
                    url=orig_url,
                    quality="orig",
                    width=p.get("width"),
                    height=p.get("height"),
                )
                orig_var.finalize(f"twitter_{tweet_id}_photo{p_idx+1}")

                large_var = MediaVariant(
                    id=f"tw-{tweet_id}-img{p_idx}-large",
                    kind="image",
                    ext=ext,
                    url=large_url,
                    quality="large",
                )
                large_var.finalize(f"twitter_{tweet_id}_photo{p_idx+1}")

                items.append(MediaItem(
                    index=len(items) + 1,
                    kind="image",
                    thumbnail=large_url,
                    variants=[orig_var, large_var]
                ))

        elif ytdlp_info:
            # yt-dlp fallback parsing
            title = ytdlp_info.get("title") or f"X (Twitter) Post {tweet_id}"
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

            parsed_vars: List[MediaVariant] = []
            seen_urls = set()

            for idx, f in enumerate(fmts):
                v_url = f.get("url")
                if not v_url or v_url in seen_urls:
                    continue
                seen_urls.add(v_url)
                h = f.get("height") or 720
                variant = MediaVariant(
                    id=f"tw-{tweet_id}-yt-{idx}",
                    kind="video",
                    ext="mp4",
                    url=v_url,
                    quality=f"{h}p",
                    height=h,
                    width=f.get("width"),
                    hasAudio=True
                )
                variant.finalize(f"twitter_{tweet_id}")
                parsed_vars.append(variant)

            if parsed_vars:
                items.append(MediaItem(
                    index=1,
                    kind="video",
                    thumbnail=ytdlp_info.get("thumbnail"),
                    durationSec=ytdlp_info.get("duration"),
                    variants=parsed_vars,
                ))

        if not items:
            raise AppError(ErrorCode.NO_MEDIA, "This post has no video or image to download.")

        return ResolveResult(
            platform=self.platform,
            sourceUrl=canonical_source,
            title=title,
            caption=caption or title,
            author=author_info,
            metrics=metrics_info,
            items=items,
        )
