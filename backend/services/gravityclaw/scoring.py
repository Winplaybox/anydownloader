"""Deterministic prompt quality scorer (no LLM). Fast, explainable, target-aware."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .catalog import TARGETS

_R = lambda p: re.compile(p, re.IGNORECASE)  # noqa: E731

CHECK_PATTERNS: Dict[str, re.Pattern] = {
    "style": _R(r"\b(style|render|rendered|painting|photo(graph)?|illustration|anime|3d|vector|cinematic|watercolor|"
                r"aesthetic|realistic|photoreal|art|sketch|cel|pixar|ghibli|oil|claymation|isometric|comic|film)\b"),
    "lighting": _R(r"\b(light(ing)?|sunlight|sunrise|sunset|glow(ing)?|shadows?|golden hour|rim|back ?lit|neon|"
                   r"volumetric|ambient|moonlight|studio light|softbox|chiaroscuro|lantern|candle)\b"),
    "composition": _R(r"\b(close[- ]?up|wide|portrait|fram(e|ing)|cent(er|re)d|rule of thirds|angle|view|composition|"
                      r"symmetr\w*|top[- ]down|overhead|\d{2,3}\s?mm|lens|bokeh|depth of field|foreground|background)\b"),
    "color": _R(r"(\b(colou?rs?|palette|tones?|hues?|monochrome|vibrant|pastel|saturated|muted|teal|orange|gold(en)?|"
                r"crimson|red|blue|green|purple|black|white|neon)\b|#[0-9a-f]{6}\b)"),
    "detail": _R(r"\b(detailed|details?|texture[sd]?|intricate|sharp|crisp|8k|4k|high[- ]res(olution)?|fine|ultra|hyper)\b"),
    "action": _R(r"\b(walk\w*|runs?|running|turn\w*|mov\w+|fl(y|ies|ying)|ris(e|es|ing)|fall\w*|danc\w+|spin\w*|"
                 r"plays?|playing|looks?|looking|reach\w*|jump\w*|crash\w*|explod\w+|pour\w*|smil\w+|speak\w*|says?)\b"),
    "camera": _R(r"\b(dolly|pan(s|ning)?|tilt\w*|tracking|orbit\w*|crane|zoom\w*|push(es)? in|pull(s)? (out|back)|"
                 r"handheld|static camera|drone|steadicam|camera|whip pan|rack focus|fpv)\b|\[(push|pan|tracking|zoom)"),
    "shot": _R(r"\b(close[- ]?up|wide shot|medium shot|establishing|over[- ]the[- ]shoulder|pov|aerial|macro|"
               r"long shot|full shot|two[- ]shot|shot)\b"),
    "audio": _R(r"\b(audio|sound|sfx|music|ambien(t|ce)|says|dialogue|whisper\w*|footsteps|rain sound|voice)\b"),
    "role": _R(r"(\byou are\b|#\s*role|\bact as\b|\bas an? (expert|senior|world))"),
    "context": _R(r"(#\s*context|\bcontext\b|\bbackground\b|\bexisting\b|\bstack\b|\baudience\b)"),
    "task": _R(r"(#\s*(objective|goal|task)|\b(task|objective|goal|your job|write|create|build|generate|design|produce)\b)"),
    "constraints": _R(r"(#\s*constraints|\b(must|never|do not|don't|avoid|only|limit|max(imum)?|under \d+)\b)"),
    "format": _R(r"(#\s*output|\b(format|output|json|markdown|table|bullets?|schema|template|sections?|headings?)\b|^\s*#{1,3}\s|\[\d)", ),
    "examples": _R(r"\b(example|e\.g\.|for instance|sample)\b"),
    "acceptance": _R(r"\b(acceptance|criteria|done when|checklist|definition of done|tests?)\b"),
    "hook": _R(r"(\bhook\b|0\s*[-–]\s*3\s*s|\[0[:.]|first (3|three) seconds|pattern interrupt|subject line)"),
    "genre": _R(r"\b(pop|rock|lo-?fi|hip ?hop|rap|edm|bhajan|kirtan|devotional|classical|folk|bollywood|jazz|"
                r"ambient|orchestral|cinematic|trap|r&b|indie|sufi|qawwali|ghazal|metal|country|synthwave|score)\b"),
    "mood": _R(r"\b(happy|sad|peaceful|calm|energetic|dark|uplifting|emotional|romantic|epic|eerie|melanchol\w+|"
               r"joyful|serene|tense|dreamy|devotional|spiritual|motivational)\b"),
    "tempo": _R(r"(\b\d{2,3}\s?bpm\b|\b(slow|mid[- ]?tempo|fast|upbeat|downtempo|tempo)\b)"),
    "instruments": _R(r"\b(piano|guitar|flute|bansuri|sitar|tabla|dhol|harmonium|violin|strings|drums|synth|bass|"
                      r"santoor|shehnai|veena|mridangam|pads|choir|bells|percussion|brass)\b"),
    "vocals": _R(r"\b(vocals?|singer|voice|male|female|choir|duet|chant\w*|instrumental|no vocals)\b"),
}

SUGGESTIONS = {
    "subject": "Name the main subject precisely (who/what, key attributes).",
    "style": "Add a medium/style (e.g. cinematic photo, Pixar 3D, watercolor).",
    "lighting": "Specify lighting (golden hour, soft studio light, neon rim light).",
    "composition": "Add framing/camera (close-up, wide angle, 35mm, rule of thirds).",
    "color": "Define a color palette or mood colors.",
    "detail": "Add texture/detail cues (intricate, sharp focus, 8k).",
    "negative": "Add a negative prompt to block artifacts (blurry, watermark, extra fingers).",
    "action": "Describe what moves and how (motion verbs).",
    "camera": "Add camera movement (dolly in, orbit, tracking shot).",
    "shot": "State the shot type (wide establishing, medium, close-up).",
    "duration": "Set a duration for the clip.",
    "audio": "Describe sound: ambience, SFX, music or dialogue.",
    "role": "Start with a clear role: 'You are a ...'.",
    "context": "Give background context (audience, product, existing stack).",
    "task": "State the exact task/objective.",
    "constraints": "Add constraints (must / must not, limits).",
    "format": "Specify the output format (sections, JSON schema, table).",
    "examples": "Include a short example of the desired output.",
    "acceptance": "Add testable acceptance criteria.",
    "hook": "Open with a strong hook in the first line / first 3 seconds.",
    "genre": "Name the genre / sub-genre.",
    "mood": "Name the mood/emotion.",
    "tempo": "Add tempo or BPM.",
    "instruments": "List key instruments.",
    "vocals": "Specify vocals (male/female, style) or instrumental.",
    "lyrics": "Add structured lyrics with [Verse]/[Chorus] tags.",
}


def _length_fit(words: int, lo: int, hi: int) -> float:
    if lo <= words <= hi:
        return 1.0
    if words < lo:
        return max(0.0, words / lo)
    return max(0.0, 1.0 - (words - hi) / max(hi, 1))


def score_prompt(prompt: str, target_id: str, *, negative: str = "", lyrics: str = "",
                 params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    t = TARGETS.get(target_id) or TARGETS["llm_task"]
    text = prompt or ""
    words = len(re.findall(r"\S+", text))
    lo, hi = t["length"]
    results: List[Dict[str, Any]] = []
    for chk in t["checks"]:
        if chk == "subject":
            ok = words >= 5
        elif chk == "negative":
            ok = len((negative or "").strip()) >= 8
        elif chk == "lyrics":
            ok = bool(re.search(r"\[(verse|chorus|intro|bridge|outro)", lyrics or "", re.I)) or bool((params or {}).get("instrumental"))
        elif chk == "duration":
            ok = any(k in (params or {}) for k in ("duration_s", "minutes", "frames")) or bool(re.search(r"\b\d+\s?(s|sec|seconds)\b", text))
        else:
            pat = CHECK_PATTERNS.get(chk)
            ok = bool(pat.search(text)) if pat else True
        results.append({"check": chk, "pass": ok, **({} if ok else {"suggestion": SUGGESTIONS.get(chk, "")})})

    passed = sum(1 for r in results if r["pass"])
    coverage = passed / max(1, len(results))
    fit = _length_fit(words, lo, hi)
    score = round(70 * coverage + 30 * fit)
    grade = "S" if score >= 92 else "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    return {
        "score": score,
        "grade": grade,
        "words": words,
        "recommended_words": [lo, hi],
        "checks": results,
        "suggestions": [r["suggestion"] for r in results if not r["pass"] and r.get("suggestion")]
                       + ([f"Aim for {lo}-{hi} words (now {words})."] if fit < 1 else []),
    }
