"""Speech-to-text for the original audio (faster-whisper, local, free).

Used for two things:
  * "original" mode: captions are built from the real spoken words.
  * AI modes: the transcript is given to the planner so the script respects what
    is actually said/heard in the clip.
Optional dependency: if faster-whisper isn't installed the pipeline still works
for AI voiceover modes (it just plans from frames + the user's brief).
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional

log = logging.getLogger("video_editor.transcribe")

_MODEL_SIZE = os.environ.get("EDITOR_WHISPER_MODEL", "base")
_model = None
_lock = threading.Lock()


def available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from faster_whisper import WhisperModel

                cache = os.environ.get("EDITOR_CACHE_DIR")
                _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8",
                                      download_root=os.path.join(cache, "whisper") if cache else None)
    return _model


def transcribe(wav16k_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Returns {"language", "text", "words":[{w,s,e}], "speech_seconds"}; empty on failure."""
    empty: Dict[str, Any] = {"language": language, "text": "", "words": [], "speech_seconds": 0.0}
    if not available():
        return empty
    wl = (language or "").split("-")[0] or None
    try:
        model = _get_model()
        with _lock:
            segs, info = model.transcribe(wav16k_path, language=wl, word_timestamps=True, vad_filter=True,
                                          beam_size=1, condition_on_previous_text=False)
            words: List[Dict[str, Any]] = []
            texts: List[str] = []
            speech = 0.0
            for s in segs:
                if getattr(s, "no_speech_prob", 0) > 0.7:
                    continue
                texts.append(s.text.strip())
                speech += max(0.0, s.end - s.start)
                for w in (s.words or []):
                    t = (w.word or "").strip()
                    if t:
                        words.append({"w": t, "s": round(float(w.start), 3), "e": round(float(w.end), 3)})
        return {"language": info.language, "text": " ".join(texts).strip(), "words": words,
                "speech_seconds": round(speech, 2)}
    except Exception as e:
        log.warning("transcription failed: %s", e)
        return empty
