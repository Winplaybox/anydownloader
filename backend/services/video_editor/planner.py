"""LLM planning for the AI Video Editor.

Two calls:
  1. plan_script  - looks at timestamped frames (+ transcript + creator brief) and writes
                    the voiceover lines with start times, plus hook / end-card texts.
  2. plan_metadata - writes publish-ready title options, description, tags, hashtags and
                    any extra sections the creator asked for in the brief.
Both outputs are validated and repaired server-side so a sloppy model reply can
never break the render.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    from backend.services.llm_router import LLMError, llm_router
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services.llm_router import LLMError, llm_router  # type: ignore

from .options import LANG_BY_ID

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
TAGS_MAX = 500


class PlanError(Exception):
    pass


def _words_per_second(lang: str) -> float:
    # measured on Kokoro/Edge at speed ~1.05 incl. short pauses; conservative so lines fit
    return {"hi": 2.5, "mr": 2.2, "gu": 2.2, "bn": 2.2, "ta": 1.7, "te": 1.8, "kn": 1.7, "ml": 1.5,
            "pa": 2.4, "ur": 2.4, "ar": 2.0, "de": 2.0, "ru": 2.0}.get(lang, 2.4)


def _script_rules(lang: str, caption_script: str) -> str:
    li = LANG_BY_ID.get(lang, {"name": lang, "indic": False})
    if li.get("indic") and caption_script == "roman":
        cap = (f"'caption' = the SAME words as 'tts' written in Roman letters the way Indians type {li['name']} "
               f"on social media (Hinglish style, e.g. 'Raat ko road par haadsa ho gaya'). Same word order, same "
               f"number of words as 'tts'. Write numbers as digits.")
    else:
        cap = "'caption' = exactly the same text as 'tts' (native script). Write numbers as digits."
    tts = (f"'tts' = the line written in natural spoken {li['name']} in its NATIVE script "
           f"(e.g. Devanagari for Hindi) so the voice engine pronounces it correctly. Spell numbers as words.")
    if lang.startswith("en"):
        tts = "'tts' = the line in natural spoken English. Spell numbers as words."
    return tts + "\n" + cap


SCRIPT_SYSTEM = """You are a senior short-form video editor and scriptwriter for YouTube Shorts, Reels and TikTok.
You write voiceover narration that matches what is ON SCREEN at each moment, hooks viewers in the first 2 seconds,
keeps them watching, and ends with a clear call to action. You never invent facts: names, places, dates, numbers,
injuries, causes or claims must come ONLY from the creator's brief, the transcript or what is clearly visible.
When something is unclear, describe what is visible instead of guessing. Respond with JSON only."""


def _script_prompt(*, brief: str, channel: str, lang: str, caption_script: str, duration: float,
                   frame_times: List[float], transcript: str, mode: str, user_script: str) -> str:
    li = LANG_BY_ID.get(lang, {"name": lang})
    wps = _words_per_second(lang)
    budget = int(duration * wps * 0.9)
    frames = ", ".join(f"frame {i + 1} @ {t:.1f}s" for i, t in enumerate(frame_times))
    need_lines = mode != "original"
    lines_rule = (
        f"""- Write the voiceover as 'lines'. Each line: 5-14 words, one idea, matched to the frames around its 'start'.
- Total spoken words across all lines: about {budget} (never more than {int(budget * 1.1)}). The video is {duration:.1f}s long.
- 'start' (seconds) must increase; leave ~0.3s between lines; first line starts at 0.2-0.5s; the last line must
  finish at least 1s before {duration:.1f}s. Cover the whole video - no silent stretch longer than 3s.
- Line 1 is the HOOK (curiosity / shock / question). Middle lines narrate what is happening on screen.
  Final line = call to action that fits the channel (follow / subscribe / comment).
{_script_rules(lang, caption_script)}"""
        if need_lines else
        "- The creator keeps the original speech, so return \"lines\": [] (empty)."
    )
    own = ""
    if user_script.strip() and need_lines:
        own = f"""
The creator wrote their own voiceover script below. Use THEIR words (you may only split them into lines,
fix obvious typos and convert script/spelling as required for 'tts' and 'caption'). Do not add new sentences.
Distribute the lines over the video by meaning.
CREATOR SCRIPT:
{user_script.strip()[:4000]}
"""
    return f"""Frames from the video are attached in order: {frames}.
Video duration: {duration:.1f}s. Voiceover language: {li['name']}. Channel: {channel or 'not given'}.

CREATOR BRIEF (what they want; may also contain publishing requests - ignore those here):
{brief.strip()[:3000] or '(none)'}

TRANSCRIPT OF ORIGINAL AUDIO (may be empty or noisy):
{transcript.strip()[:2500] or '(no clear speech)'}
{own}
Return JSON:
{{
  "summary": "2-4 factual sentences in English describing what happens in the video, scene by scene",
  "mood": "one of: news, dramatic, funny, emotional, informative, motivational, travel, food, devotional, horror, calm",
  "hook": {{"title": "on-screen title, max 5 words, CAPS-friendly, in the caption script", "subtitle": "max 4 words or empty"}},
  "end_card": {{"title": "max 4 words CTA, in the caption script", "subtitle": "max 4 words or empty"}},
  "lines": [{{"start": 0.3, "tts": "...", "caption": "..."}}]
}}
Rules:
{lines_rule}
- hook/end_card texts are short overlays, not full sentences, written in the same script as captions.
"""


def _clean_line(t: Any) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip()


def validate_script(obj: Dict[str, Any], duration: float, need_lines: bool) -> Dict[str, Any]:
    lines_in = obj.get("lines") if isinstance(obj.get("lines"), list) else []
    lines: List[Dict[str, Any]] = []
    last = -1.0
    for ln in lines_in:
        if not isinstance(ln, dict):
            continue
        tts = _clean_line(ln.get("tts"))
        cap = _clean_line(ln.get("caption")) or tts
        if not tts:
            continue
        try:
            st = float(ln.get("start", 0))
        except (TypeError, ValueError):
            st = last + 1.0
        st = max(0.2, min(st, duration - 1.0))
        if st <= last:
            st = last + 0.3
        lines.append({"start": round(st, 2), "tts": tts[:400], "caption": cap[:400]})
        last = st
    if need_lines and not lines:
        raise PlanError("The AI did not return a usable voiceover script.")

    def short(d: Any, n: int) -> Dict[str, str]:
        d = d if isinstance(d, dict) else {}
        return {"title": _clean_line(d.get("title"))[:n], "subtitle": _clean_line(d.get("subtitle"))[:n]}

    return {
        "summary": _clean_line(obj.get("summary"))[:1200],
        "mood": _clean_line(obj.get("mood"))[:20] or "informative",
        "hook": short(obj.get("hook"), 40),
        "end_card": short(obj.get("end_card"), 40),
        "lines": lines,
    }


def _fallback_script(*, brief: str, channel: str, lang: str, caption_script: str, duration: float,
                     transcript: str, mode: str, user_script: str = "") -> Dict[str, Any]:
    """Guaranteed fallback script generator if all external LLM providers are down or fail."""
    if mode == "original":
        return {
            "summary": brief or "Original video clip.",
            "mood": "informative",
            "hook": {"title": "WATCH THIS", "subtitle": ""},
            "end_card": {"title": "FOLLOW FOR MORE", "subtitle": channel or ""},
            "lines": []
        }

    source_text = user_script.strip() or brief.strip() or transcript.strip() or "Watch this incredible video clip until the end. Like and subscribe for more."
    raw_sentences = [s.strip() for s in re.split(r'[.\n!?]+', source_text) if len(s.strip()) > 2]
    if not raw_sentences:
        raw_sentences = ["Check out what happens in this clip", "Follow and subscribe for more updates"]

    wps = _words_per_second(lang)
    lines = []
    cur_t = 0.5
    for s in raw_sentences:
        if cur_t >= duration - 2.0:
            break
        word_count = max(1, len(s.split()))
        line_dur = max(1.5, min(4.5, word_count / wps))
        if cur_t + line_dur > duration - 0.5:
            line_dur = max(1.0, duration - 0.5 - cur_t)
        lines.append({
            "start": round(cur_t, 2),
            "tts": s,
            "caption": s
        })
        cur_t += line_dur + 0.3

    if cur_t < duration - 2.5:
        cta_text = f"Subscribe to {channel}" if channel else "Follow for more daily videos"
        lines.append({
            "start": round(cur_t, 2),
            "tts": cta_text,
            "caption": cta_text
        })

    return {
        "summary": brief or "Video content overview.",
        "mood": "informative",
        "hook": {"title": "WATCH THIS", "subtitle": ""},
        "end_card": {"title": "FOLLOW FOR MORE", "subtitle": channel or ""},
        "lines": lines
    }


def _fallback_metadata(*, brief: str, channel: str, lang: str, duration: float, links: List[str]) -> Dict[str, Any]:
    """Guaranteed fallback metadata generator if LLM is unavailable."""
    base_title = (brief.split('.')[0].strip() if brief else "Must Watch Viral Video")[:55]
    if not base_title:
        base_title = "Trending Viral Video"
    link_section = "\n".join(links) if links else ""
    return {
        "titles": [
            f"{base_title} #shorts",
            f"You Won't Believe This! #shorts",
            f"{channel or 'Daily Viral'}: {base_title}"
        ],
        "description": f"{brief or base_title}\n\nDon't forget to like, share and subscribe!\n{link_section}\n\n#shorts #viral #trending #reels",
        "tags": "shorts, viral, trending, reels, video, fyp",
        "hashtags": ["#shorts", "#viral", "#trending", "#reels"],
        "extras": []
    }


async def plan_script(*, frames: List[bytes], frame_times: List[float], brief: str, channel: str, lang: str,
                      caption_script: str, duration: float, transcript: str, mode: str,
                      user_script: str = "") -> Dict[str, Any]:
    prompt = _script_prompt(brief=brief, channel=channel, lang=lang, caption_script=caption_script,
                            duration=duration, frame_times=frame_times, transcript=transcript, mode=mode,
                            user_script=user_script)
    try:
        obj, res = await llm_router.complete_json_vision(SCRIPT_SYSTEM, prompt, frames, temperature=0.6,
                                                         max_tokens=5000)
    except Exception as e:
        log.warning("AI script LLM provider failed, using fallback script builder: %s", e)
        obj = _fallback_script(brief=brief, channel=channel, lang=lang, caption_script=caption_script,
                               duration=duration, transcript=transcript, mode=mode, user_script=user_script)
        res = LLMResult("", "fallback", "script_builder", 10)

    try:
        out = validate_script(obj, duration, need_lines=(mode != "original"))
    except Exception as e:
        log.warning("Script validation failed on LLM output, building robust fallback: %s", e)
        fallback_obj = _fallback_script(brief=brief, channel=channel, lang=lang, caption_script=caption_script,
                                        duration=duration, transcript=transcript, mode=mode, user_script=user_script)
        out = validate_script(fallback_obj, duration, need_lines=(mode != "original"))

    out["llm"] = f"{res.provider}:{res.model}"
    return out


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
META_SYSTEM = """You are a YouTube / Instagram growth strategist and SEO copywriter for Indian creators.
You write titles that earn clicks without clickbait lies, descriptions that rank, and tags that match real searches.
Follow the creator's requested structure exactly. Use ONLY the links the creator provided, exactly as written.
Never invent facts (places, names, numbers, causes) that are not in the brief or the video summary.
Respond with JSON only."""


def _meta_prompt(*, brief: str, channel: str, lang: str, summary: str, script_text: str, duration: float,
                 links: List[str]) -> str:
    li = LANG_BY_ID.get(lang, {"name": lang})
    fmt = "YouTube Short" if duration <= 180 else "YouTube video"
    link_rule = ("Links to use (exactly, wherever a link is needed): " + ", ".join(links)) if links else \
        "The creator gave no links: do not add any URL."
    return f"""Create publishing metadata for this {fmt} ({duration:.0f}s).
Channel: {channel or 'not given'}. Content language: {li['name']} (write in the same style the creator writes in;
for Hindi audiences use Hinglish in Roman script unless the brief asks otherwise).

CREATOR BRIEF / REQUIREMENTS (follow every request in it - sections, counts, disclaimer, links, tone):
{brief.strip()[:4000] or '(none - produce a strong standard package)'}

WHAT HAPPENS IN THE VIDEO:
{summary or '(unknown)'}

VOICEOVER / SPEECH:
{script_text[:2500] or '(none)'}

{link_rule}

Return JSON:
{{
  "titles": ["3 title options, best first, each <= 70 characters, hook-first, include #shorts for Shorts"],
  "description": "the complete ready-to-paste description as plain text with line breaks (\\n). First line = main
                  keyword + hook. Include every section the brief asks for (e.g. Topics Covered, Expanded Keywords,
                  Queries, Disclaimer) with the exact counts asked. End with relevant hashtags.",
  "tags": "comma-separated YouTube tags, most important first, total under 480 characters",
  "hashtags": ["3-5 hashtags for the top of the description / Shorts, with #"],
  "extras": [{{"heading": "any other deliverable the brief asked for that is not part of the description (e.g. Instagram caption, pinned comment, thumbnail text)", "content": "..."}}]
}}"""


def _trim_tags(tags: Any) -> str:
    if isinstance(tags, list):
        tags = ",".join(str(t) for t in tags)
    parts, seen, out = [p.strip().lstrip("#") for p in str(tags or "").split(",")], set(), []
    total = 0
    for p in parts:
        if not p or p.lower() in seen:
            continue
        add = len(p) + (1 if out else 0)
        if total + add > TAGS_MAX:
            break
        out.append(p)
        seen.add(p.lower())
        total += add
    return ",".join(out)


def validate_metadata(obj: Dict[str, Any], links: List[str]) -> Dict[str, Any]:
    titles = [_clean_line(t)[:100] for t in (obj.get("titles") or []) if _clean_line(t)][:5]
    desc = str(obj.get("description") or "").replace("\r\n", "\n").strip()[:5000]
    if links and desc and not any(l in desc for l in links):
        desc += "\n\n🔗 " + links[0]
    hashtags = []
    for h in obj.get("hashtags") or []:
        h = re.sub(r"\s+", "", str(h))
        if h and not h.startswith("#"):
            h = "#" + h
        if h and h not in hashtags:
            hashtags.append(h)
    extras = []
    for x in obj.get("extras") or []:
        if isinstance(x, dict) and _clean_line(x.get("heading")) and str(x.get("content") or "").strip():
            extras.append({"heading": _clean_line(x["heading"])[:80], "content": str(x["content"]).strip()[:3000]})
    return {"titles": titles, "description": desc, "tags": _trim_tags(obj.get("tags")),
            "hashtags": hashtags[:10], "extras": extras[:6]}


def extract_links(brief: str) -> List[str]:
    seen: List[str] = []
    for u in URL_RE.findall(brief or ""):
        u = u.rstrip(".,;")
        if u not in seen:
            seen.append(u)
    return seen


async def plan_metadata(*, brief: str, channel: str, lang: str, summary: str, script_text: str,
                        duration: float) -> Optional[Dict[str, Any]]:
    links = extract_links(brief)
    prompt = _meta_prompt(brief=brief, channel=channel, lang=lang, summary=summary, script_text=script_text,
                          duration=duration, links=links)
    try:
        obj, res = await llm_router.complete_json(META_SYSTEM, prompt, temperature=0.7, max_tokens=6000,
                                                  budget_s=120)
        out = validate_metadata(obj, links)
        out["llm"] = f"{res.provider}:{res.model}"
        return out
    except Exception as e:
        log.warning("Metadata generation LLM failed, using fallback metadata: %s", e)
        fallback_obj = _fallback_metadata(brief=brief, channel=channel, lang=lang, duration=duration, links=links)
        fallback_obj["llm"] = "fallback:metadata_builder"
        return fallback_obj
