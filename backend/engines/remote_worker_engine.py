import os
import asyncio
import urllib.parse
import httpx

try:
    from backend.utils.worker_config import get_worker_config, worker_headers
    from backend.utils.security import is_safe_cdn_host, verify_safe_upstream_url, verify_public_dns_resolution
except (ModuleNotFoundError, ImportError):
    from utils.worker_config import get_worker_config, worker_headers
    from utils.security import is_safe_cdn_host, verify_safe_upstream_url, verify_public_dns_resolution
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
        worker_config = get_worker_config()
        if not worker_config:
            return None
        worker_url, worker_secret = worker_config
        headers = worker_headers(worker_secret)
        payload = {
            "url": url,
            "content_type": ctx.content_type,
            "platform_id": ctx.platform_id
        }

        async with httpx.AsyncClient(timeout=min(ctx.timeout, 25.0), follow_redirects=False) as client:
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
        if not item.url:
            raise ValueError("Remote worker returned an empty media URL.")
        current = item.url
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            response = None
            for _ in range(6):
                parsed = urllib.parse.urlsplit(current)
                if (
                    parsed.scheme != "https" or not parsed.hostname
                    or not is_safe_cdn_host(parsed.hostname)
                    or not verify_safe_upstream_url(current)
                    or not await asyncio.to_thread(verify_public_dns_resolution, current)
                ):
                    raise ValueError("Remote worker returned an unsafe media URL or redirect.")
                request = client.build_request("GET", current, headers={"User-Agent": "Mozilla/5.0"})
                response = await client.send(request, stream=True, follow_redirects=False)
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    await response.aclose()
                    response = None
                    if not location:
                        raise ValueError("Remote media redirect has no location.")
                    current = urllib.parse.urljoin(current, location)
                    continue
                break
            if response is None:
                raise ValueError("Remote media URL exceeded the redirect limit.")
            try:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    yield chunk
            finally:
                await response.aclose()
