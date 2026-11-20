"""Admin operations for OVD: integration service tokens, audited credit grants, payment visibility.

All routes require admin auth (X-Admin-Key break-glass key, or a signed-in OVD/Supabase account
whose verified email is in WPB_ADMIN_EMAILS). Every mutation is logged with the acting admin.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

try:
    from backend.security.zero_trust import admin_locked, authenticate_admin, client_ip, record_admin_failure
    from backend.services import auth_service
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from security.zero_trust import admin_locked, authenticate_admin, client_ip, record_admin_failure  # type: ignore
    from services import auth_service  # type: ignore

log = logging.getLogger("wpb.admin_ops")
NO_STORE = {"Cache-Control": "no-store"}


def _admin(request: Request):
    ip = client_ip(request)
    if admin_locked(ip):
        return None, JSONResponse({"ok": False, "error": "Too many failed admin attempts."}, status_code=429, headers=NO_STORE)
    who = authenticate_admin(request)
    if not who:
        record_admin_failure(ip)
        return None, JSONResponse({"ok": False, "error": "Admin authentication required."}, status_code=401, headers=NO_STORE)
    return who, None


async def _json(request: Request) -> Dict[str, Any]:
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 16 * 1024:
            raise ValueError("Request body too large.")
    import json
    body = json.loads(raw or b"{}")
    if not isinstance(body, dict):
        raise ValueError("JSON object expected.")
    return body


async def tokens_list(request: Request) -> Response:
    who, err = _admin(request)
    if err:
        return err
    tokens = await asyncio.to_thread(auth_service.list_service_tokens)
    return JSONResponse({"ok": True, "tokens": tokens, "scopes": list(auth_service.SERVICE_SCOPES)}, headers=NO_STORE)


async def tokens_create(request: Request) -> Response:
    who, err = _admin(request)
    if err:
        return err
    try:
        body = await _json(request)
        scopes = body.get("scopes") or []
        if not isinstance(scopes, list):
            raise ValueError("scopes must be a list")
        ttl = body.get("ttl_days")
        ttl = int(ttl) if ttl not in (None, "") else None
        if ttl is not None and not 1 <= ttl <= 730:
            raise ValueError("ttl_days must be between 1 and 730")
        created = await asyncio.to_thread(auth_service.create_service_token, str(body.get("name") or ""), scopes, who, ttl)
    except (ValueError, TypeError) as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400, headers=NO_STORE)
    log.warning("AUDIT %s created service token %s (%s) scopes=%s", who, created["id"], created["name"], created["scopes"])
    return JSONResponse({"ok": True, "token": created,
                         "notice": "Copy this token now. It is stored hashed and cannot be shown again."}, headers=NO_STORE)


async def tokens_revoke(request: Request) -> Response:
    who, err = _admin(request)
    if err:
        return err
    tid = request.path_params["id"]
    ok = await asyncio.to_thread(auth_service.revoke_service_token, tid)
    log.warning("AUDIT %s revoked service token %s -> %s", who, tid, ok)
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404, headers=NO_STORE)


async def credits_grant(request: Request) -> Response:
    """Audited manual credit grant (support, promotions). Requires a reason."""
    who, err = _admin(request)
    if err:
        return err
    try:
        body = await _json(request)
        amount = int(body.get("amount") or 0)
        reason = str(body.get("reason") or "").strip()
        if not 1 <= amount <= 100000 or len(reason) < 4:
            raise ValueError("amount (1-100000) and a reason are required")
        target = str(body.get("user") or "").strip().lower()
        if not target:
            raise ValueError("user (email, username or user id) is required")
    except (ValueError, TypeError) as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400, headers=NO_STORE)

    def _find():
        with auth_service._connect() as conn:
            row = conn.execute("SELECT id FROM users WHERE id = ? OR email = ? OR username = ?", (target, target, target)).fetchone()
            return row["id"] if row else None
    user_id = await asyncio.to_thread(_find)
    if not user_id:
        return JSONResponse({"ok": False, "error": "User not found."}, status_code=404, headers=NO_STORE)
    ok = await asyncio.to_thread(auth_service.add_credits_to_identity,
                                 {"authenticated": True, "user_id": user_id}, amount, f"Admin grant by {who}: {reason}"[:300])
    log.warning("AUDIT %s granted %s credits to %s: %s", who, amount, user_id, reason)
    return JSONResponse({"ok": ok, "user_id": user_id}, headers=NO_STORE)


async def payments_recent(request: Request) -> Response:
    who, err = _admin(request)
    if err:
        return err

    def _load():
        with auth_service._connect() as conn:
            grants = [dict(r) for r in conn.execute(
                "SELECT * FROM payment_grants ORDER BY created_at DESC LIMIT 100").fetchall()]
            events = [dict(r) for r in conn.execute(
                "SELECT * FROM payment_webhook_events ORDER BY received_at DESC LIMIT 100").fetchall()]
            subs = [dict(r) for r in conn.execute(
                "SELECT * FROM subscriptions ORDER BY updated_at DESC LIMIT 100").fetchall()]
        return grants, events, subs
    grants, events, subs = await asyncio.to_thread(_load)
    return JSONResponse({"ok": True, "grants": grants, "webhook_events": events, "subscriptions": subs}, headers=NO_STORE)


routes_admin_ops = [
    Route("/admin/ovd/service-tokens", tokens_list, methods=["GET"]),
    Route("/admin/ovd/service-tokens", tokens_create, methods=["POST"]),
    Route("/admin/ovd/service-tokens/{id}/revoke", tokens_revoke, methods=["POST"]),
    Route("/admin/ovd/credits/grant", credits_grant, methods=["POST"]),
    Route("/admin/ovd/payments", payments_recent, methods=["GET"]),
]
