"""Authentication & Session HTTP routes."""
from __future__ import annotations

import logging
import asyncio
import hashlib
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

try:
    from backend.security.zero_trust import client_ip, rate_limit
except (ModuleNotFoundError, ImportError):
    from security.zero_trust import client_ip, rate_limit

from backend.services import auth_service
from backend.services.auth_service import (
    change_username,
    create_guest_session,
    get_all_plans,
    get_credit_history,
    issue_session_jwt,
    login_user_with_email,
    register_user_with_email,
    resolve_request_identity,
    revoke_all_sessions,
    upsert_user_from_google,
    verify_google_credential,
)

log = logging.getLogger("wpb.routes_auth")


async def _auth_rate_limited(request: Request, action: str, limit: int, window: int, identifier: str = "") -> bool:
    ip = client_ip(request)
    allowed, _ = await asyncio.to_thread(rate_limit, f"auth:{action}:ip", ip, limit, window)
    if not allowed:
        return True
    if identifier:
        account_key = hashlib.sha256(identifier.strip().lower().encode("utf-8")).hexdigest()
        account_allowed, _ = await asyncio.to_thread(
            rate_limit, f"auth:{action}:account", account_key, max(3, limit // 2), window
        )
        if not account_allowed:
            return True
    return False




async def _read_json_limited(request: Request, max_bytes: int = 32 * 1024):
    """Read JSON without trusting Content-Length; also bounds chunked request bodies."""
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > max_bytes:
            raise ValueError("Request body too large.")
    try:
        import json
        body = json.loads(raw or b"{}")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid JSON body.") from exc
    if not isinstance(body, dict):
        raise ValueError("JSON object expected.")
    return body


def _rate_limited_response() -> JSONResponse:
    return JSONResponse(
        {"ok": False, "error": "Too many authentication attempts. Please try again later."},
        status_code=429,
        headers={"Cache-Control": "no-store", "Retry-After": "60"},
    )


async def session_handler(request: Request) -> Response:
    """Returns current user or guest session state."""
    identity = resolve_request_identity(request)
    resp = JSONResponse({"ok": True, "identity": identity})
    if identity.get("is_guest") and identity.get("guest_id"):
        if not request.cookies.get("wpb_guest"):
            resp.set_cookie(
                "wpb_guest",
                identity["guest_id"],
                max_age=7 * 86400,
                httponly=True,
                samesite="lax",
                secure=True
            )
    return resp


async def google_auth_handler(request: Request) -> Response:
    """Verifies Google One-Tap or OAuth token and logs the user in."""
    if await _auth_rate_limited(request, "google", 20, 900):
        return _rate_limited_response()
    try:
        body = await _read_json_limited(request)
    except ValueError as exc:
        status = 413 if "too large" in str(exc).lower() else 400
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=status)

    credential = body.get("credential") or body.get("id_token")
    if not credential:
        return JSONResponse({"ok": False, "error": "Missing Google credential"}, status_code=400)

    google_data = await verify_google_credential(credential)
    if not google_data:
        return JSONResponse({"ok": False, "error": "Invalid or expired Google token"}, status_code=401)

    guest_id = body.get("guest_id") or request.cookies.get("wpb_guest")
    try:
        user = upsert_user_from_google(google_data, guest_id=guest_id)
    except PermissionError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
    return _session_response(user)


async def register_handler(request: Request) -> Response:
    """Registers a new account using email & password."""
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > 32 * 1024:
        return JSONResponse({"ok": False, "error": "Request body too large."}, status_code=413)
    if await _auth_rate_limited(request, "register", 6, 3600):
        return _rate_limited_response()
    try:
        body = await _read_json_limited(request)
    except ValueError as exc:
        status = 413 if "too large" in str(exc).lower() else 400
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=status)

    email = str(body.get("email") or "")
    password = str(body.get("password") or "")
    name = str(body.get("name") or "")
    username = str(body.get("username") or "")
    guest_id = body.get("guest_id") or request.cookies.get("wpb_guest")

    user, err = register_user_with_email(email, password, name=name, guest_id=guest_id, username=username)
    if err or not user:
        return JSONResponse({"ok": False, "error": err or "Registration failed"}, status_code=400)
    bonus = auth_service.SIGNUP_BONUS_CREDITS
    return _session_response(user, message=f"Welcome! Your username is @{user['username']}." +
                             (f" You received {bonus} bonus credits." if bonus else ""))


async def login_handler(request: Request) -> Response:
    """Authenticates an account using email & password."""
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > 32 * 1024:
        return JSONResponse({"ok": False, "error": "Request body too large."}, status_code=413)
    if await _auth_rate_limited(request, "login", 12, 900):
        return _rate_limited_response()
    try:
        body = await _read_json_limited(request)
    except ValueError as exc:
        status = 413 if "too large" in str(exc).lower() else 400
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=status)

    identifier = str(body.get("identifier") or body.get("email") or body.get("username") or "")
    if await _auth_rate_limited(request, "login-account", 12, 900, identifier):
        return _rate_limited_response()
    password = str(body.get("password") or "")

    user, err = login_user_with_email(identifier, password)
    if err or not user:
        return JSONResponse({"ok": False, "error": err or "Invalid credentials"}, status_code=401)
    return _session_response(user)


async def logout_handler(request: Request) -> Response:
    """Clears this browser's session. Pass {"all": true} to sign out every device."""
    try:
        body = await _read_json_limited(request)
    except ValueError:
        body = {}
    if body.get("all"):
        identity = resolve_request_identity(request, create_guest=False)
        if identity.get("authenticated"):
            revoke_all_sessions(identity["user_id"])
    resp = JSONResponse({"ok": True, "message": "Logged out successfully"}, headers={"Cache-Control": "no-store"})
    resp.delete_cookie("wpb_session", httponly=True, samesite="lax", secure=True)
    return resp


async def username_handler(request: Request) -> Response:
    """Changes the signed-in user's username."""
    if await _auth_rate_limited(request, "username", 10, 3600):
        return _rate_limited_response()
    identity = resolve_request_identity(request, create_guest=False)
    if not identity.get("authenticated"):
        return JSONResponse({"ok": False, "error": "Sign in required."}, status_code=401)
    try:
        body = await _read_json_limited(request)
    except ValueError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
    ok, err = change_username(identity["user_id"], str(body.get("username") or ""))
    if not ok:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return JSONResponse({"ok": True, "username": str(body.get("username")).strip().lower()})


async def config_handler(request: Request) -> Response:
    """Public auth configuration for the frontend (no secrets)."""
    ids = auth_service.google_client_ids()
    return JSONResponse({"ok": True, "google_client_id": ids[0] if ids else None,
                         "password_min_length": auth_service.MIN_PASSWORD_LENGTH},
                        headers={"Cache-Control": "public, max-age=300"})


def _session_response(user, message: str = "") -> JSONResponse:
    session_token = issue_session_jwt(user)
    public_user = {k: user.get(k) for k in ("id", "email", "username", "name", "avatar", "plan", "plan_name",
                                           "credits", "max_resolution", "max_duration", "email_verified", "has_password")}
    public_user.update({"authenticated": True, "is_guest": False})
    body = {"ok": True, "token": session_token, "user": public_user}
    if message:
        body["message"] = message
    resp = JSONResponse(body, headers={"Cache-Control": "no-store"})
    resp.set_cookie("wpb_session", session_token, max_age=30 * 86400, httponly=True, samesite="lax", secure=True)
    return resp


async def plans_handler(request: Request) -> Response:
    """Returns available plans and feature matrix from database."""
    plans = get_all_plans()
    return JSONResponse({"ok": True, "plans": plans})


async def ledger_handler(request: Request) -> Response:
    """Returns append-only credit ledger history for current user/guest."""
    identity = resolve_request_identity(request)
    if identity.get("authenticated") and identity.get("user_id"):
        history = get_credit_history("user", identity["user_id"])
    elif identity.get("is_guest") and identity.get("guest_id"):
        history = get_credit_history("guest", identity["guest_id"])
    else:
        history = []
    return JSONResponse({"ok": True, "history": history})


routes_auth = [
    Route("/api/auth/session", session_handler, methods=["GET"]),
    Route("/api/auth/google", google_auth_handler, methods=["POST"]),
    Route("/api/auth/register", register_handler, methods=["POST"]),
    Route("/api/auth/login", login_handler, methods=["POST"]),
    Route("/api/auth/logout", logout_handler, methods=["POST"]),
    Route("/api/auth/username", username_handler, methods=["POST"]),
    Route("/api/auth/config", config_handler, methods=["GET"]),
    Route("/api/auth/plans", plans_handler, methods=["GET"]),
    Route("/api/auth/ledger", ledger_handler, methods=["GET"]),
]
