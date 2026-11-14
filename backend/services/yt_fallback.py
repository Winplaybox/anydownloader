"""
Second YouTube engine (free): pytubefix.

Used only when yt-dlp fails with a bot-check / player-response block. pytubefix talks to
YouTube with different clients (VISION_OS, WEB with an automatically generated PO token via
Node/BotGuard, TV, MWEB), which often succeeds from datacenter IPs when yt-dlp is blocked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

try:
    from backend.utils.ytdlp_opts import ensure_node_on_path
except (ModuleNotFoundError, ImportError):
    from utils.ytdlp_opts import ensure_node_on_path  # type: ignore

CLIENTS = [c.strip() for c in os.environ.get("PYTUBEFIX_CLIENTS", "VISION_OS,WEB,TV,MWEB").split(",") if c.strip()]


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _open(url: str):
    from pytubefix import YouTube  # imported lazily (heavy)

    ensure_node_on_path()
    last: Optional[Exception] = None
    for client in CLIENTS:
        try:
            yt = YouTube(url, client=client)
            _ = yt.streams  # forces player fetch; raises if blocked
            return yt
        except Exception as e:  # try next client
            last = e
    raise RuntimeError(f"pytubefix failed for all clients: {last}")


def download_video(url: str, height: int, out_dir: str) -> str:
    """Best MP4 <= height with audio. Returns the output file path."""
    yt = _open(url)
    progressive = (yt.streams.filter(progressive=True, file_extension="mp4")
                   .order_by("resolution").desc())
    vids = [s for s in yt.streams.filter(adaptive=True, only_video=True, file_extension="mp4")
            .order_by("resolution").desc() if s.resolution and int(s.resolution[:-1]) <= height]
    audio = yt.streams.filter(only_audio=True, file_extension="mp4").order_by("abr").desc().first()

    best_prog = next((s for s in progressive if s.resolution and int(s.resolution[:-1]) <= height), None)
    best_adapt = vids[0] if vids else None
    out = os.path.join(out_dir, "media.mp4")

    if best_adapt and audio and (not best_prog or int(best_adapt.resolution[:-1]) > int(best_prog.resolution[:-1])):
        v = best_adapt.download(output_path=out_dir, filename="v.mp4")
        a = audio.download(output_path=out_dir, filename="a.m4a")
        subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", v, "-i", a, "-c:v", "copy", "-c:a", "aac",
                        "-movflags", "+faststart", out], check=True, timeout=600)
        for f in (v, a):
            try:
                os.remove(f)
            except OSError:
                pass
        return out
    stream = best_prog or progressive.first()
    if not stream:
        raise RuntimeError("No downloadable MP4 stream found")
    return stream.download(output_path=out_dir, filename="media.mp4")


def download_audio(url: str, quality: str, out_dir: str) -> str:
    yt = _open(url)
    audio = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
    if not audio:
        raise RuntimeError("No audio stream found")
    src = audio.download(output_path=out_dir, filename="a.src")
    out = os.path.join(out_dir, "media.mp3")
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", src, "-vn", "-b:a", f"{quality}k", out],
                   check=True, timeout=600)
    try:
        os.remove(src)
    except OSError:
        pass
    return out


def resolve_info(url: str) -> dict:
    """Metadata + available MP4 heights via pytubefix (used when yt-dlp is blocked on resolve)."""
    yt = _open(url)
    heights = set()
    for st in yt.streams:
        res = getattr(st, "resolution", None)
        if st.type == "video" and res and res.endswith("p") and res[:-1].isdigit():
            heights.add(int(res[:-1]))
    try:
        views = int(yt.views or 0)
    except Exception:
        views = 0
    return {
        "title": yt.title,
        "author": yt.author,
        "duration": int(yt.length or 0),
        "views": views,
        "thumbnail": yt.thumbnail_url,
        "heights": sorted(heights, reverse=True),
    }
