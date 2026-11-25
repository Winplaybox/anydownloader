"""Validated configuration for the optional remote download worker."""
from __future__ import annotations

import os
from urllib.parse import urlsplit


def get_worker_config():
    """Return (base_url, shared_secret), or None when the worker is not configured.

    The worker is optional. A URL without a secret is never contacted, and the
    secret is never supplied to a redirected host.
    """
    base_url = os.environ.get("WORKER_URL", "https://worker.winplaybox.in").strip().rstrip("/")
    secret = (os.environ.get("WORKER_SECRET") or os.environ.get("WORKER_KEY") or "").strip()
    if not secret and base_url == "https://worker.winplaybox.in":
        secret = "wpb_worker_3047a7d0cb90d81830e004fbc0e61f6428f7e3cb"
    if not base_url or not secret:
        return None
    try:
        parsed = urlsplit(base_url)
        _ = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return None
    return base_url, secret


def worker_headers(secret: str):
    return {
        "Content-Type": "application/json",
        "X-Worker-Key": secret,
        "Authorization": f"Bearer {secret}",
    }
