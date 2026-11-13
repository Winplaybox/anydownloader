import logging
from typing import Dict, Any, Optional, List
from backend.engines.base import Engine, ExtractContext, RawResult
from backend.engines.ytdlp_engine import YtDlpEngine
from backend.engines.tikwm_engine import TikWmEngine
from backend.engines.fxtwitter_engine import FxTwitterEngine
from backend.engines.gallerydl_engine import GalleryDlEngine
from backend.engines.reddit_engine import RedditEngine
from backend.engines.remote_worker_engine import RemoteWorkerEngine
from backend.engines.instagram_embed_engine import InstagramEmbedEngine
from backend.utils.errors import AppError, ErrorCode

logger = logging.getLogger("ovd.engines")

class EngineRegistry:
    def __init__(self):
        self.engines: Dict[str, Engine] = {
            "ytdlp": YtDlpEngine(),
            "tikwm": TikWmEngine(),
            "fxtwitter": FxTwitterEngine(),
            "gallerydl": GalleryDlEngine(),
            "reddit_json": RedditEngine(),
            "remote_worker": RemoteWorkerEngine(),
            "instagram_embed": InstagramEmbedEngine(),
        }

    def get(self, engine_id: str) -> Optional[Engine]:
        return self.engines.get(engine_id)

    def register(self, engine: Engine):
        self.engines[engine.id] = engine

    async def execute_chain(
        self,
        url: str,
        routes: Dict[str, List[str]],
        content_type: str,
        ctx: ExtractContext
    ) -> RawResult:
        engine_ids = routes.get(content_type) or routes.get("video") or ["ytdlp"]
        last_error = None

        for eid in engine_ids:
            engine = self.get(eid)
            if not engine:
                continue

            try:
                logger.info(f"Trying engine '{eid}' for {url} ({content_type})")
                raw = await engine.extract(url, ctx)
                if raw and raw.items:
                    return raw
            except AppError as ae:
                logger.warning(f"Engine '{eid}' AppError: {ae.code} - {ae.message}")
                last_error = ae
                # If content is private or login required, don't keep banging other engines pointlessly
                if ae.code in (ErrorCode.PRIVATE_OR_RESTRICTED, ErrorCode.NOT_FOUND):
                    raise ae
            except Exception as e:
                logger.warning(f"Engine '{eid}' unexpected exception: {e}")
                last_error = AppError(ErrorCode.UPSTREAM_FAILED, f"Engine {eid} failed: {e}")

        if last_error:
            raise last_error
        raise AppError(ErrorCode.UPSTREAM_FAILED, "All extraction engines failed to resolve media.")

engine_registry = EngineRegistry()
