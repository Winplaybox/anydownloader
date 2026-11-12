"""Voice synthesis for the AI Video Editor.

Kokoro (local, free) is the primary engine; Edge-TTS (online, free) covers the
languages Kokoro can't speak and acts as fallback. Every call returns mono
float32 samples at 24 kHz, trimmed of leading/trailing silence, so the pipeline
can place lines precisely on its own timeline.
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
import threading
import urllib.request
from typing import Optional, Tuple

import numpy as np

from .options import LANG_BY_ID, VOICE_BY_ID

log = logging.getLogger("video_editor.tts")

SR = 24000
CACHE_DIR = os.environ.get("EDITOR_CACHE_DIR") or os.path.join(tempfile.gettempdir(), "wpb_editor_cache")
_MODEL_URL = os.environ.get(
    "KOKORO_MODEL_URL",
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx")
_VOICES_URL = os.environ.get(
    "KOKORO_VOICES_URL",
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")

_kokoro = None
_kokoro_lock = threading.Lock()


class TTSError(Exception):
    pass


def _download(url: str, dest: str) -> None:
    if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    log.info("downloading %s", url)
    req = urllib.request.Request(url, headers={"User-Agent": "wpb-video-editor"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dest)


def _get_kokoro():
    global _kokoro
    if _kokoro is not None:
        return _kokoro
    with _kokoro_lock:
        if _kokoro is None:
            from kokoro_onnx import Kokoro  # heavy import, lazy

            model = os.path.join(CACHE_DIR, "kokoro", os.path.basename(_MODEL_URL))
            voices = os.path.join(CACHE_DIR, "kokoro", os.path.basename(_VOICES_URL))
            _download(_MODEL_URL, model)
            _download(_VOICES_URL, voices)
            _kokoro = Kokoro(model, voices)
    return _kokoro


def _trim(samples: np.ndarray) -> np.ndarray:
    if samples.size == 0:
        return samples
    a = np.abs(samples)
    thr = max(1e-4, float(a.max()) * 0.03)
    idx = np.where(a > thr)[0]
    if idx.size == 0:
        return samples[:0]
    return samples[max(0, idx[0] - int(0.01 * SR)): idx[-1] + int(0.025 * SR)]


def _kokoro_speak(text: str, voice: str, lang_code: str, speed: float) -> np.ndarray:
    k = _get_kokoro()
    with _kokoro_lock:  # onnxruntime session is not guaranteed thread-safe; one line at a time
        samples, sr = k.create(text, voice=voice, speed=float(speed), lang=lang_code)
    samples = np.asarray(samples, dtype=np.float32)
    if sr != SR:
        samples = _resample(samples, sr, SR)
    return samples


def _resample(x: np.ndarray, src: int, dst: int) -> np.ndarray:
    if src == dst or x.size == 0:
        return x
    n = int(round(x.size * dst / src))
    return np.interp(np.linspace(0, x.size - 1, n), np.arange(x.size), x).astype(np.float32)


async def _edge_speak(text: str, voice: str, speed: float) -> np.ndarray:
    import edge_tts

    pct = int(round((speed - 1.0) * 100))
    rate = f"{'+' if pct >= 0 else ''}{pct}%"
    with tempfile.TemporaryDirectory() as td:
        mp3 = os.path.join(td, "v.mp3")
        wav = os.path.join(td, "v.wav")
        await edge_tts.Communicate(text, voice, rate=rate).save(mp3)
        if not os.path.exists(mp3) or os.path.getsize(mp3) < 500:
            raise TTSError("edge-tts returned no audio")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
        import soundfile as sf

        data, _ = sf.read(wav, dtype="float32")
    return np.asarray(data, dtype=np.float32)


async def speak(text: str, voice_id: str, lang: str, speed: float = 1.0) -> Tuple[np.ndarray, str]:
    """Return (samples@24k, engine_used). Falls back Kokoro -> Edge (same language)."""
    text = (text or "").strip()
    if not text:
        return np.zeros(0, dtype=np.float32), "none"
    voice = VOICE_BY_ID.get(voice_id)
    if not voice:
        raise TTSError(f"unknown voice {voice_id}")
    lang_info = LANG_BY_ID.get(lang) or {}

    if voice["engine"] == "kokoro":
        kl = {"hi": "hi", "en-us": "en-us", "en-gb": "en-gb", "es": "es", "fr": "fr-fr", "it": "it", "pt": "pt-br"}.get(voice["lang"], lang_info.get("kokoro"))
        try:
            s = await asyncio.to_thread(_kokoro_speak, text, voice_id, kl, speed)
            return _trim(s), "kokoro"
        except Exception as e:  # model download / phonemizer failure -> edge fallback
            log.warning("kokoro failed (%s); trying edge fallback", type(e).__name__)
            fallback = next((v["id"] for v in VOICE_BY_ID.values()
                             if v["engine"] == "edge" and v["lang"] == voice["lang"] and v["gender"] == voice["gender"]), None)
            fallback = fallback or next((v["id"] for v in VOICE_BY_ID.values()
                                         if v["engine"] == "edge" and v["lang"] == voice["lang"]), None)
            if not fallback:
                raise TTSError(f"Kokoro failed and no fallback voice: {e}") from e
            voice_id = fallback
    s = await _edge_speak(text, voice_id, speed)
    return _trim(s), "edge"


def warm_up() -> Optional[str]:
    """Download the Kokoro model ahead of the first job (called from a background task)."""
    try:
        _get_kokoro()
        return None
    except Exception as e:  # pragma: no cover - network
        return str(e)
