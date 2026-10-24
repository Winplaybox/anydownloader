import re
from typing import Optional, Dict, Any, List
from backend.schema import (
    NormalizedResult,
    Author,
    Music,
    Stats,
    VideoVariant,
    AudioVariant,
    ImageVariant,
    ThumbnailVariant,
    SubtitleVariant,
)
from backend.engines.base import RawResult, RawItem
from backend.utils.security import sign_download_token

def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
    return clean[:80]

def normalize_raw_result(raw: RawResult, platform_def: Dict[str, Any], content_type: str) -> NormalizedResult:
    base_name = sanitize_filename(f"{raw.platform}_{raw.id}")

    videos: List[VideoVariant] = []
    audios: List[AudioVariant] = []
    images: List[ImageVariant] = []
    thumbnails: List[ThumbnailVariant] = []
    subtitles: List[SubtitleVariant] = []

    for idx, it in enumerate(raw.items):
        ext_clean = (it.ext or "mp4").lstrip(".")
        label_clean = sanitize_filename(it.label or f"item_{idx+1}")
        filename = f"{base_name}_{label_clean}.{ext_clean}"
        token = sign_download_token(it.url, filename)

        if it.kind == "video":
            videos.append(VideoVariant(
                label=it.label or f"{it.height or 'HD'}p Video",
                token=token,
                ext=ext_clean,
                width=it.width,
                height=it.height,
                fps=it.fps,
                vcodec=it.vcodec,
                acodec=it.acodec,
                filesize=it.filesize,
                hasAudio=it.has_audio,
                needsMerge=it.needs_merge,
            ))

        elif it.kind == "audio":
            audios.append(AudioVariant(
                label=it.label or "Audio Track (MP3)",
                token=token,
                ext=ext_clean,
                filesize=it.filesize,
            ))

        elif it.kind == "image":
            images.append(ImageVariant(
                label=it.label or f"Photo {idx+1}",
                token=token,
                ext=ext_clean,
                width=it.width,
                height=it.height,
            ))

        elif it.kind == "thumbnail":
            thumbnails.append(ThumbnailVariant(
                label=it.label or f"Thumbnail {idx+1}",
                token=token,
                width=it.width,
                height=it.height,
            ))

        elif it.kind == "subtitle":
            subtitles.append(SubtitleVariant(
                lang=it.label or "en",
                ext=ext_clean,
                token=token,
            ))

    author = None
    if raw.author:
        author = Author(
            username=raw.author.get("username"),
            displayName=raw.author.get("displayName") or raw.author.get("name"),
            avatar=raw.author.get("avatar"),
            profileUrl=raw.author.get("profileUrl")
        )

    stats = None
    if raw.stats:
        stats = Stats(
            views=raw.stats.get("views"),
            likes=raw.stats.get("likes"),
            comments=raw.stats.get("comments"),
            shares=raw.stats.get("shares"),
            saves=raw.stats.get("saves"),
            reposts=raw.stats.get("reposts"),
            replies=raw.stats.get("replies"),
            score=raw.stats.get("score"),
        )

    music = None
    if raw.music and (raw.music.get("title") or raw.music.get("author")):
        music = Music(
            title=raw.music.get("title"),
            author=raw.music.get("author")
        )

    # Extract hashtags from title / caption
    hashtags = []
    full_text = f"{raw.title or ''} {raw.caption or ''}"
    ht_matches = re.findall(r'#(\w+)', full_text)
    if ht_matches:
        hashtags = list(dict.fromkeys(ht_matches))[:10]

    return NormalizedResult(
        platform=raw.platform,
        contentType=content_type or "video",
        id=raw.id,
        url=raw.url,
        title=raw.title,
        description=raw.description,
        caption=raw.caption,
        author=author,
        tags=raw.tags,
        hashtags=hashtags,
        publishedAt=raw.published_at,
        duration=raw.duration,
        music=music,
        context=raw.context,
        stats=stats,
        videos=videos,
        audios=audios,
        images=images,
        thumbnails=thumbnails,
        subtitles=subtitles,
        warnings=[]
    )
