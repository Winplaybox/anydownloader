import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Literal
try:
    from backend.utils.security import sign_download_token
    from backend.utils.title import summarize_title
except (ModuleNotFoundError, ImportError):
    from utils.security import sign_download_token
    from utils.title import summarize_title

MediaKind = Literal['video', 'image']

@dataclass
class MediaVariant:
    id: str
    kind: MediaKind
    ext: str  # 'mp4' | 'webm' | 'jpg' | 'png' | 'webp' | 'gif'
    url: str  # Upstream CDN URL
    quality: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sizeBytes: Optional[int] = None
    hasAudio: Optional[bool] = None
    downloadUrl: Optional[str] = None

    def finalize(self, filename_base: str, title: Optional[str] = None):
        ext_clean = self.ext.lstrip('.')
        short_title = summarize_title(title) if title else ""
        prefix = f"{short_title}-{filename_base}" if (short_title and not filename_base.startswith(short_title)) else filename_base
        filename = f'{prefix}_{self.quality or self.id}.{ext_clean}'
        filename = re.sub(r'[\/\\:*\?"<>|]+', '_', filename)[:100]
        token = sign_download_token(self.url, filename)
        self.downloadUrl = f'/api/download?token={token}'

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop('url', None)
        return {k: v for k, v in d.items() if v is not None}

@dataclass
class MediaItem:
    index: int
    kind: MediaKind
    variants: List[MediaVariant]
    thumbnail: Optional[str] = None
    durationSec: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'kind': self.kind,
            'thumbnail': self.thumbnail,
            'durationSec': self.durationSec,
            'variants': [v.to_dict() for v in self.variants],
        }

@dataclass
class AuthorInfo:
    name: Optional[str] = None
    handle: Optional[str] = None
    avatar: Optional[str] = None
    verified: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class MetricsInfo:
    likes: Optional[Any] = None
    comments: Optional[Any] = None
    shares: Optional[Any] = None
    views: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class ResolveResult:
    platform: str
    sourceUrl: str
    items: List[MediaItem]
    title: Optional[str] = None
    caption: Optional[str] = None
    author: Optional[AuthorInfo] = None
    metrics: Optional[MetricsInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {
            'platform': self.platform,
            'sourceUrl': self.sourceUrl,
            'title': self.title,
            'items': [item.to_dict() for item in self.items],
        }
        if self.caption:
            res['caption'] = self.caption
        if self.author:
            res['author'] = self.author.to_dict()
        if self.metrics:
            res['metrics'] = self.metrics.to_dict()
        return res

class BaseExtractor(ABC):
    platform: str

    @abstractmethod
    def matches(self, url: str) -> bool:
        pass

    @abstractmethod
    async def resolve(self, url: str) -> ResolveResult:
        pass
