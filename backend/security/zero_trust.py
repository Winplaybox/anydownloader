"""
WinPlayBox Zero-Trust request layer.

* `client_ip(request)` / `request_origin(request)`  - trusted extraction
* `authenticate_admin(request)`                     - X-Admin-Key or Supabase admin JWT
* `rate_limit(bucket, key, limit, window)`          - Redis/Upstash/memory counters
* `issue_token_endpoint(request)`                   - POST /api/v1|v2/auth/token
* `@require_token(scopes, ...)`                     - decorator for protected handlers
* `verify_request(request, scopes)`                 - for legacy handlers (await)
* `ZeroTrustMiddleware`                             - headers, admin path guard, body limit, request id
* `cors_kwargs()`                                   - strict CORS config
"""

from __future__ import annotations

import asyncio
import base64
import functools
import hashlib
import hmac
import json
import logging
import os
import re
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

try:
    from backend.security.token_vault import (
        IS_PRODUCTION, PRIVILEGED_SCOPES, VALID_SCOPES, body_sha256, clean_domain, store, token_vault,
    )
except (ModuleNotFoundError, ImportError):
    from security.token_vault import (  # type: ignore
        IS_PRODUCTION, PRIVILEGED_SCOPES, VALID_SCOPES, body_sha256, clean_domain, store, token_vault,
    )

log = logging.getLogger("wpb.zero_trust")

# Trust forwarded client-IP headers only when the deployment proxy is configured to overwrite them.
TRUST_PROXY = os.environ.get("WPB_TRUST_PROXY", "0") == "1"
ADMIN_KEY = (os.environ.get("WPB_ADMIN_KEY") or os.environ.get("ADMIN_API_KEY") or "").strip()
if ADMIN_KEY and len(ADMIN_KEY) < 32:
    log.error("WPB_ADMIN_KEY shorter than 32 chars - admin key auth DISABLED.")
    ADMIN_KEY = ""
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
ADMIN_EMAILS = {e.strip().lower() for e in os.environ.get("WPB_ADMIN_EMAILS", "").split(",") if e.strip()}
TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET_KEY", "").strip()
TURNSTILE_REQUIRED = os.environ.get("WPB_TURNSTILE_REQUIRED", "0") == "1" and bool(TURNSTILE_SECRET)

MAX_BODY_BYTES = int(os.environ.get("WPB_MAX_BODY_BYTES", str(256 * 1024)))
ISSUE_LIMIT_PER_MIN = int(os.environ.get("WPB_ISSUE_LIMIT_PER_MIN", "40"))
ADMIN_FAIL_LIMIT = 5          # per 15 minutes per IP
ADMIN_ONLY_PATH_PREFIXES = ("/admin/", "/api/v1/system/")


# --------------------------------------------------------------------------- #
# Request facts
# --------------------------------------------------------------------------- #

def client_ip(request: Request) -> str:
    if TRUST_PROXY:
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            return xff.split(",")[0].strip()
        real = request.headers.get("x-real-ip") or request.headers.get("cf-connecting-ip")
        if real:
            return real.strip()
    return request.client.host if request.client else "unknown"


def request_origin(request: Request) -> str:
    """Origin header (browser-controlled), falling back to Referer. Never the body."""
    return request.headers.get("origin") or request.headers.get("referer") or ""


def request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = uuid.uuid4().hex[:16]
        request.state.request_id = rid
    return rid


def error(request: Request, status: int, code: str, message: str, **extra: Any) -> JSONResponse:
    payload = {"ok": False, "error": {"code": code, "message": message, **extra}, "request_id": request_id(request)}
    return JSONResponse(payload, status_code=status, headers={"Cache-Control": "no-store"})


def bearer(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip()
    return request.headers.get("x-auth-token", "").strip()


# --------------------------------------------------------------------------- #
# Rate limiting
# --------------------------------------------------------------------------- #

def rate_limit(bucket: str, key: str, limit: int, window: int) -> Tuple[bool, int]:
    """Fixed-window counter. Returns (allowed, remaining)."""
    win = int(time.time() // window)
    k = f"wpb:rl:{bucket}:{hashlib.sha256(key.encode()).hexdigest()[:24]}:{win}"
    try:
        n = store.incr(k, window + 1)
    except Exception:
        log.exception("rate limiter store failure")
        # Production defaults to fail-closed; development remains fail-open.
        fail_open_default = "0" if IS_PRODUCTION else "1"
        fail_open = os.environ.get("WPB_RATE_LIMIT_FAIL_OPEN", fail_open_default) == "1"
        return (True, limit) if fail_open else (False, 0)
    return n <= limit, max(0, limit - n)


async def _arate(bucket: str, key: str, limit: int, window: int) -> Tuple[bool, int]:
    return await asyncio.to_thread(rate_limit, bucket, key, limit, window)


def _fail_key(ip: str) -> str:
    return f"wpb:adminfail:{hashlib.sha256(ip.encode()).hexdigest()[:24]}"


def admin_locked(ip: str) -> bool:
    try:
        return store.get(_fail_key(ip)) >= ADMIN_FAIL_LIMIT
    except Exception:
        return False


def record_admin_failure(ip: str) -> None:
    try:
        store.incr(_fail_key(ip), 900)
    except Exception:
        log.exception("admin failure counter error")


# --------------------------------------------------------------------------- #
# Admin authentication
# --------------------------------------------------------------------------- #

def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _verify_supabase_jwt(jwt: str) -> Optional[str]:
    """HS256 Supabase access token -> admin email (or None)."""
    if not SUPABASE_JWT_SECRET or not ADMIN_EMAILS or jwt.count(".") != 2:
        return None
    try:
        h, p, s = jwt.split(".")
        header = json.loads(_b64d(h))
        if header.get("alg") != "HS256":
            return None
        expected = base64.urlsafe_b64encode(
            hmac.new(SUPABASE_JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        ).decode().rstrip("=")
        if not hmac.compare_digest(expected, s):
            return None
        claims = json.loads(_b64d(p))
        if claims.get("exp", 0) < time.time() or claims.get("aud") != "authenticated":
            return None
        email = (claims.get("email") or "").lower()
        return email if email in ADMIN_EMAILS else None
    except Exception:
        return None


def authenticate_admin(request: Request, allow_bearer_jwt: bool = True) -> Optional[str]:
    """Returns an admin subject id, or None."""
    key = request.headers.get("x-admin-key", "")
    if key and ADMIN_KEY and hmac.compare_digest(key.encode(), ADMIN_KEY.encode()):
        return "admin:key"
    if allow_bearer_jwt:
        tok = bearer(request)
        if tok and not tok.startswith("wpb"):
            email = _verify_supabase_jwt(tok)
            if email:
                return f"admin:{email}"
    return None


def admin_auth_attempted(request: Request) -> bool:
    t = bearer(request)
    return bool(request.headers.get("x-admin-key") or (t and not t.startswith("wpb")))


# --------------------------------------------------------------------------- #
# Turnstile (optional bot protection for anonymous issuance)
# --------------------------------------------------------------------------- #

async def _turnstile_ok(token: str, ip: str) -> bool:
    if not token:
        return False
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={"secret": TURNSTILE_SECRET, "response": token, "remoteip": ip},
            )
            return bool(r.json().get("success"))
    except Exception:
        log.warning("turnstile verification failed (network)")
        return False


# --------------------------------------------------------------------------- #
# Token issuance endpoint
# --------------------------------------------------------------------------- #

async def issue_token_endpoint(request: Request) -> Response:
    """
    POST /api/v2/auth/token   (also mounted on /api/v1/auth/token)
    body: {
      "scope": "gravityclaw:generate" | ["a","b"],
      "aud": "/api/v2/gravityclaw/generate",     # optional endpoint binding
      "body_sha256": "<hex>",                    # optional exact-body binding
      "turnstile_token": "..."                   # when Turnstile is enforced
    }
    Admin: add header X-Admin-Key: <key>  or  Authorization: Bearer <supabase admin JWT>
    NOTE: "origin" in the body is ignored. The Origin header is used.
    """
    ip = client_ip(request)
    ok, _ = await _arate("issue", ip, ISSUE_LIMIT_PER_MIN, 60)
    if not ok:
        return error(request, 429, "RateLimited", "Too many token requests. Slow down.")

    raw = await request.body()
    if len(raw) > 8 * 1024:
        return error(request, 413, "PayloadTooLarge", "Token request too large.")
    try:
        body = json.loads(raw or b"{}")
        if not isinstance(body, dict):
            raise ValueError
    except Exception:
        return error(request, 400, "BadJSON", "Body must be a JSON object.")

    scope = body.get("scope") or body.get("scopes") or ""
    scopes = scope if isinstance(scope, list) else str(scope).split(",")
    scopes = [str(s).strip() for s in scopes if str(s).strip()]

    subject, is_admin = "anon", False
    if admin_auth_attempted(request):
        if await asyncio.to_thread(admin_locked, ip):
            return error(request, 429, "RateLimited", "Too many failed admin attempts. Try again in 15 minutes.")
        sub = authenticate_admin(request)
        if not sub:
            await asyncio.to_thread(record_admin_failure, ip)
            return error(request, 401, "AdminAuthFailed", "Invalid admin credentials.")
        subject, is_admin = sub, True

    if not is_admin and TURNSTILE_REQUIRED:
        tt = body.get("turnstile_token") or request.headers.get("cf-turnstile-response", "")
        if not await _turnstile_ok(tt, ip):
            return error(request, 403, "BotCheckFailed", "Human verification failed.")

    ok, res = token_vault.issue(
        origin=request_origin(request),
        scopes=scopes,
        client_ip=ip,
        subject=subject,
        is_admin=is_admin,
        aud=body.get("aud"),
        body_hash=(body.get("body_sha256") or None),
    )
    if not ok:
        status = 401 if res.get("error") == "AdminRequired" else 403 if res.get("error") == "ForbiddenDomain" else 400
        return error(request, status, res["error"], res["message"])
    res["request_id"] = request_id(request)
    return JSONResponse(res, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #

async def verify_request(request: Request, scopes: Iterable[str], *, bind_path: bool = True):
    """Verify + burn the bearer token of this request. Returns VerifyResult."""
    body = await request.body()  # Starlette caches; handler can still call request.json()
    return await asyncio.to_thread(
        token_vault.verify,
        bearer(request),
        set(scopes),
        origin=request_origin(request),
        client_ip=client_ip(request),
        path=request.url.path if bind_path else None,
        body=body,
    )


async def legacy_verify(request: Request, *scopes: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Drop-in for the old double verify_and_burn_token() pattern in main.py."""
    res = await verify_request(request, scopes)
    return res.as_tuple()


Handler = Callable[[Request], Awaitable[Response]]


def require_token(
    scopes: Iterable[str],
    *,
    rate: Optional[Tuple[str, int, int]] = None,
    daily: Optional[int] = None,
    max_body: int = MAX_BODY_BYTES,
) -> Callable[[Handler], Handler]:
    """Decorator: size limit -> rate limit -> verify+burn token -> handler(request).
    Claims are available at request.state.claims."""
    scope_set = set(scopes)

    def deco(fn: Handler) -> Handler:
        @functools.wraps(fn)
        async def wrapper(request: Request) -> Response:
            cl = request.headers.get("content-length")
            if cl and cl.isdigit() and int(cl) > max_body:
                return error(request, 413, "PayloadTooLarge", f"Body exceeds {max_body} bytes.")
            body = await request.body()
            if len(body) > max_body:
                return error(request, 413, "PayloadTooLarge", f"Body exceeds {max_body} bytes.")

            res = await verify_request(request, scope_set)
            if not res.ok:
                return error(request, res.status, "Unauthorized" if res.status == 401 else "Forbidden", res.reason)
            claims = res.claims
            request.state.claims = claims

            if not claims.get("adm"):
                ident = client_ip(request)
                if rate:
                    bucket, limit, window = rate
                    ok, remaining = await _arate(bucket, ident, limit, window)
                    if not ok:
                        return error(request, 429, "RateLimited", f"Limit {limit}/{window}s reached.")
                if daily:
                    ok, _ = await _arate(f"{(rate or ('d',))[0]}:day", ident, daily, 86400)
                    if not ok:
                        return error(request, 429, "DailyLimit", f"Daily limit of {daily} reached.")
            return await fn(request)

        wrapper.__wpb_scopes__ = scope_set  # type: ignore[attr-defined]
        return wrapper

    return deco


# --------------------------------------------------------------------------- #
# Middleware + CORS
# --------------------------------------------------------------------------- #

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Resource-Policy": "cross-origin",
}


class ZeroTrustMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id", "")
        request.state.request_id = rid if re.fullmatch(r"[A-Za-z0-9_-]{8,64}", rid or "") else uuid.uuid4().hex[:16]
        path = request.url.path

        if request.method != "OPTIONS":
            cl = request.headers.get("content-length")
            max_body = 50 * 1024 * 1024
            if path == "/api/temp-media":  # automation video uploads; the route enforces TEMP_MEDIA_MAX_MB
                max_body = (int(os.environ.get("TEMP_MEDIA_MAX_MB", "300")) + 1) * 1024 * 1024
            if path == "/api/editor/jobs":  # video uploads; the route enforces its own exact limit
                max_body = (int(os.environ.get("EDITOR_MAX_UPLOAD_MB", "100")) + 1) * 1024 * 1024
            if cl and cl.isdigit() and int(cl) > max_body:
                return error(request, 413, "PayloadTooLarge", "Request too large.")
            if path.startswith(ADMIN_ONLY_PATH_PREFIXES):
                ip = client_ip(request)
                if await asyncio.to_thread(admin_locked, ip):
                    return error(request, 429, "RateLimited", "Too many failed admin attempts.")
                if not authenticate_admin(request):
                    await asyncio.to_thread(record_admin_failure, ip)
                    return error(request, 401, "AdminAuthRequired", "Admin authentication required.")

        start = time.perf_counter()
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if IS_PRODUCTION:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        response.headers["X-Request-ID"] = request.state.request_id
        if path.startswith(("/api/v1/auth", "/api/v2/auth")):
            response.headers["Cache-Control"] = "no-store"
        log.info(json.dumps({
            "rid": request.state.request_id, "m": request.method, "p": path,
            "s": response.status_code, "ms": round((time.perf_counter() - start) * 1000, 1),
        }))
        return response


def cors_kwargs() -> Dict[str, Any]:
    extra = [o.strip() for o in os.environ.get("WPB_CORS_EXTRA_ORIGINS", "").split(",") if o.strip()]
    pattern = r"https://([a-z0-9-]+\.)*winplaybox\.in|https://(www\.)?latestnewsnx\.com|https://(www\.)?buzzstormnow\.com|chrome-extension://[a-z0-9]{32}|moz-extension://.*"
    if not IS_PRODUCTION or os.environ.get("WPB_ALLOW_DEV_ORIGINS") == "1":
        pattern += r"|http://(localhost|127\.0\.0\.1)(:\d+)?"
    return {
        "allow_origins": extra,
        "allow_origin_regex": pattern,
        "allow_methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "X-Admin-Key", "X-Request-ID",
                          "X-Extension-Key", "X-Auth-Token", "cf-turnstile-response", "x-guest-id", "X-Guest-ID",
                          "x-ovd-source", "x-ovd-medium", "x-ovd-channel", "x-ovd-referrer",
                          "X-OVD-Source", "X-OVD-Medium", "X-OVD-Channel", "X-OVD-Referrer"],
        "expose_headers": ["X-Request-ID"],
        "allow_credentials": True,
        "max_age": 600,
    }


__all__ = [
    "authenticate_admin", "bearer", "client_ip", "cors_kwargs", "error", "issue_token_endpoint",
    "legacy_verify", "rate_limit", "request_id", "request_origin", "require_token", "verify_request",
    "ZeroTrustMiddleware", "VALID_SCOPES", "PRIVILEGED_SCOPES", "body_sha256", "clean_domain",
]
