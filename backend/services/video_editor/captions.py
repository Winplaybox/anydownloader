"""ASS subtitle builder: word-timed caption styles + title overlays.

Input words are dicts {w, s, e, brk} on the final video timeline (seconds);
`brk` marks the end of a phrase (punctuation / pause) so chunks never span it.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

PUNCT_END = (",", ".", "!", "?", "।", "|", ";", ":", "…", "؟", "،")


def ass_color(hex_color: str, alpha: int = 0) -> str:
    h = (hex_color or "#FFFFFF").lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        h = "FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def esc(text: str) -> str:
    return re.sub(r"[{}\\]", "", text or "").replace("\n", " ").strip()


def mark_breaks(words: List[Dict[str, Any]], gap: float = 0.35) -> List[Dict[str, Any]]:
    out = []
    for i, w in enumerate(words):
        nxt = words[i + 1]["s"] if i + 1 < len(words) else None
        brk = w.get("brk") or str(w["w"]).endswith(PUNCT_END) or (nxt is not None and nxt - w["e"] > gap)
        out.append({**w, "brk": bool(brk)})
    return out


def chunk(words: List[Dict[str, Any]], max_words: int, max_chars: int = 22) -> List[List[Dict[str, Any]]]:
    chunks: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []
    for w in words:
        if cur and (len(cur) >= max_words or len(" ".join(x["w"] for x in cur + [w])) > max_chars):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w["brk"]:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def _upper(t: str) -> str:
    return t.upper() if re.search(r"[a-z]", t) else t


class _Doc:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.styles: List[str] = []
        self.events: List[str] = []

    def style(self, name: str, font: str, size: int, primary: str, secondary: str, outline_c: str, back: str,
              border_style: int, outline: float, shadow: float, align: int = 5, bold: int = -1,
              margin_v: int = 0, margin_lr: int = 60, spacing: float = 0) -> None:
        self.styles.append(
            f"Style: {name},{font},{size},{primary},{secondary},{outline_c},{back},{bold},0,0,0,100,100,"
            f"{spacing},0,{border_style},{outline},{shadow},{align},{margin_lr},{margin_lr},{margin_v},1")

    def event(self, start: float, end: float, style: str, text: str, layer: int = 1) -> None:
        if end - start < 0.02:
            return
        self.events.append(f"Dialogue: {layer},{ts(start)},{ts(end)},{style},,0,0,0,,{text}")

    def render(self) -> str:
        return (
            "[Script Info]\nScriptType: v4.00+\n"
            f"PlayResX: {self.w}\nPlayResY: {self.h}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n"
            "YCbCr Matrix: TV.709\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n" + "\n".join(self.styles) +
            "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" +
            "\n".join(self.events) + "\n")


def build_ass(*, words: List[Dict[str, Any]], style: str, width: int, height: int, font: str,
              accent: str = "#FFE500", hook: Optional[Dict[str, str]] = None,
              end_card: Optional[Dict[str, str]] = None, duration: float = 0.0,
              overlay_font: Optional[str] = None) -> str:
    vertical = height / max(1, width) > 1.3
    unit = (width / 1080.0) if vertical else (height / 1080.0) * 0.82
    cx = width // 2
    cy = int(height * (0.70 if vertical else 0.80))
    white, black = ass_color("#FFFFFF"), ass_color("#000000")
    acc = ass_color(accent)
    doc = _Doc(width, height)
    ofont = overlay_font or font

    # ---- title overlays (hook at start, CTA at end) ---------------------------------
    doc.style("Tag", ofont, int(64 * unit), white, white, ass_color("#E01A1A"), black, 3, int(18 * unit), 0,
              align=8, margin_v=int(height * (0.155 if vertical else 0.07)))
    doc.style("Tag2", ofont, int(44 * unit), black, black, acc, black, 3, int(13 * unit), 0,
              align=8, margin_v=int(height * (0.155 if vertical else 0.07)) + int(108 * unit))
    fade = r"{\fad(200,200)}"
    if hook and hook.get("title"):
        doc.event(0.0, min(3.6, duration or 3.6), "Tag", fade + esc(_upper(hook["title"])), layer=3)
        if hook.get("subtitle"):
            doc.event(0.25, min(3.6, duration or 3.6), "Tag2", fade + esc(_upper(hook["subtitle"])), layer=3)
    if end_card and end_card.get("title") and duration > 8:
        st = max(4.0, duration - 4.2)
        doc.event(st, duration, "Tag", fade + esc(_upper(end_card["title"])), layer=3)
        if end_card.get("subtitle"):
            doc.event(st + 0.2, duration, "Tag2", fade + esc(_upper(end_card["subtitle"])), layer=3)

    if style == "none" or not words:
        return doc.render()

    words = mark_breaks(sorted(words, key=lambda x: x["s"]))
    pos = rf"{{\an5\pos({cx},{cy})}}"

    def hold_end(chs: List[List[Dict[str, Any]]], i: int) -> float:
        end = chs[i][-1]["e"]
        nxt = chs[i + 1][0]["s"] if i + 1 < len(chs) else end + 0.4
        return nxt if nxt - end < 0.35 else end + 0.12

    if style in ("pop", "box"):
        size = int((86 if style == "pop" else 70) * unit)
        if style == "pop":
            doc.style("Cap", font, size, white, white, black, ass_color("#000000", 0x70), 1, 7 * unit, 3 * unit)
        else:
            doc.style("Cap", font, size, white, white, ass_color("#000000", 0x30), black, 3, 16 * unit, 0)
        chs = chunk(words, 3 if style == "pop" else 4, 20 if style == "pop" else 26)
        for ci, ch in enumerate(chs):
            end = hold_end(chs, ci)
            for wi, w in enumerate(ch):
                s = w["s"] if wi else min(w["s"], ch[0]["s"])
                e = ch[wi + 1]["s"] if wi + 1 < len(ch) else end
                parts = []
                for wj, x in enumerate(ch):
                    t = esc(_upper(x["w"]))
                    if wj == wi:
                        pop = r"\t(0,90,\fscx112\fscy112)\t(90,180,\fscx104\fscy104)" if style == "pop" else ""
                        parts.append(rf"{{\c{acc}{pop}}}{t}{{\c{white}\fscx100\fscy100}}")
                    else:
                        parts.append(t)
                doc.event(s, e, "Cap", pos + " ".join(parts))

    elif style == "single":
        doc.style("Cap", font, int(116 * unit), white, white, black, ass_color("#000000", 0x60), 1, 8 * unit, 4 * unit)
        for i, w in enumerate(words):
            e = words[i + 1]["s"] if i + 1 < len(words) and words[i + 1]["s"] - w["e"] < 0.35 else w["e"] + 0.1
            color = acc if (i % 3 == 0 or w["brk"]) else white
            doc.event(w["s"], e, "Cap",
                      pos + rf"{{\c{color}\fscx70\fscy70\t(0,80,\fscx108\fscy108)\t(80,160,\fscx100\fscy100)}}"
                      + esc(_upper(w["w"])))

    elif style == "karaoke":
        # Primary = sung colour, Secondary = not-yet-sung colour.
        doc.style("Cap", font, int(80 * unit), acc, white, black, ass_color("#000000", 0x70), 1, 7 * unit, 3 * unit)
        chs = chunk(words, 4, 26)
        for ci, ch in enumerate(chs):
            end = hold_end(chs, ci)
            parts, t = [], ch[0]["s"]
            for wi, w in enumerate(ch):
                nxt = ch[wi + 1]["s"] if wi + 1 < len(ch) else w["e"]
                dur_cs = max(1, int(round((nxt - t) * 100)))
                parts.append(rf"{{\kf{dur_cs}}}{esc(_upper(w['w']))}")
                t = nxt
            doc.event(ch[0]["s"], end, "Cap", pos + " ".join(parts))

    elif style == "minimal":
        doc.style("Cap", font, int(64 * unit), white, white, black, ass_color("#000000", 0x40), 1, 0, 3 * unit,
                  align=2, margin_v=int(height * (0.25 if vertical else 0.08)), margin_lr=int(90 * unit))
        chs = chunk(words, 9, 52)
        for ci, ch in enumerate(chs):
            doc.event(ch[0]["s"], hold_end(chs, ci), "Cap",
                      r"{\fad(120,120)}" + " ".join(esc(x["w"]) for x in ch))
    return doc.render()


def words_from_lines(placed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """placed: [{caption, start, end}] -> per-word timings proportional to spoken length."""
    out: List[Dict[str, Any]] = []
    for ln in placed:
        toks = (ln.get("caption") or "").split()
        if not toks:
            continue
        dur = max(0.2, ln["end"] - ln["start"])
        weights = []
        for tok in toks:
            core = re.sub(r"[^\w]", "", tok, flags=re.UNICODE)
            wt = (len(core) if not core.isdigit() else len(core) * 3) + 2
            if tok.endswith(PUNCT_END):
                wt += 3
            weights.append(wt)
        tot, t = float(sum(weights)), ln["start"]
        for tok, wt in zip(toks, weights):
            d = dur * wt / tot
            out.append({"w": tok, "s": round(t, 3), "e": round(t + d, 3), "brk": tok.endswith(PUNCT_END)})
            t += d
        out[-1]["brk"] = True
    return out


def srt_from_words(words: List[Dict[str, Any]]) -> str:
    words = mark_breaks(sorted(words, key=lambda x: x["s"]))
    chs = chunk(words, 8, 42)

    def f(t: float) -> str:
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    return "\n".join(f"{i}\n{f(c[0]['s'])} --> {f(c[-1]['e'])}\n{' '.join(x['w'] for x in c)}\n"
                     for i, c in enumerate(chs, 1))
