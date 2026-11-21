import asyncio
import os
import re
import urllib.parse
from typing import AsyncIterator, Dict, Any, Optional, List
import yt_dlp
import httpx

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
    from backend.utils.ytdlp_opts import is_youtube_block, robust_opts
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode
    from utils.ytdlp_opts import is_youtube_block, robust_opts

class YtDlpEngine:
    id: str = "ytdlp"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        loop = asyncio.get_running_loop()

        def _run_ytdlp():
            # Same Deno / multi-client / cookies / proxy setup as downloads (utils/ytdlp_opts.py)
            ydl_opts = robust_opts("extract", socket_timeout=min(ctx.timeout, 12),
                                   cookies_path=ctx.cookies_path, proxy=ctx.proxy)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await loop.run_in_executor(None, _run_ytdlp)
        except Exception as e:
            err_str = str(e).lower()
            # Bot-check / IP block must be checked BEFORE "sign in" (it is not a private video)
            if is_youtube_block(err_str):
                raise AppError(ErrorCode.SOURCE_BLOCKED, "YouTube is temporarily blocking our server for this video. Please retry in a few minutes.")
            if any(k in err_str for k in ("private", "login", "sign in", "certain audiences", "isn't available to everyone", "age-restricted", "confirm your age")):
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
        is_yt = (ctx.platform_id == "youtube")
        if is_yt:
            raw_items.extend(self._youtube_items(info, url, title))
        for f in formats:
            if is_yt:
                break  # YouTube video/audio are served by /api/download_video|audio (see _youtube_items)
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

        # Subtitles (Creator + Auto)
        raw_subs = info.get("subtitles") or {}
        auto_subs = info.get("automatic_captions") or {}
        seen_langs = set()
        for lang, tracks in list(raw_subs.items()):
            for tr in tracks:
                if tr.get("url") and tr.get("ext") in ("vtt", "srt"):
                    raw_items.append(RawItem(
                        kind="subtitle",
                        url=tr.get("url"),
                        label=f"Subtitles ({lang.upper()})",
                        ext=tr.get("ext", "srt")
                    ))
                    seen_langs.add(lang)
                    break
            if len(seen_langs) >= 6:
                break

        if len(seen_langs) < 4:
            for lang in ("en", "hi", "es", "fr", "de"):
                if lang in auto_subs and lang not in seen_langs:
                    for tr in auto_subs[lang]:
                        if tr.get("url") and tr.get("ext") in ("vtt", "srt"):
                            raw_items.append(RawItem(
                                kind="subtitle",
                                url=tr.get("url"),
                                label=f"Auto Captions ({lang.upper()})",
                                ext=tr.get("ext", "srt")
                            ))
                            seen_langs.add(lang)
                            break

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

    @staticmethod
    def _youtube_items(info: Dict[str, Any], url: str, title: str) -> List[RawItem]:
        """YouTube variants point at the server-side merge endpoints, never at raw stream URLs.

        Raw yt-dlp URLs are IP-bound to the extraction IP, may be HLS (m3u8) manifests (a text
        playlist saved as ".mp4") and DASH video-only. /api/download_video merges video+audio
        with ffmpeg and /api/download_audio returns a real MP3, both proxy-aware.
        """
        vid = str(info.get("id") or "")
        watch = f"https://www.youtube.com/watch?v={vid}" if vid else url
        src_q = urllib.parse.quote(watch, safe="")
        title_q = urllib.parse.quote(re.sub(r'[\\/*?:"<>|]', "", title or "").strip() or "video")
        heights = sorted({
            min(int(f["height"]), 1080)
            for f in info.get("formats", [])
            if f.get("vcodec") not in (None, "none") and f.get("height") and int(f["height"]) >= 144
        }, reverse=True) or [1080, 720, 480, 360]
        items: List[RawItem] = []
        for h in heights:
            items.append(RawItem(
                kind="video", url=f"/api/download_video?url={src_q}&height={h}&title={title_q}",
                label=f"{h}p", ext="mp4", height=h, vcodec="avc1", acodec="mp4a",
                has_audio=True, needs_merge=False,
            ))
        for kbps in (320, 192, 128):
            items.append(RawItem(
                kind="audio", url=f"/api/download_audio?url={src_q}&quality={kbps}&title={title_q}",
                label=f"{kbps}kbps Audio (MP3)", ext="mp3",
            ))
        return items

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        headers = item.headers or {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
