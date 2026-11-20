"""Renders one clip: cut + 9:16 framing + burned captions/hook + -14 LUFS audio + thumbnail + SRT."""
from __future__ import annotations

import os
import subprocess
import threading
from typing import Any, Callable, Dict, List, Optional

from . import config, media, reframe

try:
    from backend.services.video_editor import captions as _cap
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services.video_editor import captions as _cap  # type: ignore


def output_size(resolution: int) -> tuple[int, int]:
    w = 1080 if resolution >= 1080 else 720
    return w, w * 16 // 9


def _hook_lines(text: str, max_chars: int = 16) -> Dict[str, str]:
    """Long hooks overflow a 9:16 frame: split into the big red line + the second (yellow) line."""
    words = text.split()
    if len(text) <= max_chars or len(words) < 2:
        return {"title": text}
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
    return {"title": " ".join(words[:best]), "subtitle": " ".join(words[best:])}


def clip_words(words: List[Dict[str, Any]], s: float, e: float) -> List[Dict[str, Any]]:
    out = []
    for w in words:
        if w["e"] <= s or w["s"] >= e:
            continue
        out.append({"w": w["w"], "s": round(max(0.0, w["s"] - s), 3), "e": round(min(e, w["e"]) - s, 3)})
    return out


def render_clip(*, src: str, info: Dict[str, Any], clip: Dict[str, Any], words: List[Dict[str, Any]],
                settings: Dict[str, Any], lang: str, out_dir: str, index: int,
                progress: Optional[Callable[[float], None]] = None) -> Dict[str, Any]:
    s, e = float(clip["start"]), float(clip["end"])
    dur = round(e - s, 3)
    out_w, out_h = output_size(settings["resolution"])
    base = f"clip_{index:02d}"
    mp4, jpg, srt, ass = (os.path.join(out_dir, base + x) for x in (".mp4", ".jpg", ".srt", ".ass"))

    frame = reframe.decide(src, info, s, e, settings["layout"])
    cw = clip_words(words, s, e)
    font = config.FONT_BY_LANG.get((lang or "").split("-")[0], config.DEFAULT_FONT)
    hook = _hook_lines(clip["hook"]) if settings.get("hook") and clip.get("hook") else None
    doc = _cap.build_ass(words=cw, style=settings["caption_style"], width=out_w, height=out_h, font=font,
                         accent=settings["accent"], hook=hook, duration=dur, overlay_font=config.DEFAULT_FONT
                         if font == config.DEFAULT_FONT else font)
    with open(ass, "w", encoding="utf-8") as f:
        f.write(doc)

    vchain = reframe.video_filter(info, frame, out_w, out_h)
    vchain += f",ass='{media.filter_path(ass)}':fontsdir='{media.filter_path(media.FONTS_DIR)}',format=yuv420p[v]"
    graph = vchain
    cmd = [media.bin_path("ffmpeg"), "-hide_banner", "-nostats", "-y", "-ss", f"{s:.3f}", "-i", src,
           "-t", f"{dur:.3f}", "-filter_complex", graph, "-map", "[v]"]
    if info.get("has_audio"):
        cmd += ["-map", "0:a:0", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", config.X264_PRESET, "-crf", config.X264_CRF, "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-threads", config.FFMPEG_THREADS, "-movflags", "+faststart",
            "-progress", "pipe:1", mp4]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    tail: List[str] = []

    def drain() -> None:
        for line in proc.stderr:  # type: ignore[union-attr]
            tail.append(line)
            del tail[:-8]

    t = threading.Thread(target=drain, daemon=True)
    t.start()
    for line in proc.stdout:  # type: ignore[union-attr]
        if progress and line.startswith("out_time_us="):
            try:
                progress(min(1.0, int(line.split("=", 1)[1]) / 1e6 / max(0.1, dur)))
            except ValueError:
                pass
    proc.wait(timeout=1800)
    t.join(timeout=5)
    if proc.returncode != 0 or not os.path.exists(mp4) or os.path.getsize(mp4) < 1000:
        raise media.RenderError("Clip render failed: " + " | ".join(x.strip() for x in tail[-4:]))

    media.grab_frame(mp4, min(1.2, dur / 2), jpg, width=out_w // 2)
    with open(srt, "w", encoding="utf-8") as f:
        f.write(_cap.srt_from_words(cw) if cw else "")
    try:
        os.unlink(ass)
    except OSError:
        pass
    return {
        **clip, "index": index, "width": out_w, "height": out_h, "framing": frame,
        "files": {"video": base + ".mp4", "thumb": base + ".jpg" if os.path.exists(jpg) else None,
                  "srt": base + ".srt"},
        "size_bytes": os.path.getsize(mp4),
    }
