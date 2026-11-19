"""Ownership checks for private editor-job resources."""
from __future__ import annotations

import hmac
from typing import Any, Dict, Optional


def job_owner_matches(
    job: Dict[str, Any],
    identity: Dict[str, Any],
    fallback_key: Optional[str] = None,
) -> bool:
    owner = str(job.get("client") or "")
    if not owner:
        return False
    stable_ids = {
        str(identity.get("user_id") or "").strip(),
        str(identity.get("guest_id") or "").strip(),
    }
    stable_ids.discard("")
    if stable_ids:
        return any(hmac.compare_digest(owner, candidate) for candidate in stable_ids)
    return bool(fallback_key and hmac.compare_digest(owner, str(fallback_key)))
