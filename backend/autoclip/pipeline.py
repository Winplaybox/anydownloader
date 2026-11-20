"""End-to-end job: source -> audio -> transcript -> AI picks -> rendered clips + clips.json.

Same code runs inline (API process) and on a remote worker. The caller supplies `report`,
an async callback (stage, progress, meta) -> bool; False means stop (cancelled / lease lost).
Blocking work runs in threads; a ticker forwards their progress every few seconds.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from . import __version__, brain, clipper, media, speech

log = logging.getLogger("autoclip.pipeline")

Report = Callable[[str, int, Dict[str, Any]], Awaitable[bool]]

# progress budget per stage (cumulative %)
_STAGES = {"fetching": (2, 15), "analyzing": (15, 20), "transcribing": (20, 55), "finding": (55, 62),
           "rendering": (62, 98)}


class Cancelled(Exception):
    pass


class _State:
    def __init__(self) -> None:
        self.stage, self.frac, self.meta, self.stop = "starting", 0.0, {}, False

    def pct(self) -> int:
        a, b = _STAGES.get(self.stage, (1, 2))
        return int(a + (b - a) * max(0.0, min(1.0, self.frac)))

    def set(self, stage: str, frac: float = 0.0) -> None:
        if self.stop:
            raise Cancelled()
        self.stage, self.frac = stage, frac

    def tick(self, frac: float) -> bool:
        self.frac = frac
        return not self.stop


async def run(spec: Dict[str, Any], workdir: str, report: Report, *, source_path: Optional[str] = None) -> Dict[str, Any]:
    st = spec["settings"]
    state = _State()
    os.makedirs(workdir, exist_ok=True)
    out_dir = os.path.join(workdir, "clips")
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    async def ticker() -> None:
        while True:
            await asyncio.sleep(4)
            if not await report(state.stage, state.pct(), state.meta):
                state.stop = True

    async def push(stage: str, frac: float = 0.0, **meta: Any) -> None:
        state.set(stage, frac)
        state.meta.update({k: v for k, v in meta.items() if v})
        if not await report(stage, state.pct(), state.meta):
            state.stop = True
            raise Cancelled()

    def prog(frac: float) -> None:
        if not state.tick(frac):
            raise Cancelled()

    tk = asyncio.create_task(ticker())
    try:
        # 1. source -------------------------------------------------------------
        title, uploader = spec.get("source_name") or "", ""
        if spec["source_kind"] == "url":
            await push("fetching")
            got = await asyncio.to_thread(media.fetch_url, spec["source_url"], workdir, prog)
            src, title, uploader = got["path"], got["title"] or title, got["uploader"]
        else:
            src = source_path or ""
            if not src or not os.path.exists(src):
                raise media.SourceError("Uploaded file is missing. Please upload again.")
        await push("analyzing", 0.1, title=title)
        info = await asyncio.to_thread(media.probe, src)
        dur = float(info["duration"] or 0)
        if dur <= 3:
            raise media.SourceError("Video is too short to clip.")
        if dur > media.config.MAX_SOURCE_MINUTES * 60 + 30:
            raise media.SourceError(f"Video is {dur / 60:.0f} min. The limit is {media.config.MAX_SOURCE_MINUTES} min.")
        await push("analyzing", 0.4, duration=dur)

        # 2. audio + loudness ---------------------------------------------------
        words, z, lang = [], [], st.get("language", "auto")
        if info.get("has_audio"):
            wav = os.path.join(workdir, "audio16k.wav")
            await asyncio.to_thread(media.extract_audio_16k, src, wav)
            z = media.zscores(await asyncio.to_thread(media.loudness_per_second, wav))
            # 3. transcript -------------------------------------------------------
            await push("transcribing")
            tr = await asyncio.to_thread(speech.transcribe, wav, dur, lang, prog)
            words, lang = tr["words"], tr.get("language") or lang
            _unlink(wav)

        # 4. pick moments -------------------------------------------------------
        await push("finding", 0.2)
        picks, engine = await brain.find_clips(words, z, dur, st, title=title, uploader=uploader)
        if not picks:
            raise media.SourceError("No clip-worthy moments found in this video.")
        await push("finding", 1.0)

        # 5. render -------------------------------------------------------------
        clips = []
        for i, c in enumerate(picks, 1):
            base = (i - 1) / len(picks)

            def cprog(f: float, base: float = base) -> None:
                prog(base + f / len(picks))

            await push("rendering", base, clip=f"{i}/{len(picks)}")
            clips.append(await asyncio.to_thread(
                clipper.render_clip, src=src, info=info, clip=c, words=words, settings=st, lang=lang,
                out_dir=out_dir, index=i, progress=cprog))

        result = {
            "version": __version__, "title": title, "uploader": uploader, "duration": dur, "language": lang,
            "source": {"width": info["width"], "height": info["height"], "fps": info.get("fps")},
            "engine": engine, "clips": clips, "elapsed_s": round(time.time() - t0, 1),
            "words_count": len(words),
        }
        with open(os.path.join(out_dir, "clips.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        return result
    finally:
        tk.cancel()
        for name in os.listdir(workdir):
            if name.startswith("source.part") or name.endswith((".part", ".ytdl")):
                _unlink(os.path.join(workdir, name))


def _unlink(p: str) -> None:
    try:
        os.unlink(p)
    except OSError:
        pass


def friendly(e: BaseException) -> str:
    if isinstance(e, media.SourceError):
        return str(e)
    if isinstance(e, media.RenderError):
        return "Rendering failed on our side. Please try again."
    if isinstance(e, MemoryError):
        return "Server ran out of memory for this video. Try a shorter video."
    return "Something went wrong while clipping. Please try again."


def retryable(e: BaseException) -> bool:
    return not isinstance(e, (media.SourceError, Cancelled))


def rmtree(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)
