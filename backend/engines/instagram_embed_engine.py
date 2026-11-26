"""
Instagram without login: read the public embed page of a post/reel.

https://www.instagram.com/p/<code>/embed/captioned/ serves the media URL for most
public posts to anonymous clients (including datacenter IPs) where yt-dlp/gallery-dl
now get "No video formats found". Free, no cookies.
"""

from __future__ import annotations

import html
import json
import re
from typing import List, Optional

import httpx

try:
    from backend.engines.base import ExtractContext, RawItem, RawResult
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import ExtractContext, RawItem, RawResult
    from utils.errors import AppError, ErrorCode

_CODE_RE = re.compile(r"instagram\.com/(?:[^/]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]{5,})")
_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
       "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")


def _unescape_json_str(s: str) -> str:
    try:
        return json.loads(f'"{s}"')
    except Exception:
        return s.replace("\\/", "/").replace("\\u0026", "&")


def parse_embed_html(page: str) -> dict:
    """Pure function (unit-tested): pull video/image URLs + caption/author from embed HTML."""
    videos: List[str] = []
    images: List[str] = []
    for m in re.finditer(r'"video_url"\s*:\s*"([^"]+)"', page):
        u = _unescape_json_str(m.group(1))
        if u not in videos:
            videos.append(u)
    for m in re.finditer(r'<video[^>]+src="([^"]+)"', page):
        u = html.unescape(m.group(1))
        if u not in videos:
            videos.append(u)
    for m in re.finditer(r'"display_url"\s*:\s*"([^"]+)"', page):
        u = _unescape_json_str(m.group(1))
        if u not in images:
            images.append(u)
    if not images:
        m = re.search(r'<img[^>]+class="[^"]*EmbeddedMediaImage[^"]*"[^>]+src="([^"]+)"', page)
        if m:
            images.append(html.unescape(m.group(1)))
    caption = None
    m = re.search(r'<div class="Caption">(.*?)</div>', page, re.S)
    if m:
        caption = re.sub(r"<[^>]+>", " ", html.unescape(m.group(1)))
        caption = re.sub(r"\s+", " ", caption).strip() or None
    author = None
    m = re.search(r'class="UsernameText"[^>]*>([^<]+)<', page) or re.search(r'"owner"\s*:\s*\{[^}]*"username"\s*:\s*"([^"]+)"', page)
    if m:
        author = m.group(1).strip()
    return {"videos": videos, "images": images, "caption": caption, "author": author}


class InstagramEmbedEngine:
    id: str = "instagram_embed"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        m = _CODE_RE.search(url)
        if not m:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "Not an Instagram post/reel URL.")
        code = m.group(1)
        embed = f"https://www.instagram.com/p/{code}/embed/captioned/"
        try:
            async with httpx.AsyncClient(timeout=min(ctx.timeout, 12), follow_redirects=True,
                                         headers={"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"}) as c:
                r = await c.get(embed)
        except Exception as e:
            raise AppError(ErrorCode.UPSTREAM_FAILED, f"Instagram embed unreachable: {type(e).__name__}")
        if r.status_code == 404:
            raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or does not exist.")
        if r.status_code != 200:
            raise AppError(ErrorCode.UPSTREAM_FAILED, f"Instagram embed HTTP {r.status_code}")

        data = parse_embed_html(r.text)
        items: List[RawItem] = []
        for i, v in enumerate(data["videos"]):
            items.append(RawItem(kind="video", url=v, label="Original" if i == 0 else f"Video {i + 1}", ext="mp4"))
        if not data["videos"]:
            if ctx.content_type == "reel":
                raise AppError(
                    ErrorCode.NO_MEDIA,
                    "Instagram embed exposed no video for this reel (login or session cookies required).",
                )
            for i, im in enumerate(data["images"]):
                items.append(RawItem(kind="image", url=im, label=f"Photo {i + 1}", ext="jpg", has_audio=False))
        if not items:
            raise AppError(ErrorCode.NO_MEDIA, "Instagram embed exposed no media (private or login-only post).")

        author: Optional[dict] = None
        if data["author"]:
            author = {"username": data["author"], "displayName": data["author"],
                      "profileUrl": f"https://www.instagram.com/{data['author']}/"}
        return RawResult(
            engine_id=self.id, id=code, url=url, platform="instagram",
            title=(data["caption"] or "Instagram media")[:120], description=data["caption"],
            caption=data["caption"], author=author, items=items,
            context={"thumbnail": data["images"][0] if data["images"] else None},
        )
