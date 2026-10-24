import asyncio
import json
import shutil
import os
from typing import AsyncIterator, Dict, Any, Optional, List
import httpx

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode

class GalleryDlEngine:
    id: str = "gallerydl"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        gdl_bin = shutil.which("gallery-dl")
        if not gdl_bin:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "gallery-dl executable not found on system.")

        cmd = [gdl_bin, "-j", url]
        if ctx.cookies_path and os.path.exists(ctx.cookies_path):
            cmd.extend(["--cookies", ctx.cookies_path])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=ctx.timeout)
        except asyncio.TimeoutError:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "gallery-dl process timed out.")
        except Exception as e:
            raise AppError(ErrorCode.UPSTREAM_FAILED, f"gallery-dl failed to spawn: {e}")

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="ignore").lower()
            if "login" in err_msg or "authentication" in err_msg:
                raise AppError(ErrorCode.LOGIN_REQUIRED, "Content requires active authentication or cookies.")
            if "not found" in err_msg or "deleted" in err_msg or "404" in err_msg:
                raise AppError(ErrorCode.NOT_FOUND, "Media post was deleted or does not exist.")
            raise AppError(ErrorCode.UPSTREAM_FAILED, f"gallery-dl error: {err_msg[:200]}")

        raw_items: List[RawItem] = []
        author = None
        title = "Gallery Media"
        item_id = "gallery_media"

        lines = stdout.decode("utf-8", errors="ignore").strip().splitlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                item_data = json.loads(line)
                # gallery-dl JSON format: [category, url, metadata_dict] or [url, metadata_dict]
                m_url = None
                meta = {}
                if isinstance(item_data, list):
                    for el in item_data:
                        if isinstance(el, str) and el.startswith("http"):
                            m_url = el
                        elif isinstance(el, dict):
                            meta = el
                elif isinstance(item_data, dict):
                    m_url = item_data.get("url") or item_data.get("filename")
                    meta = item_data

                if m_url:
                    ext = "jpg"
                    if ".png" in m_url.lower(): ext = "png"
                    elif ".mp4" in m_url.lower(): ext = "mp4"
                    elif ".webm" in m_url.lower(): ext = "webm"

                    is_vid = ext in ("mp4", "webm")
                    raw_items.append(RawItem(
                        kind="video" if is_vid else "image",
                        url=m_url,
                        label=f"Media {idx+1} (Full Quality)",
                        ext=ext,
                        width=meta.get("width"),
                        height=meta.get("height"),
                        has_audio=is_vid
                    ))

                    if not author and meta.get("author") or meta.get("user") or meta.get("username"):
                        u = meta.get("author") or meta.get("user") or meta.get("username")
                        author = {"username": str(u), "displayName": str(u)}
                    if meta.get("description") or meta.get("title"):
                        title = meta.get("description") or meta.get("title")
                    if meta.get("id"):
                        item_id = str(meta.get("id"))
            except Exception:
                continue

        if not raw_items:
            raise AppError(ErrorCode.NO_MEDIA, "No downloadable media items found by gallery-dl.")

        return RawResult(
            engine_id=self.id,
            id=item_id,
            url=url,
            platform=ctx.platform_id or "gallery",
            title=title,
            description=title,
            caption=title,
            author=author,
            items=raw_items
        )

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
