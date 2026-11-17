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

    async def extract(self, url: str, ctx: ExtractContext) -> Optional[RawResult]:
        if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("WORKER_URL"):
            return None
        worker_url = os.environ.get("WORKER_URL", "https://worker.winplaybox.in").strip()
        worker_secret = (
            os.environ.get("WORKER_SECRET", "").strip()
            or os.environ.get("WORKER_KEY", "").strip()
            or "wpb_worker_3047a7d0cb90d81830e004fbc0e61f6428f7e3cb"
        )
        if not worker_url:
            # Gracefully skip if remote worker is not configured — do NOT crash the chain
            return None

        headers = {
            "Authorization": f"Bearer {worker_secret}",
            "X-Worker-Key": worker_secret,
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "content_type": ctx.content_type,
            "platform_id": ctx.platform_id
        }

        async with httpx.AsyncClient(timeout=min(ctx.timeout, 25.0), follow_redirects=True) as client:
            try:
                resp = await client.post(f"{worker_url.rstrip('/')}/extract", json=payload, headers=headers)
                if resp.status_code != 200:
                    return None
                data = resp.json()
            except Exception:
                return None

        if not data or not data.get("ok", True):
            return None

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

        for s in data.get("subtitles", []):
            if not any(i.kind == "subtitle" and i.url == s.get("url") for i in raw_items):
                raw_items.append(RawItem(
                    kind="subtitle",
                    url=s.get("url"),
                    label=s.get("label") or f"Subtitles ({s.get('lang', 'en').upper()})",
                    ext=s.get("ext", "srt")
                ))

        if not raw_items and not data.get("images") and not data.get("videos"):
            return None

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
