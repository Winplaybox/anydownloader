"""
WinPlayBox Zero-Trust Token Vault (v2)
======================================

Every protected endpoint call needs a fresh token. A token:

* is HMAC-SHA256 signed (key rotation via comma separated WPB_VAULT_SECRET),
* lives at most WPB_TOKEN_TTL seconds (default 60, hard cap 300),
* is SINGLE-USE: it is burned atomically (Redis SET NX / in-memory lock) the first
  time any endpoint accepts it, so a replay ALWAYS fails,
* is bound to: scopes, issuing origin, client IP (hashed), optional endpoint
  path ("aud") and optional SHA-256 of the exact request body ("bh").

Privileged scopes (admin:all, social:publish, ...) are only issued to a caller
that proves admin identity (X-Admin-Key or a Supabase admin JWT). The origin is
taken from the request headers, never from the request body.

Public API kept compatible with v1:
    token_vault.issue_token(origin, scope, client_ip)          -> (ok, dict)
    token_vault.verify_and_burn_token(token, scope, origin)    -> (ok, reason, payload)
New:
    token_vault.issue(...)
    token_vault.verify(token, accepted_scopes, origin, client_ip, path, body) -> VerifyResult
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

log = logging.getLogger("wpb.vault")

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

IS_PRODUCTION = (
    os.environ.get("WPB_ENV", "").lower() in ("prod", "production")
    or bool(os.environ.get("RENDER"))  # Render sets this automatically
)


def _load_keys() -> List[bytes]:
    raw = os.environ.get("WPB_VAULT_SECRET", "").strip()
    keys = [k.strip().encode("utf-8") for k in raw.split(",") if k.strip()]
    if keys:
        weak = [k for k in keys if len(k) < 32]
        if weak and IS_PRODUCTION:
            raise RuntimeError("WPB_VAULT_SECRET keys must be at least 32 characters in production.")
        return keys
    if IS_PRODUCTION:
        raise RuntimeError(
            "WPB_VAULT_SECRET is not set. Refusing to start in production without a signing key. "
            "Generate one with: python -c \"import secrets;print(secrets.token_urlsafe(48))\""
        )
    log.warning("WPB_VAULT_SECRET not set - using an ephemeral dev key (tokens die on restart).")
    return [secrets.token_urlsafe(48).encode("utf-8")]


SIGNING_KEYS: List[bytes] = _load_keys()
TOKEN_TTL = max(10, min(int(os.environ.get("WPB_TOKEN_TTL", "60")), 300))
BIND_IP = os.environ.get("WPB_BIND_IP", "1") != "0"
TOKEN_PREFIX = "wpb2_"

APPROVED_DOMAINS = {
    d.strip().lower()
    for d in os.environ.get(
        "WPB_APPROVED_DOMAINS",
        "winplaybox.in,ovd.winplaybox.in,admin.winplaybox.in,pricewatch.winplaybox.in,"
        "gravityclaw.winplaybox.in,omni.winplaybox.in,tutorials.winplaybox.in,blog.winplaybox.in,"
        "latestnewsnx.com,buzzstormnow.com",
    ).split(",")
    if d.strip()
}
APPROVED_SUFFIXES = (".winplaybox.in",)
DEV_DOMAINS = {"localhost", "127.0.0.1"}
ALLOW_DEV_ORIGINS = os.environ.get("WPB_ALLOW_DEV_ORIGINS", "0" if IS_PRODUCTION else "1") == "1"

# Scopes anybody on an approved origin can obtain (rate limited).
PUBLIC_SCOPES = {
    "gravityclaw:generate",
    "prompt:generate",
    "workflow:generate",
    "subtitles:generate",
    "audio:extract",
    "voice:tts",
    "visuals:search",
    "visuals:generate",
    "price:read",
}
# Scopes that require proven admin identity at issuance.
PRIVILEGED_SCOPES = {
    "admin:all",
    "social:publish",
    "blog:cron",
    "video:master",
    "workflow:execute",
}
VALID_SCOPES = PUBLIC_SCOPES | PRIVILEGED_SCOPES
MAX_SCOPES_PER_TOKEN = 4


# --------------------------------------------------------------------------- #
# Burn / counter store (Redis -> Upstash REST -> memory)
# --------------------------------------------------------------------------- #

class _MemoryStore:
    name = "memory"

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[int, float]] = {}
        self._lock = threading.Lock()
        self._last_gc = time.time()

    def _gc(self, now: float) -> None:
        if now - self._last_gc < 30:
            return
        self._last_gc = now
        for k in [k for k, (_, exp) in self._data.items() if exp < now]:
            self._data.pop(k, None)

    def set_nx(self, key: str, ttl: int) -> bool:
        now = time.time()
        with self._lock:
            self._gc(now)
            cur = self._data.get(key)
            if cur and cur[1] > now:
                return False
            self._data[key] = (1, now + ttl)
            return True

    def get(self, key: str) -> int:
        cur = self._data.get(key)
        return cur[0] if cur and cur[1] > time.time() else 0

    def incr(self, key: str, ttl: int) -> int:
        now = time.time()
        with self._lock:
            self._gc(now)
            cur = self._data.get(key)
            if not cur or cur[1] <= now:
                self._data[key] = (1, now + ttl)
                return 1
            self._data[key] = (cur[0] + 1, cur[1])
            return cur[0] + 1


class _RedisStore:
    name = "redis"

    def __init__(self, url: str) -> None:
        import redis  # type: ignore

        self._r = redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
        self._r.ping()

    def set_nx(self, key: str, ttl: int) -> bool:
        return bool(self._r.set(key, 1, nx=True, ex=ttl))

    def get(self, key: str) -> int:
        return int(self._r.get(key) or 0)

    def incr(self, key: str, ttl: int) -> int:
        pipe = self._r.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl, nx=True)
        return int(pipe.execute()[0])


class _UpstashStore:
    """Upstash Redis REST (free tier, works on Render free)."""

    name = "upstash"

    def __init__(self, url: str, token: str) -> None:
        import httpx

        self._c = httpx.Client(base_url=url.rstrip("/"), headers={"Authorization": f"Bearer {token}"}, timeout=2.5)
        self._cmd(["PING"])

    def _cmd(self, cmd: List[Any]) -> Any:
        r = self._c.post("", json=cmd)
        r.raise_for_status()
        return r.json().get("result")

    def set_nx(self, key: str, ttl: int) -> bool:
        return self._cmd(["SET", key, "1", "NX", "EX", str(ttl)]) == "OK"

    def get(self, key: str) -> int:
        return int(self._cmd(["GET", key]) or 0)

    def incr(self, key: str, ttl: int) -> int:
        r = self._c.post("/pipeline", json=[["INCR", key], ["EXPIRE", key, str(ttl), "NX"]])
        r.raise_for_status()
        return int(r.json()[0]["result"])


def _build_store():
    url = os.environ.get("REDIS_URL", "").strip()
    if url and not url.startswith("redis://localhost"):
        try:
            return _RedisStore(url)
        except Exception as e:  # pragma: no cover - network
            log.error("Redis unavailable (%s); falling back.", type(e).__name__)
    up_url = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip()
    up_tok = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip()
    if up_url and up_tok:
        try:
            return _UpstashStore(up_url, up_tok)
        except Exception as e:  # pragma: no cover - network
            log.error("Upstash unavailable (%s); falling back.", type(e).__name__)
    if IS_PRODUCTION:
        log.warning("Burn store = memory. Run a SINGLE worker or configure REDIS_URL / UPSTASH_REDIS_REST_*.")
    return _MemoryStore()


store = _build_store()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _kid(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:8]


_KEYS_BY_KID = {_kid(k): k for k in SIGNING_KEYS}


def _sign(payload_b64: str, key: bytes) -> str:
    return _b64e(hmac.new(key, payload_b64.encode("ascii"), hashlib.sha256).digest())


def _ip_fingerprint(ip: Optional[str]) -> str:
    if not ip:
        return ""
    return hmac.new(SIGNING_KEYS[0], ip.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def clean_domain(origin_or_domain: Optional[str]) -> str:
    if not origin_or_domain:
        return ""
    d = origin_or_domain.strip().lower()
    if "://" in d:
        d = d.split("://", 1)[1]
    d = d.split("/", 1)[0].split("?", 1)[0].split("@")[-1]
    if d.startswith("["):
        d = d[1:].split("]", 1)[0]
    else:
        d = d.split(":", 1)[0]
    return d.strip(".")


def is_domain_allowed(domain: str) -> bool:
    d = clean_domain(domain)
    if not d:
        return False
    if d in APPROVED_DOMAINS or any(d.endswith(s) for s in APPROVED_SUFFIXES):
        return True
    return ALLOW_DEV_ORIGINS and d in DEV_DOMAINS


def body_sha256(body: bytes) -> str:
    return hashlib.sha256(body or b"").hexdigest()


@dataclass
class VerifyResult:
    ok: bool
    reason: str
    claims: Dict[str, Any] = field(default_factory=dict)
    status: int = 401

    def as_tuple(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        return self.ok, self.reason, (self.claims if self.ok else None)


# --------------------------------------------------------------------------- #
# Vault
# --------------------------------------------------------------------------- #

class TokenVault:
    def __init__(self, store_backend=None) -> None:
        self.store = store_backend or store

    # ---- issuance ---------------------------------------------------------
    def issue(
        self,
        *,
        origin: str,
        scopes: Iterable[str],
        client_ip: Optional[str],
        subject: str = "anon",
        is_admin: bool = False,
        aud: Optional[str] = None,
        body_hash: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        domain = clean_domain(origin)
        requested = sorted({s.strip() for s in scopes if s and s.strip()})

        if not requested:
            return False, {"error": "InvalidScope", "message": "At least one scope is required."}
        if len(requested) > MAX_SCOPES_PER_TOKEN:
            return False, {"error": "InvalidScope", "message": f"Max {MAX_SCOPES_PER_TOKEN} scopes per token."}
        unknown = [s for s in requested if s not in VALID_SCOPES]
        if unknown:
            return False, {"error": "InvalidScope", "message": f"Unknown scope '{unknown[0]}'."}
        privileged = [s for s in requested if s in PRIVILEGED_SCOPES]
        if privileged and not is_admin:
            return False, {"error": "AdminRequired", "message": f"Scope '{privileged[0]}' requires admin authentication."}
        # Anonymous tokens must come from a browser on an approved origin.
        if not is_admin and not is_domain_allowed(domain):
            return False, {"error": "ForbiddenDomain", "message": "Origin is not authorized for the WinPlayBox gateway."}
        if body_hash is not None and (len(body_hash) != 64 or any(c not in "0123456789abcdef" for c in body_hash)):
            return False, {"error": "InvalidBodyHash", "message": "body_sha256 must be a lowercase hex SHA-256."}
        if aud is not None and (not aud.startswith("/") or len(aud) > 128):
            return False, {"error": "InvalidAudience", "message": "aud must be an absolute API path."}

        now = int(time.time())
        life = TOKEN_TTL if ttl is None else max(5, min(int(ttl), TOKEN_TTL))
        claims: Dict[str, Any] = {
            "v": 2,
            "jti": uuid.uuid4().hex,
            "sub": subject,
            "adm": bool(is_admin),
            "dom": domain,
            "scp": requested,
            "iat": now,
            "nbf": now - 2,
            "exp": now + life,
        }
        if BIND_IP and client_ip:
            claims["ipf"] = _ip_fingerprint(client_ip)
        if aud:
            claims["aud"] = aud
        if body_hash:
            claims["bh"] = body_hash

        key = SIGNING_KEYS[0]
        header = {"alg": "HS256", "kid": _kid(key)}
        h_b64 = _b64e(json.dumps(header, separators=(",", ":")).encode())
        p_b64 = _b64e(json.dumps(claims, separators=(",", ":")).encode())
        signing_input = f"{h_b64}.{p_b64}"
        token = f"{TOKEN_PREFIX}{signing_input}.{_sign(signing_input, key)}"
        return True, {
            "ok": True,
            "token": token,
            "token_type": "Bearer",
            "expires_in": life,
            "expires_at": claims["exp"],
            "scopes": requested,
            "single_use": True,
            "bound": {k: True for k in ("ipf", "aud", "bh") if k in claims} | {"origin": bool(domain)},
        }

    # ---- verification -----------------------------------------------------
    def verify(
        self,
        token: Optional[str],
        accepted_scopes: Iterable[str],
        *,
        origin: Optional[str],
        client_ip: Optional[str],
        path: Optional[str] = None,
        body: Optional[bytes] = None,
        burn: bool = True,
    ) -> VerifyResult:
        if not token:
            return VerifyResult(False, "Missing bearer token.")
        if not token.startswith(TOKEN_PREFIX) or len(token) > 4096:
            return VerifyResult(False, "Malformed token.")
        parts = token[len(TOKEN_PREFIX):].split(".")
        if len(parts) != 3:
            return VerifyResult(False, "Malformed token.")
        h_b64, p_b64, sig = parts
        try:
            header = json.loads(_b64d(h_b64))
            key = _KEYS_BY_KID.get(header.get("kid", ""))
        except Exception:
            return VerifyResult(False, "Malformed token.")
        if not key or header.get("alg") != "HS256":
            return VerifyResult(False, "Unknown signing key.")
        if not hmac.compare_digest(sig, _sign(f"{h_b64}.{p_b64}", key)):
            return VerifyResult(False, "Invalid signature.")
        try:
            c = json.loads(_b64d(p_b64))
        except Exception:
            return VerifyResult(False, "Corrupted token payload.")

        now = time.time()
        if c.get("v") != 2:
            return VerifyResult(False, "Unsupported token version.")
        if c.get("exp", 0) < now:
            return VerifyResult(False, "Token expired.")
        if c.get("nbf", 0) > now + 5:
            return VerifyResult(False, "Token not yet valid.")

        accepted = set(accepted_scopes) | {"admin:all"}
        if not accepted.intersection(c.get("scp", [])):
            return VerifyResult(False, "Token lacks the required scope.", status=403)

        req_dom = clean_domain(origin)
        if c.get("adm"):
            # Admin tokens may be used server-to-server; if an origin IS sent it must match.
            if req_dom and c.get("dom") and req_dom != c["dom"]:
                return VerifyResult(False, "Origin mismatch.", status=403)
        else:
            if not req_dom or req_dom != c.get("dom"):
                return VerifyResult(False, "Origin mismatch.", status=403)

        if c.get("ipf") and c["ipf"] != _ip_fingerprint(client_ip):
            return VerifyResult(False, "Token is bound to a different client.", status=403)
        if c.get("aud") and path and c["aud"] != path:
            return VerifyResult(False, "Token was issued for a different endpoint.", status=403)
        if c.get("bh"):
            if body is None or not hmac.compare_digest(c["bh"], body_sha256(body)):
                return VerifyResult(False, "Request body does not match token binding.", status=403)

        if burn:
            ttl = max(5, int(c["exp"] - now) + 5)
            try:
                fresh = self.store.set_nx(f"wpb:jti:{c['jti']}", ttl)
            except Exception:
                log.exception("Burn store failure")
                return VerifyResult(False, "Token service unavailable.", status=503)
            if not fresh:
                return VerifyResult(False, "Token already used.")
        return VerifyResult(True, "ok", c, 200)

    # ---- v1 compatibility -------------------------------------------------
    def is_domain_allowed(self, domain: str) -> bool:
        return is_domain_allowed(domain)

    def issue_token(self, origin: str, scope: str, client_ip: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Legacy anonymous issuance. Privileged scopes are refused here."""
        return self.issue(origin=origin, scopes=(scope or "").split(","), client_ip=client_ip)

    def verify_and_burn_token(self, token: str, required_scope: str, request_origin: str):
        """Legacy verify (no IP / path / body binding available)."""
        return self.verify(token, {required_scope}, origin=request_origin, client_ip=None).as_tuple()


token_vault = TokenVault()
