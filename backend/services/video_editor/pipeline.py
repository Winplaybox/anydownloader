"""AI Video Editor job pipeline.

upload -> probe -> frames + transcript -> LLM script -> TTS voiceover -> word-timed
captions -> ffmpeg render (+ -14 LUFS master) -> metadata (titles, description, tags).

Job state lives in <WORK_DIR>/<job_id>/job.json so any uvicorn worker can answer
status polls; the job itself runs in the worker that accepted the upload. Heavy
work runs one job at a time (EDITOR_CONCURRENCY) to keep small servers alive.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

import numpy as np

from . import captions as cap
from . import planner, render, transcribe, tts
from .options import LANG_BY_ID

log = logging.getLogger("video_editor")

WORK_DIR = os.environ.get("EDITOR_WORK_DIR") or os.path.join(tempfile.gettempdir(), "wpb_editor_jobs")
RETENTION_S = float(os.environ.get("EDITOR_RETENTION_HOURS", "6")) * 3600
CONCURRENCY = max(1, int(os.environ.get("EDITOR_CONCURRENCY", "1")))
MAX_DURATION = float(os.environ.get("EDITOR_MAX_SECONDS", "180"))
TRANSCRIBE_FOR_AI = os.environ.get("EDITOR_TRANSCRIBE_FOR_AI", "1") == "1"

_sem: Optional[asyncio.Semaphore] = None
_cleaner_started = False

STAGES = [
    ("queued", "Waiting in queue"),
    ("analyzing", "Watching your video"),
    ("transcribing", "Listening to the audio"),
    ("scripting", "Writing the script"),
    ("voiceover", "Recording the voiceover"),
    ("captions", "Timing the captions"),
    ("rendering", "Rendering the video"),
    ("metadata", "Writing title, description & tags"),
    ("done", "Done"),
]


class JobError(Exception):
    """User-facing failure (message is safe to show)."""


# --------------------------------------------------------------------------- #
# Job state on disk
# --------------------------------------------------------------------------- #
def job_dir(job_id: str) -> str:
    return os.path.join(WORK_DIR, job_id)


def _valid_id(job_id: str) -> bool:
    try:
        return uuid.UUID(job_id).hex == job_id.replace("-", "")
    except (ValueError, AttributeError):
        return False


def load_job(job_id: str) -> Optional[Dict[str, Any]]:
    if not _valid_id(job_id):
        return None
    p = os.path.join(job_dir(job_id), "job.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_job(job: Dict[str, Any]) -> None:
    d = job_dir(job["id"])
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, f".job.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False)
    os.replace(tmp, os.path.join(d, "job.json"))


def _update(job: Dict[str, Any], **kw: Any) -> None:
    job.update(kw)
    job["updated_at"] = time.time()
    save_job(job)


def public_job(job: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("id", "status", "stage", "stage_label", "progress", "error", "created_at", "updated_at",
            "settings", "result", "queue_position", "warnings")
    out = {k: job.get(k) for k in keys}
    if job.get("status") == "queued":
        out["queue_position"] = queue_position(job)
    return out


def queue_position(job: Dict[str, Any]) -> int:
    n = 0
    try:
        for name in os.listdir(WORK_DIR):
            other = load_job(name)
            if other and other["id"] != job["id"] and other.get("status") in ("queued", "running") \
                    and other.get("created_at", 0) <= job.get("created_at", 0):
                n += 1
    except OSError:
        pass
    return n


def new_job(settings: Dict[str, Any], client_key: str) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    now = time.time()
    job = {"id": job_id, "status": "queued", "stage": "queued", "stage_label": "Waiting in queue", "progress": 0,
           "error": None, "created_at": now, "updated_at": now, "settings": settings, "client": client_key,
           "result": None, "warnings": []}
    os.makedirs(job_dir(job_id), exist_ok=True)
    save_job(job)
    return job


def file_path(job_id: str, kind: str) -> Optional[str]:
    names = {"video": "final.mp4", "srt": "captions.srt", "voiceover": "voiceover.wav", "metadata": "metadata.txt"}
    if kind not in names or not _valid_id(job_id):
        return None
    p = os.path.join(job_dir(job_id), names[kind])
    return p if os.path.exists(p) else None


# --------------------------------------------------------------------------- #
# Voiceover assembly
# --------------------------------------------------------------------------- #
def _place(segs: List[np.ndarray], starts: List[float], gap: float, pack: bool) -> List[Dict[str, float]]:
    placed, cursor = [], 0.0
    for i, (s, st) in enumerate(zip(segs, starts)):
        d = s.size / tts.SR
        t0 = (cursor + gap if i else st) if pack else max(st, cursor + gap if i else st)
        placed.append({"start": round(t0, 3), "end": round(t0 + d, 3)})
        cursor = t0 + d
    return placed


async def build_voiceover(lines: List[Dict[str, Any]], voice: str, lang: str, duration: float,
                          out_wav: str) -> Dict[str, Any]:
    limit = duration - 0.5
    speed = 1.05
    engines = set()

    async def synth(sp: float) -> List[np.ndarray]:
        out = []
        for ln in lines:
            s, eng = await tts.speak(ln["tts"], voice, lang, sp)
            engines.add(eng)
            out.append(s)
        return out

    segs = await synth(speed)
    keep = list(range(len(lines)))
    starts = [ln["start"] for ln in lines]
    placed = _place(segs, starts, 0.25, pack=False)
    if placed and placed[-1]["end"] > limit:
        placed = _place(segs, starts, 0.18, pack=True)
    if placed and placed[-1]["end"] > limit:
        spoken = sum(s.size for s in segs) / tts.SR
        room = max(1.0, limit - starts[0] - 0.18 * (len(segs) - 1))
        new_speed = min(1.3, speed * spoken / room * 1.02)
        if new_speed > speed + 0.02:
            speed = new_speed
            segs = await synth(speed)
            placed = _place(segs, starts, 0.18, pack=True)
    # still too long: drop lines before the final CTA until it fits
    while placed and placed[-1]["end"] > limit and len(keep) > 1:
        drop = len(keep) - 2 if len(keep) > 2 else len(keep) - 1
        keep.pop(drop)
        segs.pop(drop)
        starts.pop(drop)
        placed = _place(segs, starts, 0.18, pack=True)
    if placed and placed[-1]["end"] > duration:
        raise JobError("The voiceover is longer than the video. Try a shorter script.")

    track = np.zeros(int((duration + 0.1) * tts.SR), dtype=np.float32)
    for s, p in zip(segs, placed):
        i0 = int(p["start"] * tts.SR)
        seg = s[: max(0, track.size - i0)]
        track[i0:i0 + seg.size] += seg
    peak = float(np.abs(track).max() or 1.0)
    if peak > 0.98:
        track *= 0.98 / peak
    import soundfile as sf

    sf.write(out_wav, track, tts.SR)
    out_lines = []
    for idx, p in zip(keep, placed):
        out_lines.append({**lines[idx], "start": p["start"], "end": p["end"]})
    return {"lines": out_lines, "speed": round(speed, 2), "engines": sorted(engines),
            "dropped": len(lines) - len(keep)}


async def _romanize(words: List[Dict[str, Any]], lang: str) -> Optional[List[str]]:
    toks = [w["w"] for w in words][:900]
    if not toks:
        return None
    li = LANG_BY_ID.get(lang, {"name": lang})
    try:
        obj, _ = await planner.llm_router.complete_json(
            "You transliterate text into Roman letters the way Indians type on social media. JSON only.",
            f"Transliterate each {li['name']} token into Roman (Hinglish style). Keep EXACTLY the same number of "
            f"tokens and order; keep punctuation attached. Return {{\"tokens\": [...]}}.\n" + json.dumps(toks, ensure_ascii=False),
            temperature=0.1, max_tokens=4000, budget_s=60)
        out = [str(t) for t in obj.get("tokens") or []]
        return out if len(out) == len(toks) else None
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# The job
# --------------------------------------------------------------------------- #
def _ensure_cleaner() -> None:
    global _cleaner_started
    if _cleaner_started:
        return
    _cleaner_started = True

    async def loop() -> None:
        while True:
            try:
                now = time.time()
                for name in os.listdir(WORK_DIR):
                    j = load_job(name)
                    d = job_dir(name)
                    age_ref = (j or {}).get("updated_at") or os.path.getmtime(d)
                    if now - age_ref > RETENTION_S:
                        shutil.rmtree(d, ignore_errors=True)
            except OSError:
                pass
            await asyncio.sleep(900)

    asyncio.get_running_loop().create_task(loop())


def start(job: Dict[str, Any], src_path: str,
          on_finish: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None) -> None:
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(CONCURRENCY)
    _ensure_cleaner()
    asyncio.get_running_loop().create_task(_run(job, src_path, on_finish))


async def _run(job: Dict[str, Any], src_path: str,
               on_finish: Optional[Callable[[Dict[str, Any]], Awaitable[None]]]) -> None:
    assert _sem is not None
    async with _sem:
        _update(job, status="running")
        try:
            await _process(job, src_path)
            _update(job, status="done", stage="done", stage_label="Done", progress=100)
        except JobError as e:
            _update(job, status="failed", error=str(e))
        except (render.RenderError, planner.PlanError, tts.TTSError) as e:
            log.warning("editor job %s failed: %s", job["id"], e)
            _update(job, status="failed", error=str(e)[:300])
        except Exception as e:  # pragma: no cover - unexpected
            log.exception("editor job %s crashed", job["id"])
            _update(job, status="failed", error=f"Unexpected server error ({type(e).__name__}). Please try again.")
        finally:
            try:
                os.remove(src_path)
            except OSError:
                pass
            if on_finish:
                try:
                    await on_finish(job)
                except Exception:  # pragma: no cover
                    log.exception("on_finish hook failed")


def _stage(job: Dict[str, Any], stage: str, progress: int) -> None:
    label = dict(STAGES).get(stage, stage)
    _update(job, stage=stage, stage_label=label, progress=progress)


async def _process(job: Dict[str, Any], src_path: str) -> None:
    s = job["settings"]
    d = job_dir(job["id"])
    lang, mode, style = s["language"], s["mode"], s["caption_style"]

    # 1. analyse ---------------------------------------------------------------
    _stage(job, "analyzing", 5)
    info = await asyncio.to_thread(render.probe, src_path)
    if info["duration"] <= 0.5:
        raise JobError("The video is too short or unreadable.")
    if info["duration"] > MAX_DURATION + 0.5:
        raise JobError(f"Video is {info['duration']:.0f}s long; the limit is {MAX_DURATION:.0f}s.")
    duration = info["duration"]
    frames = await asyncio.to_thread(render.extract_frames, src_path, os.path.join(d, "frames"), duration, 8)
    _update(job, source=info)

    # 2. transcript --------------------------------------------------------------
    words_orig: List[Dict[str, Any]] = []
    transcript = ""
    if info["has_audio"] and (mode == "original" or TRANSCRIBE_FOR_AI):
        _stage(job, "transcribing", 12)
        if mode == "original" and not transcribe.available():
            raise JobError("Speech recognition is not installed on this server; choose an AI voiceover mode.")
        wav16 = await asyncio.to_thread(render.extract_audio_16k, src_path, os.path.join(d, "audio16k.wav"))
        tr = await asyncio.to_thread(transcribe.transcribe, wav16, lang)
        transcript, words_orig = tr["text"], tr["words"]
    if mode == "original" and style != "none" and not words_orig:
        raise JobError("No clear speech found in the video to caption. Try an AI voiceover mode instead.")

    # 3. script -------------------------------------------------------------------
    _stage(job, "scripting", 22)
    plan = await planner.plan_script(frames=[b for _, b in frames], frame_times=[t for t, _ in frames],
                                     brief=s.get("brief", ""), channel=s.get("channel", ""), lang=lang,
                                     caption_script=s["caption_script"], duration=duration, transcript=transcript,
                                     mode=mode, user_script=s.get("script", ""))
    hook = plan["hook"] if s.get("overlays", True) else None
    end_card = plan["end_card"] if s.get("overlays", True) else None

    # 4. voiceover ------------------------------------------------------------------
    vo_path = None
    spoken_lines: List[Dict[str, Any]] = []
    vo_meta: Dict[str, Any] = {}
    if mode in ("ai_mix", "ai_replace"):
        _stage(job, "voiceover", 35)
        vo_path = os.path.join(d, "voiceover.wav")
        vo_meta = await build_voiceover(plan["lines"], s["voice"], lang, duration, vo_path)
        spoken_lines = vo_meta["lines"]
        if vo_meta.get("dropped"):
            job["warnings"].append(f"{vo_meta['dropped']} script line(s) were dropped to fit the video length.")

    # 5. captions -------------------------------------------------------------------
    _stage(job, "captions", 55)
    if mode == "original":
        words = words_orig
        if s["caption_script"] == "roman" and LANG_BY_ID.get(lang, {}).get("indic"):
            rom = await _romanize(words, lang)
            if rom:
                words = [{**w, "w": r} for w, r in zip(words, rom)]
            else:
                job["warnings"].append("Captions are in native script (Roman conversion was unavailable).")
    else:
        words = cap.words_from_lines(spoken_lines)
    out_w, out_h = render.output_size(info["width"], info["height"], s["format"])
    font = LANG_BY_ID.get(lang, {}).get("font", "Inter Black")
    if s["caption_script"] == "roman":
        font = "Inter Black"
    ass_text = cap.build_ass(words=words, style=style, width=out_w, height=out_h, font=font, accent=s["accent"],
                             hook=hook, end_card=end_card, duration=duration, overlay_font=font)
    ass_path = os.path.join(d, "captions.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_text)
    if words:
        with open(os.path.join(d, "captions.srt"), "w", encoding="utf-8") as f:
            f.write(cap.srt_from_words(words))

    # 6. render ---------------------------------------------------------------------
    _stage(job, "rendering", 60)
    last = [0.0]

    def prog(p: float) -> None:
        if p - last[0] >= 0.04:
            last[0] = p
            _update(job, progress=60 + int(p * 30))

    out_path = os.path.join(d, "final.mp4")
    rinfo = await asyncio.to_thread(render.render, src_path=src_path, src=info, out_path=out_path, ass_path=ass_path,
                                    vo_path=vo_path, mode=mode, fmt=s["format"], duration=duration, progress=prog)
    loud = await asyncio.to_thread(render.measure_loudness, out_path)

    # 7. metadata -------------------------------------------------------------------
    _stage(job, "metadata", 92)
    script_text = " ".join(l["caption"] for l in spoken_lines) if spoken_lines else transcript
    meta = await planner.plan_metadata(brief=s.get("brief", ""), channel=s.get("channel", ""), lang=lang,
                                       summary=plan.get("summary", ""), script_text=script_text, duration=duration)
    if not meta:
        job["warnings"].append("Title/description service was busy; you can still download the video.")
    else:
        with open(os.path.join(d, "metadata.txt"), "w", encoding="utf-8") as f:
            f.write(_metadata_txt(meta))

    _update(job, result={
        "duration": duration,
        "width": rinfo["width"], "height": rinfo["height"],
        "loudness": loud,
        "summary": plan.get("summary"),
        "mood": plan.get("mood"),
        "hook": hook, "end_card": end_card,
        "script": [{"start": l["start"], "end": l["end"], "text": l["caption"]} for l in spoken_lines],
        "voice": {"id": s.get("voice"), "speed": vo_meta.get("speed"), "engines": vo_meta.get("engines")} if vo_path else None,
        "metadata": meta,
        "files": {k: bool(file_path(job["id"], k)) for k in ("video", "srt", "voiceover", "metadata")},
        "llm": plan.get("llm"),
    })


def _metadata_txt(meta: Dict[str, Any]) -> str:
    parts = ["TITLE OPTIONS"] + [f"{i}. {t}" for i, t in enumerate(meta.get("titles") or [], 1)]
    parts += ["", "DESCRIPTION", meta.get("description") or "", "", "TAGS", meta.get("tags") or "", "",
              "HASHTAGS", " ".join(meta.get("hashtags") or [])]
    for x in meta.get("extras") or []:
        parts += ["", x["heading"].upper(), x["content"]]
    return "\n".join(parts) + "\n"
