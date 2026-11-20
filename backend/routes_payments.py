"""Routes for Dodo Payments, subscription checkouts, and webhooks."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse
from starlette.routing import Route

try:
    from backend.security.zero_trust import client_ip, rate_limit
except (ModuleNotFoundError, ImportError):
    from security.zero_trust import client_ip, rate_limit

from backend.services import auth_service, dodo_service

log = logging.getLogger("routes_payments")


async def checkout_handler(request: Request) -> Response:
    """Creates a Dodo Payments checkout session for subscription plans."""
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > 32 * 1024:
        return JSONResponse({"ok": False, "error": "Request body too large."}, status_code=413)
    allowed, _ = rate_limit("payments:checkout", client_ip(request), 10, 900)
    if not allowed:
        return JSONResponse(
            {"ok": False, "error": "Too many checkout attempts. Try again later."},
            status_code=429, headers={"Cache-Control": "no-store", "Retry-After": "60"},
        )
    try:
        body: Dict[str, Any] = await request.json() if request.method == "POST" else {}
    except Exception:
        body = {}

    plan_id = body.get("plan_id") or request.query_params.get("plan_id")
    if not plan_id:
        return JSONResponse({"ok": False, "error": "plan_id is required"}, status_code=400)

    identity = auth_service.resolve_request_identity(request)
    if os.environ.get("PAYMENTS_REQUIRE_ACCOUNT", "1") == "1" and not identity.get("authenticated"):
        # Paid credits must belong to a recoverable account (a guest cookie can be lost).
        return JSONResponse({"ok": False, "error": "Please sign in to purchase.", "auth_required": True},
                            status_code=401, headers={"Cache-Control": "no-store"})
    customer_email = body.get("email") or request.query_params.get("email")
    customer_name = body.get("name") or request.query_params.get("name")
    return_url = body.get("return_url") or request.query_params.get("return_url")
    currency = body.get("currency") or request.query_params.get("currency") or "INR"

    try:
        session = await dodo_service.create_checkout_session(
            plan_id=plan_id,
            identity=identity,
            customer_email=customer_email,
            customer_name=customer_name,
            return_url=return_url,
            currency=currency
        )
        return JSONResponse(session, headers={"Cache-Control": "no-store"})
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception as e:
        log.exception("checkout_handler error: %s", e)
        return JSONResponse({"ok": False, "error": "Checkout is temporarily unavailable. Please try again."}, status_code=503)


async def webhook_handler(request: Request) -> Response:
    """Receives Dodo webhooks: verified signature + 5-minute window, each webhook-id processed exactly once.

    Returns 5xx for retryable failures so Dodo retries; a processed id returns 200 on every retry.
    """
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1024 * 1024:
            return JSONResponse({"ok": False, "error": "Webhook payload too large."}, status_code=413)
    payload_bytes = bytes(raw)
    headers = {k.lower(): v for k, v in request.headers.items()}

    if not dodo_service.verify_webhook_signature(payload_bytes, headers):
        log.warning("Rejected Dodo webhook: bad signature or stale timestamp")
        return JSONResponse({"ok": False, "error": "Invalid signature"}, status_code=401)

    try:
        event = json.loads(payload_bytes.decode("utf-8"))
        if not isinstance(event, dict):
            raise ValueError("not an object")
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)

    webhook_id = headers["webhook-id"]
    event_type = str(event.get("type") or "")
    if not auth_service.claim_webhook_event(webhook_id, event_type):
        return JSONResponse({"ok": True, "duplicate": True})
    try:
        result = await dodo_service.process_webhook_event(event)
    except Exception:
        log.exception("Dodo webhook %s (%s) failed", webhook_id, event_type)
        auth_service.release_webhook_event(webhook_id)
        return JSONResponse({"ok": False, "error": "processing_failed"}, status_code=500)
    if not result.get("ok") and result.get("retry"):
        # e.g. payment arrived before we can resolve its owner: let Dodo retry later.
        auth_service.release_webhook_event(webhook_id)
        return JSONResponse({"ok": False, "error": result.get("error")}, status_code=503)
    auth_service.finish_webhook_event(webhook_id, json.dumps(result)[:500])
    log.info("Dodo webhook %s %s -> %s", webhook_id, event_type, result.get("action") or result.get("error"))
    return JSONResponse({"ok": True})


async def mock_checkout_handler(request: Request) -> Response:
    """Mock checkout page is disabled by default and never enabled in production."""
    production = os.environ.get("WPB_ENV", "").lower() in ("prod", "production") or bool(os.environ.get("RENDER"))
    if production or os.environ.get("WPB_ENABLE_MOCK_CHECKOUT", "0") != "1":
        return JSONResponse({"ok": False, "error": "Mock checkout is disabled."}, status_code=404)
    session_id = request.query_params.get("session_id", "mock_session")
    plan_id = request.query_params.get("plan_id", "plan_1")
    user_id = request.query_params.get("user_id", "")
    guest_id = request.query_params.get("guest_id", "")
    return_url = request.query_params.get("return_url", "https://ovd.winplaybox.in/ai-video-editor?payment=success")

    action = request.query_params.get("action")
    if action == "pay":
        # Simulate payment.succeeded webhook
        mock_event = {
            "type": "payment.succeeded",
            "data": {
                "payment_id": session_id,
                "metadata": {
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "guest_id": guest_id
                }
            }
        }
        await dodo_service.process_webhook_event(mock_event)
        target = return_url
        if "payment=" not in target:
            sep = "&" if "?" in target else "?"
            target = f"{target}{sep}payment=success&plan={plan_id}&session_id={session_id}"
        return RedirectResponse(url=target, status_code=302)

    plan = auth_service.get_plan(plan_id) or {}
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dodo Payments Sandbox Checkout</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0c; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .card {{ background: #16181d; border: 1px solid #272a34; border-radius: 16px; padding: 32px; max-width: 440px; width: 100%; box-shadow: 0 8px 30px rgba(0,0,0,0.5); text-align: center; }}
            h2 {{ margin-top: 0; color: #facc15; font-size: 24px; }}
            .badge {{ display: inline-block; background: rgba(250, 204, 21, 0.1); color: #facc15; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; margin-bottom: 20px; }}
            .detail {{ background: #1f222a; padding: 16px; border-radius: 10px; margin: 20px 0; text-align: left; font-size: 14px; line-height: 1.8; color: #d1d5db; }}
            .btn {{ display: block; width: 100%; background: #2563eb; color: white; padding: 14px 0; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; text-decoration: none; transition: background 0.2s; }}
            .btn:hover {{ background: #1d4ed8; }}
            .cancel {{ display: block; margin-top: 14px; color: #9ca3af; text-decoration: none; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Dodo Payments</h2>
            <div class="badge">SANDBOX TEST ENVIRONMENT</div>
            <p>You are upgrading to <strong>{plan.get('name', plan_id)}</strong></p>
            <div class="detail">
                <div><strong>Resolution:</strong> Up to {plan.get('max_res', 720)}p</div>
                <div><strong>Monthly Credits:</strong> {plan.get('credits', 30)} credits</div>
                <div><strong>Price:</strong> &#8377;{plan.get('price_inr', 0)} / ${plan.get('price_usd', 0)}</div>
                <div><strong>User ID:</strong> {user_id or guest_id or 'Guest'}</div>
            </div>
            <a href="?session_id={session_id}&plan_id={plan_id}&user_id={user_id}&guest_id={guest_id}&return_url={return_url}&action=pay" class="btn">Simulate Successful Payment</a>
            <a href="{return_url}" class="cancel">Cancel and return</a>
        </div>
    </body>
    </html>
    """
    return Response(html, media_type="text/html")


payments_routes = [
    Route("/api/payments/dodo/checkout", checkout_handler, methods=["GET", "POST"]),
    Route("/api/payments/dodo/webhook", webhook_handler, methods=["POST"]),
    Route("/api/payments/dodo/mock-checkout", mock_checkout_handler, methods=["GET"]),
]
