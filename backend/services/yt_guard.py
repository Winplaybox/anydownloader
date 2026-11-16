"""
Circuit breaker for YouTube.

YouTube rate-limits datacenter IPs (HTTP 429 / "no player response"). Every extra attempt while we are
blocked makes it worse and makes users wait for nothing. After a few block errors in a row we stop
calling YouTube for a cooldown, answer instantly with a friendly error, then let one request probe again.
"""
from __future__ import annotations

import threading
import time

FAIL_THRESHOLD = 3
WINDOW_S = 300
BASE_COOLDOWN_S = 90
MAX_COOLDOWN_S = 900

_lock = threading.Lock()
_fails: list = []          # timestamps of recent block errors
_open_until = 0.0
_opens = 0                 # consecutive opens without a success (drives backoff)
_last_ok = 0.0
_last_fail = 0.0


def retry_after() -> int:
    """Seconds until YouTube may be tried again; 0 when requests are allowed."""
    with _lock:
        return max(0, int(_open_until - time.time()))


def failure() -> None:
    global _open_until, _opens, _last_fail
    now = time.time()
    with _lock:
        _last_fail = now
        _fails[:] = [t for t in _fails if now - t < WINDOW_S] + [now]
        if len(_fails) >= FAIL_THRESHOLD and now >= _open_until:
            _opens += 1
            _open_until = now + min(MAX_COOLDOWN_S, BASE_COOLDOWN_S * (2 ** (_opens - 1)))
            _fails.clear()


def success() -> None:
    global _open_until, _opens, _last_ok
    with _lock:
        _last_ok = time.time()
        _fails.clear()
        _opens = 0
        _open_until = 0.0


def state() -> dict:
    with _lock:
        now = time.time()
        return {
            "open": now < _open_until,
            "retry_after_s": max(0, int(_open_until - now)),
            "recent_failures": len(_fails),
            "consecutive_opens": _opens,
            "last_ok_ago_s": int(now - _last_ok) if _last_ok else None,
            "last_fail_ago_s": int(now - _last_fail) if _last_fail else None,
        }
