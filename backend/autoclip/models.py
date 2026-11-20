"""Speech-model manager: lets users install a faster-whisper tier on the server once, then pick it per job.

faster-whisper models are multilingual, so one tier covers every language in config.LANGUAGES. Only an allowlist
of sizes is installable (tiny/base/small), one download at a time, with a disk-space guard, so this cannot be
used to fill the disk or fetch arbitrary files.
"""
from __future__ import annotations

import logging
import os
import shutil
import threading
import time
from typing import Any, Dict, Optional

from . import config

log = logging.getLogger("autoclip.models")
_lock = threading.Lock()
_state: Dict[str, Dict[str, Any]] = {}  # id -> {status: idle|downloading|error, error, started}
MIN_FREE_GB = 4


def _root() -> str:
    cache = os.environ.get("EDITOR_CACHE_DIR")
    return os.path.join(cache, "whisper") if cache else os.path.join(config.DATA_DIR, "whisper")


def installed(model_id: str) -> bool:
    if model_id not in config.STT_IDS:
        return False
    d = os.path.join(_root(), f"models--Systran--faster-whisper-{model_id}", "snapshots")
    try:
        for snap in os.listdir(d):
            if os.path.isfile(os.path.join(d, snap, "model.bin")):
                return True
    except OSError:
        pass
    return False


def listing() -> Dict[str, Any]:
    out = []
    for m in config.STT_MODELS:
        st = _state.get(m["id"], {})
        out.append({**m, "installed": installed(m["id"]), "status": st.get("status", "idle"),
                    "error": st.get("error")})
    try:
        import faster_whisper  # noqa: F401
        engine = True
    except ImportError:
        engine = False
    return {"engine": engine, "models": out, "default": os.environ.get("EDITOR_WHISPER_MODEL", "base")}


def _download(model_id: str) -> None:
    try:
        from faster_whisper.utils import download_model

        os.makedirs(_root(), exist_ok=True)
        download_model(model_id, cache_dir=_root())
        _state[model_id] = {"status": "idle"}
        log.info("installed whisper tier %s", model_id)
    except Exception as e:  # noqa: BLE001
        log.warning("whisper tier %s install failed: %s", model_id, type(e).__name__)
        _state[model_id] = {"status": "error", "error": "Download failed. Try again in a minute."}


def install(model_id: str) -> Dict[str, Any]:
    """Start a background download. Returns the new status. Raises ValueError with a user-safe message."""
    if model_id not in config.STT_IDS:
        raise ValueError("Unknown speech model.")
    if installed(model_id):
        return {"status": "installed"}
    os.makedirs(config.DATA_DIR, exist_ok=True)
    free_gb = shutil.disk_usage(config.DATA_DIR).free / 1e9
    if free_gb < MIN_FREE_GB:
        raise ValueError("The server is low on disk space. Try again later.")
    with _lock:
        if any(s.get("status") == "downloading" for s in _state.values()):
            raise ValueError("Another model is downloading. Wait for it to finish.")
        _state[model_id] = {"status": "downloading", "started": time.time()}
    threading.Thread(target=_download, args=(model_id,), daemon=True, name=f"stt-{model_id}").start()
    return {"status": "downloading"}
