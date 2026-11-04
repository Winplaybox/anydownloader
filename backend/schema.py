from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Literal

ContentType = Literal['video', 'short', 'reel', 'image', 'carousel', 'slideshow', 'story', 'audio', 'text']

@dataclass
class Author:
    username: Optional[str] = None
    displayName: Optional[str] = None
    avatar: Optional[str] = None
    profileUrl: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class Music:
    title: Optional[str] = None
    author: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class Stats:
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    reposts: Optional[int] = None
    replies: Optional[int] = None
    score: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        # Principle 5: Honest metadata. Omit unavailable keys, never fake 0.
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class VideoVariant:
    label: str
    token: str
    ext: str = "mp4"
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    hasAudio: bool = True
    needsMerge: bool = False
    downloadUrl: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.downloadUrl:
            d["downloadUrl"] = f"/api/download?token={self.token}"
        return {k: v for k, v in d.items() if v is not None}

@dataclass
class AudioVariant:
    label: str
    token: str
    ext: str = "mp3"
    bitrate: Optional[int] = None
    filesize: Optional[int] = None
    downloadUrl: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.downloadUrl:
            d["downloadUrl"] = f"/api/download?token={self.token}"
        return {k: v for k, v in d.items() if v is not None}

@dataclass
class ImageVariant:
    label: str
    token: str
    ext: str = "jpg"
    width: Optional[int] = None
    height: Optional[int] = None
    url: Optional[str] = None
    downloadUrl: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.downloadUrl:
            d["downloadUrl"] = f"/api/download?token={self.token}"
        return {k: v for k, v in d.items() if v is not None}

@dataclass
class ThumbnailVariant:
    label: str
    token: str
    width: Optional[int] = None
    height: Optional[int] = None
    url: Optional[str] = None
    downloadUrl: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.downloadUrl:
            d["downloadUrl"] = f"/api/download?token={self.token}"
        return {k: v for k, v in d.items() if v is not None}

@dataclass
class SubtitleVariant:
    lang: str
    ext: str
    token: str
    downloadUrl: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.downloadUrl:
            d["downloadUrl"] = f"/api/download?token={self.token}"
        return {k: v for k, v in d.items() if v is not None}

@dataclass
class NormalizedResult:
    platform: str
    contentType: str
    id: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    author: Optional[Author] = None
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    publishedAt: Optional[str] = None
    duration: Optional[float] = None
    music: Optional[Music] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stats: Optional[Stats] = None
    videos: List[VideoVariant] = field(default_factory=list)
    audios: List[AudioVariant] = field(default_factory=list)
    images: List[ImageVariant] = field(default_factory=list)
    thumbnails: List[ThumbnailVariant] = field(default_factory=list)
    subtitles: List[SubtitleVariant] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "platform": self.platform,
            "contentType": self.contentType,
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "caption": self.caption,
            "tags": self.tags,
            "hashtags": self.hashtags,
            "publishedAt": self.publishedAt,
            "duration": self.duration,
            "videos": [v.to_dict() for v in self.videos],
            "audios": [a.to_dict() for a in self.audios],
            "images": [i.to_dict() for i in self.images],
            "thumbnails": [t.to_dict() for t in self.thumbnails],
            "subtitles": [s.to_dict() for s in self.subtitles],
            "warnings": self.warnings
        }
        if self.author:
            res["author"] = self.author.to_dict()
        if self.music:
            res["music"] = self.music.to_dict()
        if self.context:
            res["context"] = {k: v for k, v in self.context.items() if v is not None}
        if self.stats:
            res["stats"] = self.stats.to_dict()
        # Backwards compatibility for items array
        items = []
        for idx, v in enumerate(self.videos):
            items.append({
                "index": len(items) + 1,
                "kind": "video",
                "thumbnail": self.thumbnails[0].downloadUrl if self.thumbnails else None,
                "durationSec": self.duration,
                "variants": [v.to_dict()]
            })
        for idx, img in enumerate(self.images):
            items.append({
                "index": len(items) + 1,
                "kind": "image",
                "thumbnail": img.downloadUrl,
                "variants": [img.to_dict()]
            })
        res["items"] = items
        return {k: v for k, v in res.items() if v is not None}
