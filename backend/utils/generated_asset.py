"""Safe resolver for temporary generated media files."""
from __future__ import annotations

import os
import re
import tempfile
import time
from typing import Optional

_VIDEO_NAME = re.compile(r"wpb_master_(?:story|reel)_[0-9a-f]{12,32}\.mp4\Z")
_AUDIO_NAMES = {"wpb_audio_master.mp3", "wpb_audio_master.wav"}
_RETENTION_SECONDS = 2 * 60 * 60


def resolve_generated_asset(filename: str, kind: str, now: Optional[float] = None) -> Optional[str]:
    """Resolve only known generated filenames, within temp storage and retention."""
    if not isinstance(filename, str) or filename != os.path.basename(filename):
        return None
    if kind == "video" and not _VIDEO_NAME.fullmatch(filename):
        return None
    if kind == "audio" and filename not in _AUDIO_NAMES:
        return None
    if kind not in {"video", "audio"}:
        return None

    root = os.path.realpath(tempfile.gettempdir())
    path = os.path.realpath(os.path.join(root, filename))
    try:
        if os.path.commonpath((root, path)) != root:
            return None
        if os.path.islink(os.path.join(root, filename)) or not os.path.isfile(path):
            return None
        current = time.time() if now is None else now
        modified = os.path.getmtime(path)
        if modified > current + 60 or current - modified > _RETENTION_SECONDS:
            return None
        return path
    except (OSError, ValueError):
        return None
