"""Routes for Dodo Payments, subscription checkouts, and webhooks."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse
from starlette.routing import Route

from backend.services import auth_service, dodo_service

log = logging.getLogger("routes_payments")


async def checkout_handler(request: Request) -> Response:
    """Creates a Dodo Payments checkout session for subscription plans."""
    try:
        body: Dict[str, Any] = await request.json() if request.method == "POST" else {}
    except Exception:
        body = {}

    plan_id = body.get("plan_id") or request.query_params.get("plan_id")
    if not plan_id:
        return JSONResponse({"ok": False, "error": "plan_id is required"}, status_code=400)

    identity = auth_service.resolve_request_identity(request)
    customer_email = body.get("email") or request.query_params.get("email")
    customer_name = body.get("name") or request.query_params.get("name")
    return_url = body.get("return_url") or request.query_params.get("return_url")

    try:
        session = await dodo_service.create_checkout_session(
            plan_id=plan_id,
            identity=identity,
            customer_email=customer_email,
            customer_name=customer_name,
            return_url=return_url
        )
        return JSONResponse(session)
    except Exception as e:
        log.exception("checkout_handler error: %s", e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


async def webhook_handler(request: Request) -> Response:
    """Receives and verifies Dodo Payments webhooks."""
    payload_bytes = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    # Signature verification
    if not dodo_service.verify_webhook_signature(payload_bytes, headers):
        log.warning("Invalid Dodo webhook signature received")
        return JSONResponse({"ok": False, "error": "Invalid signature"}, status_code=401)

    try:
        event = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Invalid JSON: {e}"}, status_code=400)

    result = await dodo_service.process_webhook_event(event)
    return JSONResponse(result)


async def mock_checkout_handler(request: Request) -> Response:
    """Mock checkout landing page for sandbox testing."""
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
