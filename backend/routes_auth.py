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

from backend.services.auth_service import (
    create_guest_session,
    get_all_plans,
    get_credit_history,
    issue_session_jwt,
    login_user_with_email,
    register_user_with_email,
    resolve_request_identity,
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
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > 32 * 1024:
        return JSONResponse({"ok": False, "error": "Request body too large."}, status_code=413)
    if await _auth_rate_limited(request, "google", 20, 900):
        return _rate_limited_response()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    credential = body.get("credential") or body.get("id_token")
    if not credential:
        return JSONResponse({"ok": False, "error": "Missing Google credential"}, status_code=400)

    google_data = await verify_google_credential(credential)
    if not google_data:
        return JSONResponse({"ok": False, "error": "Invalid or expired Google token"}, status_code=401)

    guest_id = body.get("guest_id") or request.cookies.get("wpb_guest")
    user = upsert_user_from_google(google_data, guest_id=guest_id)
    session_token = issue_session_jwt(user)

    resp = JSONResponse({
        "ok": True,
        "token": session_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "avatar": user.get("avatar"),
            "plan": user.get("plan", "free"),
            "credits": user.get("credits", 2),
            "authenticated": True,
            "is_guest": False
        }
    })
    resp.set_cookie(
        "wpb_session",
        session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=True
    )
    return resp


async def register_handler(request: Request) -> Response:
    """Registers a new account using email & password."""
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > 32 * 1024:
        return JSONResponse({"ok": False, "error": "Request body too large."}, status_code=413)
    if await _auth_rate_limited(request, "register", 6, 3600):
        return _rate_limited_response()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    email = body.get("email")
    password = body.get("password")
    name = body.get("name", "")
    guest_id = body.get("guest_id") or request.cookies.get("wpb_guest")

    user, err = register_user_with_email(email, password, name=name, guest_id=guest_id)
    if err or not user:
        return JSONResponse({"ok": False, "error": err or "Registration failed"}, status_code=400)

    session_token = issue_session_jwt(user)
    resp = JSONResponse({
        "ok": True,
        "token": session_token,
        "user": user,
        "message": "Welcome! You received 5 bonus credits."
    })
    resp.set_cookie(
        "wpb_session",
        session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=True
    )
    return resp


async def login_handler(request: Request) -> Response:
    """Authenticates an account using email & password."""
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > 32 * 1024:
        return JSONResponse({"ok": False, "error": "Request body too large."}, status_code=413)
    if await _auth_rate_limited(request, "login", 12, 900):
        return _rate_limited_response()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    email = body.get("email")
    if await _auth_rate_limited(request, "login-account", 12, 900, str(email or "")):
        return _rate_limited_response()
    password = body.get("password")

    user, err = login_user_with_email(email, password)
    if err or not user:
        return JSONResponse({"ok": False, "error": err or "Invalid credentials"}, status_code=401)

    session_token = issue_session_jwt(user)
    resp = JSONResponse({
        "ok": True,
        "token": session_token,
        "user": user
    })
    resp.set_cookie(
        "wpb_session",
        session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=True
    )
    return resp


async def logout_handler(request: Request) -> Response:
    """Clears authentication session."""
    resp = JSONResponse({"ok": True, "message": "Logged out successfully"})
    resp.delete_cookie("wpb_session")
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
    Route("/api/auth/plans", plans_handler, methods=["GET"]),
    Route("/api/auth/ledger", ledger_handler, methods=["GET"]),
]
