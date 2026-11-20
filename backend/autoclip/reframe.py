"""9:16 framing decision per clip: face-centred crop, centre crop, or blurred fit.

Face detection uses OpenCV's bundled Haar cascade when opencv is installed (opencv-python-headless).
Without OpenCV, 'auto' falls back to blurred fit for wide sources and 'face' to a centre crop.
"""
from __future__ import annotations

import logging
import os
import statistics
import tempfile
from typing import Any, Dict, List, Optional

from . import media

log = logging.getLogger("autoclip.reframe")
_cascade = None


def _detector():
    """Haar face cascade, or False when OpenCV/the cascade file isn't available (never raises)."""
    global _cascade
    if _cascade is None:
        try:
            import cv2

            path = os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""),
                                "haarcascade_frontalface_default.xml")
            c = cv2.CascadeClassifier(path) if os.path.isfile(path) else None
            _cascade = c if c is not None and not c.empty() else False
        except Exception:
            _cascade = False
        if _cascade is False:
            log.warning("face cascade unavailable; framing falls back to centre/fit")
    return _cascade


def face_tracking_available() -> bool:
    return bool(_detector())


def face_centers(src: str, start: float, end: float, samples: int = 7) -> List[Dict[str, float]]:
    """[{x, area}] normalised 0..1 for the biggest face in each sampled frame."""
    det = _detector()
    if not det:
        return []
    import cv2

    out: List[Dict[str, float]] = []
    with tempfile.TemporaryDirectory(prefix="ac_face_") as tmp:
        for i in range(samples):
            t = start + (end - start) * (i + 0.5) / samples
            p = media.grab_frame(src, t, os.path.join(tmp, f"f{i}.jpg"), width=640)
            if not p:
                continue
            img = cv2.imread(p)
            if img is None:
                continue
            gray = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
            h, w = gray.shape[:2]
            faces = det.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=6,
                                                 minSize=(max(24, w // 20), max(24, w // 20)))
            if len(faces):
                x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                out.append({"x": (x + fw / 2) / w, "area": (fw * fh) / float(w * h)})
    return out


def decide(src: str, info: Dict[str, Any], start: float, end: float, layout: str) -> Dict[str, Any]:
    """Returns {"mode": "crop"|"fit", "cx": 0..1}."""
    sw, sh = info["width"], info["height"]
    aspect = sw / max(1, sh)
    if aspect <= 0.75:                      # already vertical: plain fill
        return {"mode": "crop", "cx": 0.5, "why": "vertical source"}
    if layout == "fit":
        return {"mode": "fit", "cx": 0.5, "why": "chosen"}
    if layout == "center":
        return {"mode": "crop", "cx": 0.5, "why": "chosen"}
    faces = face_centers(src, start, end)
    hit_rate = len(faces) / 7.0
    if faces and hit_rate >= 0.4:
        xs = [f["x"] for f in faces]
        spread = statistics.pstdev(xs) if len(xs) > 1 else 0.0
        cx = statistics.median(xs)
        if layout == "auto" and spread > 0.2:   # two people far apart: show both
            return {"mode": "fit", "cx": 0.5, "why": "multiple speakers"}
        return {"mode": "crop", "cx": round(cx, 3), "why": f"face {hit_rate:.0%}"}
    if layout == "face":
        return {"mode": "crop", "cx": 0.5, "why": "no face found"}
    return {"mode": "fit", "cx": 0.5, "why": "no face (screen/gameplay)"}


def video_filter(info: Dict[str, Any], frame: Dict[str, Any], out_w: int, out_h: int) -> str:
    """ffmpeg filter_complex video chain ending in an unlabeled stream (caller appends ass + format)."""
    sw, sh = info["width"], info["height"]
    fps = "fps=30" if (info.get("fps") or 30) > 31 else "null"
    if frame["mode"] == "fit":
        src_ar = sw / max(1, sh)
        fg_w = out_w
        fg_h = int(round(out_w / src_ar)) // 2 * 2
        if fg_h > out_h:
            fg_h, fg_w = out_h, int(round(out_h * src_ar)) // 2 * 2
        return (f"[0:v]{fps},split=2[a][b];"
                f"[a]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h},"
                f"boxblur=28:3,eq=brightness=-0.10:saturation=1.1[bg];"
                f"[b]scale={fg_w}:{fg_h}:flags=lanczos,unsharp=3:3:0.3:3:3:0[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    # crop: full height, 9:16 width, centred on cx (clamped inside the frame)
    target = out_w / out_h
    if sw / max(1, sh) > target:
        cw = int(sh * target) // 2 * 2
        x = int(round(frame["cx"] * sw - cw / 2))
        x = max(0, min(sw - cw, x))
        crop = f"crop={cw}:{sh}:{x}:0"
    else:
        ch = int(sw / target) // 2 * 2
        y = max(0, (sh - ch) // 2)
        crop = f"crop={sw}:{ch}:0:{y}"
    sharpen = "unsharp=5:5:0.45:5:5:0" if sh < 1000 else "unsharp=3:3:0.25:3:3:0"
    return f"[0:v]{fps},{crop},scale={out_w}:{out_h}:flags=lanczos,{sharpen},setsar=1"
