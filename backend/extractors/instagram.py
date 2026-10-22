import re
import html
import json
import urllib.parse
import asyncio
from typing import Dict, Any, List, Optional
import httpx
import yt_dlp

from backend.utils.errors import AppError, ErrorCode
from backend.extractors.base import (
    BaseExtractor,
    ResolveResult,
    MediaItem,
    MediaVariant,
    AuthorInfo,
)

class InstagramExtractor(BaseExtractor):
    platform: str = "instagram"

    def matches(self, url: str) -> bool:
        if not url:
            return False
        host = urllib.parse.urlparse(url).netloc.lower()
        return "instagram.com" in host or "instagr.am" in host

    async def resolve(self, url: str) -> ResolveResult:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.rstrip("/")

        # Check for profile link
        is_post = any(segment in path for segment in ("/p/", "/reel/", "/reels/", "/tv/"))
        if not is_post:
            if "/stories/" in path:
                raise AppError(
                    ErrorCode.PRIVATE_OR_RESTRICTED,
                    "Stories require an active login or are private."
                )
            raise AppError(
                ErrorCode.NO_MEDIA,
                "This post has no video or image to download. Please paste a post or reel link."
            )

        # Extract shortcode
        code_m = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', path)
        if not code_m:
            raise AppError(ErrorCode.URL_INVALID, "That doesn't look like a valid link.")

        shortcode = code_m.group(1)
        canonical_source = f"https://www.instagram.com/p/{shortcode}/"

        # Primary extraction: Googlebot request + Polaris JSON
        webpage = ""
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.get(canonical_source, headers=headers)
                if resp.status_code == 200:
                    webpage = resp.text
                elif resp.status_code == 404:
                    raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
                elif resp.status_code in (401, 403):
                    raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
            except AppError:
                raise
            except Exception:
                webpage = ""

        # Parse Polaris JSON
        items: List[MediaItem] = []
        author_info = None
        title = ""

        if webpage:
            og_descs = re.findall(r'property="og:description" content="(.*?)"', webpage)
            desc_text = html.unescape(og_descs[0]) if og_descs else ""

            uploader = ""
            author_match = re.search(r'-\s*([a-zA-Z0-9._]+)\s+on\s+[A-Za-z]+', desc_text)
            if author_match:
                uploader = author_match.group(1)

            if '"' in desc_text:
                q_m = re.search(r'"([^"]+)"', desc_text)
                if q_m:
                    title = q_m.group(1).strip()
            if not title:
                title = f"Instagram Post by @{uploader}" if uploader else f"Instagram Post {shortcode}"

            author_info = AuthorInfo(
                handle=uploader,
                name=uploader,
            )

            scripts = re.findall(r'<script[^>]*>(.*?)</script>', webpage, re.DOTALL)
            media_dict = None

            def find_media(obj):
                if isinstance(obj, dict):
                    if any(k in obj for k in ['carousel_media', 'video_versions']) and any(k in obj for k in ['id', 'pk', 'code', 'taken_at']):
                        return obj
                    for v in obj.values():
                        res = find_media(v)
                        if res:
                            return res
                elif isinstance(obj, list):
                    for it in obj:
                        res = find_media(it)
                        if res:
                            return res
                return None

            for s in scripts:
                if any(k in s for k in ['"carousel_media":', '"video_versions":', '"image_versions2":']):
                    try:
                        data = json.loads(s)
                        found = find_media(data)
                        if found:
                            media_dict = found
                            break
                    except Exception:
                        continue

            if media_dict:
                carousel_list = media_dict.get("carousel_media") or [media_dict]
                for idx, c_item in enumerate(carousel_list):
                    v_versions = c_item.get("video_versions") or []
                    i_versions = c_item.get("image_versions2", {}).get("candidates") or []

                    if v_versions:
                        v_vars: List[MediaVariant] = []
                        v_versions.sort(key=lambda x: (x.get("width") or 0) * (x.get("height") or 0), reverse=True)
                        for v_idx, v in enumerate(v_versions):
                            v_url = v.get("url")
                            if not v_url:
                                continue
                            h = v.get("height") or 720
                            q_label = f"{h}p" if h else "HD"
                            var = MediaVariant(
                                id=f"ig-{shortcode}-{idx}-v{v_idx}",
                                kind="video",
                                ext="mp4",
                                url=v_url,
                                quality=q_label,
                                width=v.get("width"),
                                height=v.get("height"),
                                hasAudio=True
                            )
                            var.finalize(f"instagram_{shortcode}")
                            v_vars.append(var)

                        if v_vars:
                            items.append(MediaItem(
                                index=len(items) + 1,
                                kind="video",
                                thumbnail=i_versions[0].get("url") if i_versions else None,
                                variants=v_vars
                            ))
                    elif i_versions:
                        i_versions.sort(key=lambda x: (x.get("width") or 0) * (x.get("height") or 0), reverse=True)
                        orig_img = i_versions[0]
                        orig_var = MediaVariant(
                            id=f"ig-{shortcode}-{idx}-orig",
                            kind="image",
                            ext="jpg",
                            url=orig_img.get("url"),
                            quality="orig",
                            width=orig_img.get("width"),
                            height=orig_img.get("height"),
                        )
                        orig_var.finalize(f"instagram_{shortcode}_img{idx+1}")
                        items.append(MediaItem(
                            index=len(items) + 1,
                            kind="image",
                            thumbnail=orig_img.get("url"),
                            variants=[orig_var]
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
                if "login" in err_str or "private" in err_str:
                    raise AppError(ErrorCode.PRIVATE_OR_RESTRICTED, "This content is private, age-restricted, or needs login.")
                if "does not exist" in err_str or "deleted" in err_str or "not found" in err_str:
                    raise AppError(ErrorCode.NOT_FOUND, "This post was deleted or doesn't exist.")
                raise AppError(ErrorCode.UPSTREAM_FAILED, "The platform didn't respond. Try again.")

            if ytdlp_info:
                title = ytdlp_info.get("title") or f"Instagram Post {shortcode}"
                uploader = ytdlp_info.get("uploader") or ytdlp_info.get("channel")
                author_info = AuthorInfo(
                    name=uploader,
                    handle=uploader,
                    avatar=ytdlp_info.get("thumbnail"),
                )

                # Check if playlist / carousel
                entries = ytdlp_info.get("entries")
                if entries:
                    for idx, entry in enumerate(entries):
                        fmts = [f for f in entry.get("formats", []) if f.get("url")]
                        fmts.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)
                        if fmts:
                            top = fmts[0]
                            is_video = top.get("vcodec") != "none"
                            var = MediaVariant(
                                id=f"ig-{shortcode}-{idx}-yt",
                                kind="video" if is_video else "image",
                                ext="mp4" if is_video else "jpg",
                                url=top.get("url"),
                                quality=f"{top.get('height')}p" if top.get("height") else "HD",
                                hasAudio=True if is_video else False
                            )
                            var.finalize(f"instagram_{shortcode}_{idx+1}")
                            items.append(MediaItem(
                                index=len(items) + 1,
                                kind="video" if is_video else "image",
                                thumbnail=entry.get("thumbnail"),
                                variants=[var]
                            ))
                else:
                    fmts = [f for f in ytdlp_info.get("formats", []) if f.get("url")]
                    fmts.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)
                    v_vars = []
                    for idx, f in enumerate(fmts):
                        if f.get("vcodec") != "none":
                            h = f.get("height") or 720
                            var = MediaVariant(
                                id=f"ig-{shortcode}-v{idx}",
                                kind="video",
                                ext="mp4",
                                url=f.get("url"),
                                quality=f"{h}p",
                                hasAudio=True
                            )
                            var.finalize(f"instagram_{shortcode}")
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
