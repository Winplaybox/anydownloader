import os
import httpx
from typing import AsyncIterator, Dict, Any, Optional, List

try:
    from backend.engines.base import Engine, ExtractContext, RawResult, RawItem
    from backend.utils.errors import AppError, ErrorCode
except (ModuleNotFoundError, ImportError):
    from engines.base import Engine, ExtractContext, RawResult, RawItem
    from utils.errors import AppError, ErrorCode

class RemoteWorkerEngine:
    id: str = "remote_worker"

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        worker_url = os.environ.get("WORKER_URL")
        worker_secret = os.environ.get("WORKER_SECRET", "")
        if not worker_url:
            raise AppError(ErrorCode.UPSTREAM_FAILED, "Remote worker mode not configured (WORKER_URL not set).")

        headers = {
            "Authorization": f"Bearer {worker_secret}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "content_type": ctx.content_type,
            "platform_id": ctx.platform_id
        }

        async with httpx.AsyncClient(timeout=ctx.timeout, follow_redirects=True) as client:
            try:
                resp = await client.post(f"{worker_url.rstrip('/')}/extract", json=payload, headers=headers)
                if resp.status_code != 200:
                    raise AppError(ErrorCode.UPSTREAM_FAILED, f"Remote worker returned HTTP {resp.status_code}")
                data = resp.json()
            except AppError:
                raise
            except Exception as e:
                raise AppError(ErrorCode.UPSTREAM_FAILED, f"Failed to connect to remote worker: {e}")

        raw_items = []
        for it in data.get("items", []):
            raw_items.append(RawItem(
                kind=it.get("kind", "video"),
                url=it.get("url"),
                label=it.get("label"),
                ext=it.get("ext", "mp4"),
                width=it.get("width"),
                height=it.get("height"),
                filesize=it.get("filesize"),
                fps=it.get("fps"),
                has_audio=it.get("has_audio", True),
                needs_merge=it.get("needs_merge", False)
            ))

        return RawResult(
            engine_id=self.id,
            id=data.get("id", "remote_media"),
            url=url,
            platform=ctx.platform_id or "remote",
            title=data.get("title"),
            description=data.get("description"),
            caption=data.get("caption"),
            author=data.get("author"),
            stats=data.get("stats"),
            items=raw_items,
            raw_payload=data
        )

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", item.url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk
