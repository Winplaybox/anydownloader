from dataclasses import dataclass, field
from typing import Protocol, AsyncIterator, Dict, Any, Optional, List

@dataclass
class ExtractContext:
    url: str
    content_type: str = "video"
    platform_id: Optional[str] = None
    cookies_path: Optional[str] = None
    proxy: Optional[str] = None
    timeout: float = 20.0
    attribution: Optional[Dict[str, Any]] = None

@dataclass
class RawItem:
    kind: str  # video | image | audio | subtitle
    url: str
    label: Optional[str] = None
    ext: str = "mp4"
    width: Optional[int] = None
    height: Optional[int] = None
    filesize: Optional[int] = None
    fps: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    has_audio: bool = True
    needs_merge: bool = False
    headers: Optional[Dict[str, str]] = None

@dataclass
class RawResult:
    engine_id: str
    id: str
    url: str
    platform: str
    title: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    author: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None
    published_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    music: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    items: List[RawItem] = field(default_factory=list)
    raw_payload: Optional[Dict[str, Any]] = None

class Engine(Protocol):
    id: str

    async def extract(self, url: str, ctx: ExtractContext) -> RawResult:
        ...

    async def open_stream(self, item: RawItem, ctx: ExtractContext) -> AsyncIterator[bytes]:
        ...
