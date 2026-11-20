"""Picks the moments worth clipping.

1. Words -> sentence lines with [seconds] stamps; loud seconds marked (LOUD).
2. Long videos are read in overlapping windows (AUTOCLIP_WINDOW_SECONDS) so one prompt never overflows.
3. Gemini (shared GEMINI_API_KEY via llm_router, other providers as fallback) returns JSON clips.
4. Every clip is validated, snapped to word/sentence boundaries, de-duplicated and ranked.
5. No AI configured / AI failed -> deterministic fallback from loudness + speech density.
"""
from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from . import config

try:
    from backend.services.llm_router import llm_router, LLMError
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services.llm_router import llm_router, LLMError  # type: ignore

log = logging.getLogger("autoclip.brain")

_END = (".", "!", "?", "।", "॥", "؟")

SYSTEM = (
    "You are a senior short-form video editor who finds viral moments in long videos for YouTube Shorts, "
    "Instagram Reels and TikTok. You only return strict JSON. You never invent things that are not in the transcript."
)

PROMPT = """Below is a timestamped transcript of part of a video. Each line starts with [seconds].
Lines marked (LOUD) are where the audio got much louder than usual (laughing, shouting, sudden action).

Video title: {title}
Channel: {uploader}
Part: {part}
{focus}
Pick up to {n} moments that work as STANDALONE vertical clips for a stranger scrolling the feed:
a strong opinion, a surprising fact, a funny moment, an emotional peak, a story with a payoff, a clear tip,
a controversial take, a big reaction.

Rules:
- Each clip is {min_len} to {max_len} seconds. Use the [seconds] values for start and end.
- Start where the thought starts (not mid-sentence). The first 2 seconds must already be interesting.
- End right after the payoff, on the last word of a complete sentence.
- Skip intros, sponsor reads, "like and subscribe", greetings and dead air.
- Fewer strong clips beat many weak ones. Return an empty list if nothing is worth clipping.
- score: 0-100, honest chance a stranger watches to the end. Most real clips are 55-85.
- hook: max 6 words, shown as big text in the first 3 seconds. Curiosity, but true to the clip.
- title: max 70 characters, for YouTube Shorts. No clickbait lies.
- description: 1-2 sentences.
- hashtags: 3-6 relevant tags without the # sign.
- Write hook/title/description in the SAME language and script the speaker uses (Hinglish stays Hinglish in Latin letters).

Return JSON only:
{{"clips":[{{"start":0,"end":0,"score":0,"hook":"","title":"","description":"","hashtags":[],"reason":""}}]}}

Transcript:
{transcript}"""


# --------------------------------------------------------------------------- #
# Transcript shaping
# --------------------------------------------------------------------------- #

def make_lines(words: List[Dict[str, Any]], z: List[float]) -> List[Dict[str, Any]]:
    """Group words into readable sentence-ish lines."""
    lines: List[Dict[str, Any]] = []
    cur: List[Dict[str, Any]] = []

    def flush() -> None:
        if not cur:
            return
        s, e = cur[0]["s"], cur[-1]["e"]
        peak = max((z[i] for i in range(int(s), min(len(z), int(e) + 1))), default=0.0) if z else 0.0
        lines.append({"s": s, "e": e, "text": " ".join(w["w"] for w in cur), "loud": peak >= 1.6})
        cur.clear()

    for i, w in enumerate(words):
        if cur and (w["s"] - cur[-1]["e"] > 0.9 or len(cur) >= 22):
            flush()
        cur.append(w)
        if w["w"].endswith(_END) and len(cur) >= 4:
            flush()
    flush()
    return lines


def _fmt(lines: List[Dict[str, Any]]) -> str:
    return "\n".join(f"[{ln['s']:.1f}] {ln['text']}{' (LOUD)' if ln['loud'] else ''}" for ln in lines)


def windows(lines: List[Dict[str, Any]], duration: float) -> List[Tuple[float, float, List[Dict[str, Any]]]]:
    size, overlap = float(config.WINDOW_SECONDS), 60.0
    if duration <= size * 1.2:
        return [(0.0, duration, lines)]
    out, t = [], 0.0
    while t < duration:
        a, b = t, min(duration, t + size)
        out.append((a, b, [ln for ln in lines if ln["s"] >= a and ln["s"] < b]))
        if b >= duration:
            break
        t = b - overlap
    return out


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #

def _num(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _txt(v: Any, limit: int) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()[:limit]


def _tags(v: Any) -> List[str]:
    items = v if isinstance(v, list) else re.split(r"[,\s]+", str(v or ""))
    out: List[str] = []
    for t in items:
        t = re.sub(r"[^\w]", "", str(t).lstrip("#"), flags=re.UNICODE)[:30]
        if t and t.lower() not in {x.lower() for x in out}:
            out.append(t)
    return out[:6]


def snap(start: float, end: float, words: List[Dict[str, Any]], min_len: float, max_len: float,
         duration: float) -> Optional[Tuple[float, float]]:
    """Move edges onto word boundaries; prefer ending on a sentence end. None if it can't be made valid."""
    start, end = max(0.0, start), min(duration, end)
    if end - start < min_len * 0.6:
        end = min(duration, start + min_len)
    if not words:
        s, e = start, min(end, start + max_len)
        return (round(s, 2), round(e, 2)) if e - s >= min(min_len, duration) * 0.6 else None
    # start: first word starting at/after start-0.5
    si = next((i for i, w in enumerate(words) if w["s"] >= start - 0.5), None)
    if si is None:
        return None
    # if we landed mid-sentence, step back to the sentence start (max 6 s back)
    j = si
    while j > 0 and not words[j - 1]["w"].endswith(_END) and words[si]["s"] - words[j - 1]["s"] <= 6 and \
            words[j]["s"] - words[j - 1]["e"] < 0.9:
        j -= 1
    si = j
    s = words[si]["s"]
    # end: last word ending at/before end+0.6, then extend to the sentence end if it fits
    ei = None
    for i in range(si, len(words)):
        if words[i]["e"] <= end + 0.6:
            ei = i
        else:
            break
    if ei is None:
        return None
    k = ei
    while k + 1 < len(words) and not words[k]["w"].endswith(_END) and words[k + 1]["e"] - s <= max_len:
        k += 1
    if words[k]["w"].endswith(_END):
        ei = k
    e = words[ei]["e"]
    if e - s > max_len:
        # trim back to the last sentence end inside max_len, else hard cut on a word
        cut = [i for i in range(si, ei + 1) if words[i]["e"] - s <= max_len]
        ends = [i for i in cut if words[i]["w"].endswith(_END)]
        ei = (ends or cut or [si])[-1]
        e = words[ei]["e"]
    if e - s < min(min_len, duration) * 0.8:
        return None
    return round(max(0.0, s - 0.12), 2), round(min(duration, e + 0.35), 2)


def _overlap(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    return inter / max(0.01, min(a[1] - a[0], b[1] - b[0]))


def dedupe(clips: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in sorted(clips, key=lambda x: -x["score"]):
        if all(_overlap((c["start"], c["end"]), (o["start"], o["end"])) < 0.3 for o in out):
            out.append(c)
        if len(out) >= n:
            break
    return sorted(out, key=lambda x: x["start"])


def _text_between(words: List[Dict[str, Any]], s: float, e: float) -> str:
    return " ".join(w["w"] for w in words if w["s"] >= s and w["e"] <= e + 0.05)


def _tidy(raw: Dict[str, Any], words: List[Dict[str, Any]], st: Dict[str, Any], duration: float,
          engine: str) -> Optional[Dict[str, Any]]:
    se = snap(_num(raw.get("start")), _num(raw.get("end")), words, st["min_len"], st["max_len"], duration)
    if not se:
        return None
    s, e = se
    text = _text_between(words, s, e)
    first = " ".join(text.split()[:6])
    hook = _txt(raw.get("hook"), 60) or first
    return {
        "start": s, "end": e, "duration": round(e - s, 2),
        "score": int(max(0, min(100, _num(raw.get("score"), 50)))),
        "hook": " ".join(hook.split()[:7]),
        "title": _txt(raw.get("title"), 100) or (first[:70] if first else "Clip"),
        "description": _txt(raw.get("description"), 400),
        "hashtags": _tags(raw.get("hashtags")) or ["shorts"],
        "reason": _txt(raw.get("reason"), 200),
        "transcript": text[:2000],
        "picked_by": engine,
    }


# --------------------------------------------------------------------------- #
# Fallback (no AI)
# --------------------------------------------------------------------------- #

def fallback(words: List[Dict[str, Any]], z: List[float], duration: float, st: Dict[str, Any]) -> List[Dict[str, Any]]:
    n = st["max_clips"]
    length = max(st["min_len"], min(st["max_len"], 35))
    sec = int(math.ceil(duration))
    if sec <= 0:
        return []
    speech = [0.0] * (sec + 1)
    for w in words:
        for t in range(int(w["s"]), min(sec, int(w["e"]) + 1)):
            speech[t] = 1.0
    zz = (list(z) + [0.0] * (sec + 1))[: sec + 1]
    win = int(length)
    cands = []
    step = max(3, win // 4)
    for a in range(0, max(1, sec - win + 1), step):
        b = a + win
        loud = sum(max(0.0, x) for x in zz[a:b]) / max(1, win)
        talk = sum(speech[a:b]) / max(1, win)
        cands.append((loud * 2 + talk, a, b))
    if not cands:
        cands = [(1.0, 0, min(sec, win))]
    picked: List[Dict[str, Any]] = []
    for sc, a, b in sorted(cands, reverse=True):
        c = _tidy({"start": a, "end": b, "score": int(40 + min(40, sc * 20))}, words, st, duration, "loudness")
        if c and all(_overlap((c["start"], c["end"]), (o["start"], o["end"])) < 0.3 for o in picked):
            picked.append(c)
        if len(picked) >= n:
            break
    return sorted(picked, key=lambda x: x["start"])


# --------------------------------------------------------------------------- #
# Main entry
# --------------------------------------------------------------------------- #

async def find_clips(words: List[Dict[str, Any]], z: List[float], duration: float, st: Dict[str, Any], *,
                     title: str = "", uploader: str = "") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Returns (clips, engine_info)."""
    n = st["max_clips"]
    if duration < st["min_len"]:
        st = {**st, "min_len": max(5, int(duration * 0.6)), "max_len": int(duration)}
    lines = make_lines(words, z)
    if len(lines) < 3:
        clips = fallback(words, z, duration, st)
        return clips, {"engine": "loudness", "reason": "not enough speech"}

    parts = windows(lines, duration)
    per = max(2, math.ceil(n * 1.6 / len(parts)))
    focus = f"Editor's focus from the creator: {st['focus']}\n" if st.get("focus") else ""
    found: List[Dict[str, Any]] = []
    used: Optional[str] = None
    errors = 0
    for idx, (a, b, part_lines) in enumerate(parts):
        if len(part_lines) < 2:
            continue
        user = PROMPT.format(title=title or "(unknown)", uploader=uploader or "(unknown)",
                             part=f"{idx + 1} of {len(parts)} ({a:.0f}s-{b:.0f}s of {duration:.0f}s)", focus=focus,
                             n=per, min_len=st["min_len"], max_len=st["max_len"], transcript=_fmt(part_lines)[:60000])
        try:
            obj, res = await llm_router.complete_json(SYSTEM, user, temperature=0.4, max_tokens=4096,
                                                      budget_s=config.LLM_BUDGET_S)
            used = f"{res.provider}:{res.model}"
        except LLMError as e:
            errors += 1
            log.warning("clip AI failed on part %s: %s", idx + 1, e)
            continue
        raw = obj.get("clips") if isinstance(obj, dict) else obj
        for r in raw if isinstance(raw, list) else []:
            if isinstance(r, dict):
                c = _tidy(r, words, st, duration, "ai")
                if c:
                    found.append(c)

    clips = dedupe(found, n)
    if not clips:
        clips = fallback(words, z, duration, st)
        return clips, {"engine": "loudness", "reason": "AI unavailable" if errors else "AI found nothing",
                       "ai": used}
    return clips, {"engine": "ai", "ai": used, "parts": len(parts), "ai_errors": errors}
