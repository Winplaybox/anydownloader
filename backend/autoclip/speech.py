"""Word-level speech-to-text with progress. Reuses the API's shared faster-whisper model
(one copy in RAM for Editor + AutoClip) unless AUTOCLIP_WHISPER_MODEL asks for a different size."""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Callable, Dict, List, Optional

from . import config

try:
    from backend.services.video_editor import transcribe as _ed_tr
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services.video_editor import transcribe as _ed_tr  # type: ignore

log = logging.getLogger("autoclip.speech")
_own_model = None
_own_lock = threading.Lock()


def available() -> bool:
    return _ed_tr.available()


def _model():
    want = config.WHISPER_MODEL.strip()
    if not want or want == os.environ.get("EDITOR_WHISPER_MODEL", "base"):
        return _ed_tr._get_model(), _ed_tr._lock
    global _own_model
    if _own_model is None:
        with _own_lock:
            if _own_model is None:
                from faster_whisper import WhisperModel

                cache = os.environ.get("EDITOR_CACHE_DIR")
                _own_model = WhisperModel(want, device="cpu", compute_type="int8",
                                          download_root=os.path.join(cache, "whisper") if cache else None)
    return _own_model, _own_lock


def transcribe(wav16k: str, duration: float, language: Optional[str] = None,
               progress: Optional[Callable[[float], bool]] = None) -> Dict[str, Any]:
    """Returns {language, words:[{w,s,e}], text}. progress(frac) returning False aborts (cancel)."""
    if not available():
        log.warning("faster-whisper not installed; clips will be picked by loudness only")
        return {"language": language, "words": [], "text": ""}
    model, lock = _model()
    lang = None if (not language or language == "auto") else language.split("-")[0]
    words: List[Dict[str, Any]] = []
    texts: List[str] = []
    with lock:
        segs, info = model.transcribe(wav16k, language=lang, word_timestamps=True, vad_filter=True,
                                      beam_size=1, condition_on_previous_text=False)
        for s in segs:  # generator: decoding happens while we iterate
            if progress and duration > 0 and progress(min(1.0, float(s.end) / duration)) is False:
                raise InterruptedError("cancelled")
            if getattr(s, "no_speech_prob", 0) > 0.75:
                continue
            texts.append(s.text.strip())
            for w in (s.words or []):
                t = (w.word or "").strip()
                if t:
                    words.append({"w": t, "s": round(float(w.start), 3), "e": round(float(w.end), 3)})
    return {"language": getattr(info, "language", lang), "words": words, "text": " ".join(texts).strip()}
