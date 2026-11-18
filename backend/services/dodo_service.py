"""Dodo Payments integration service for OVD AI Video Editor and Studio.

Handles:
- Subscription plans and one-time credit pack checkout sessions
- Webhook signature verification (Standard Webhooks HMAC-SHA256)
- Plan upgrade activation and credit balance settlement
- Mock / sandbox simulation for zero-downtime testing
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Dict, Optional
import httpx

from . import auth_service

log = logging.getLogger("dodo_payments")

DODO_API_KEY = os.environ.get("DODO_PAYMENTS_API_KEY", "").strip()
DODO_WEBHOOK_SECRET = os.environ.get("DODO_PAYMENTS_WEBHOOK_SECRET", "").strip()
DODO_ENV = os.environ.get("DODO_PAYMENTS_ENV", "live" if DODO_API_KEY.startswith("dodo_live_") else "test").strip().lower()

BASE_URL = "https://live.dodopayments.com" if (DODO_ENV == "live" or DODO_API_KEY.startswith("dodo_live_")) else "https://test.dodopayments.com"
SUCCESS_RETURN_URL = os.environ.get("DODO_RETURN_URL", "https://ovd.winplaybox.in/payment/success")

# Product ID mapping for Dodo Payments Live Environment
DODO_PRODUCT_IDS: Dict[str, str] = {
    # Monthly 7-Tier Plans
    "plan1": os.environ.get("DODO_PRODUCT_PLAN_1", "pdt_0NsD5gB9BVgr9HcXQ1bZn"),
    "plan_1": os.environ.get("DODO_PRODUCT_PLAN_1", "pdt_0NsD5gB9BVgr9HcXQ1bZn"),
    "plan2": os.environ.get("DODO_PRODUCT_PLAN_2", "pdt_0NsD6LN0JNlPsYDKDC68B"),
    "plan_2": os.environ.get("DODO_PRODUCT_PLAN_2", "pdt_0NsD6LN0JNlPsYDKDC68B"),
    "plan3": os.environ.get("DODO_PRODUCT_PLAN_3", "pdt_0NsD6LSzzhmCeUJSD6xal"),
    "plan_3": os.environ.get("DODO_PRODUCT_PLAN_3", "pdt_0NsD6LSzzhmCeUJSD6xal"),
    "plan4": os.environ.get("DODO_PRODUCT_PLAN_4", "pdt_0NsD6LZhTr5YKnO2ofQtH"),
    "plan_4": os.environ.get("DODO_PRODUCT_PLAN_4", "pdt_0NsD6LZhTr5YKnO2ofQtH"),
    "plan5": os.environ.get("DODO_PRODUCT_PLAN_5", "pdt_0NsD6LqMzHo26g2eV0eC1"),
    "plan_5": os.environ.get("DODO_PRODUCT_PLAN_5", "pdt_0NsD6LqMzHo26g2eV0eC1"),
    "plan6": os.environ.get("DODO_PRODUCT_PLAN_6", "pdt_0NsD6M6kJNKNQ83qBKNVn"),
    "plan_6": os.environ.get("DODO_PRODUCT_PLAN_6", "pdt_0NsD6M6kJNKNQ83qBKNVn"),

    # Yearly Plans (20% off)
    "plan1_yearly": os.environ.get("DODO_PRODUCT_PLAN_1_YEARLY", "pdt_0NsDTroXSQKLLqwaoMNV1"),
    "plan2_yearly": os.environ.get("DODO_PRODUCT_PLAN_2_YEARLY", "pdt_0NsDTrwOilW0LIcdiNcly"),
    "plan3_yearly": os.environ.get("DODO_PRODUCT_PLAN_3_YEARLY", "pdt_0NsDTs3x8Y7ZbeE07bawr"),
    "plan4_yearly": os.environ.get("DODO_PRODUCT_PLAN_4_YEARLY", "pdt_0NsDTsB84lRbmGgk3mUx8"),
    "plan5_yearly": os.environ.get("DODO_PRODUCT_PLAN_5_YEARLY", "pdt_0NsDTsHILc59bPNfawC6Q"),
    "plan6_yearly": os.environ.get("DODO_PRODUCT_PLAN_6_YEARLY", "pdt_0NsDTsOBDIg9hEZUM9oAG"),

    # 24-Hour Creator Day Pass (One-off projects)
    "day_pass": os.environ.get("DODO_PRODUCT_DAY_PASS", "pdt_0NsDTUmxEe6Wbzz5hsp7L"),
    "daypass": os.environ.get("DODO_PRODUCT_DAY_PASS", "pdt_0NsDTUmxEe6Wbzz5hsp7L"),

    # One-Time Credit Top-Up Packs (Never Expire)
    "pack_100": os.environ.get("DODO_PRODUCT_PACK_100", "pdt_0NsDTrR0ewxQK6PTTP98G"),
    "pack_300": os.environ.get("DODO_PRODUCT_PACK_300", "pdt_0NsDTrWv3ibp4UavYQ6wF"),
    "pack_500": os.environ.get("DODO_PRODUCT_PACK_500", "pdt_0Ns7d19f2M1B7GslZEnKA"),
    "pack_1500": os.environ.get("DODO_PRODUCT_PACK_1500", "pdt_0NsDTrfAWJD4RrbM3SuwL"),
}


def verify_webhook_signature(payload_bytes: bytes, headers: Dict[str, str]) -> bool:
    """Verifies Dodo Payments webhook HMAC-SHA256 signature."""
    if not DODO_WEBHOOK_SECRET:
        # If secret not set in test environment, allow mock / dev webhooks
        return DODO_ENV != "live"

    webhook_id = headers.get("webhook-id", "")
    webhook_timestamp = headers.get("webhook-timestamp", "")
    signature_header = headers.get("webhook-signature", "")

    if not signature_header:
        return False

    # Standard Webhooks specification
    to_sign = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + payload_bytes
    secret = DODO_WEBHOOK_SECRET.replace("whsec_", "")
    try:
        secret_bytes = base64.b64decode(secret) if len(secret) % 4 == 0 else secret.encode("utf-8")
    except Exception:
        secret_bytes = secret.encode("utf-8")

    expected_sig = hmac.new(secret_bytes, to_sign, hashlib.sha256).digest()
    expected_b64 = base64.b64encode(expected_sig).decode("utf-8")

    for part in signature_header.split(" "):
        sig = part.split(",", 1)[-1].strip()
        if sig.startswith("v1,"):
            sig = sig[3:]
        if hmac.compare_digest(sig, expected_b64):
            return True
    return False


async def create_checkout_session(
    plan_id: str,
    identity: Dict[str, Any],
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
    return_url: Optional[str] = None,
    currency: str = "INR"
) -> Dict[str, Any]:
    """Creates a Dodo Payments checkout session for subscription plans."""
    plan = auth_service.get_plan(plan_id) or auth_service.get_plan(plan_id.lower().replace("_", ""))
    if not plan or plan["id"] == "free":
        raise ValueError(f"Invalid plan '{plan_id}' selected for checkout.")
    plan_id = plan["id"]

    user_id = identity.get("user_id") or ""
    guest_id = identity.get("guest_id") or ""
    email = customer_email or identity.get("email") or f"{guest_id or 'guest'}@winplaybox.in"
    name = customer_name or identity.get("name") or "Valued Creator"
    dest_url = return_url or SUCCESS_RETURN_URL
    curr = (currency or "INR").upper().strip()

    # Map currency to standard regional country code for localized tax/billing
    currency_to_country = {
        "INR": "IN",
        "EUR": "DE",
        "USD": "US",
        "GBP": "GB",
        "AED": "AE",
        "CAD": "CA",
        "AUD": "AU",
    }
    country_code = currency_to_country.get(curr, "US")

    product_id = DODO_PRODUCT_IDS.get(plan_id) or DODO_PRODUCT_IDS.get(plan_id.lower().replace("_", "")) or f"p_ovd_{plan_id}"

    metadata = {
        "plan_id": plan_id,
        "user_id": user_id,
        "guest_id": guest_id,
        "entity_type": "user" if user_id else "guest",
        "plan_name": plan["name"],
        "max_res": str(plan["max_res"]),
        "credits": str(plan["credits"]),
        "currency": curr
    }

    # 1. If live or test API key is provided, call Dodo Payments API
    if DODO_API_KEY:
        try:
            payload = {
                "billing_currency": curr,
                "billing": {
                    "country": country_code
                },
                "customer": {
                    "email": email,
                    "name": name
                },
                "product_cart": [
                    {
                        "product_id": product_id,
                        "quantity": 1
                    }
                ],
                "return_url": dest_url,
                "metadata": metadata
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{BASE_URL}/checkouts",
                    headers={
                        "Authorization": f"Bearer {DODO_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    checkout_url = data.get("checkout_url") or data.get("payment_link")
                    if checkout_url:
                        return {
                            "ok": True,
                            "checkout_url": checkout_url,
                            "session_id": data.get("payment_id") or data.get("id"),
                            "mode": DODO_ENV
                        }
                log.warning("Dodo API call failed (%s): %s", res.status_code, res.text)
        except Exception as e:
            log.exception("Error calling Dodo Payments API: %s", e)

    # 2. Seamless sandbox mock checkout for immediate development & preview testing
    mock_session_id = f"dodo_mock_{int(time.time())}_{plan_id}"
    mock_url = f"https://api.winplaybox.in/api/payments/dodo/mock-checkout?session_id={mock_session_id}&plan_id={plan_id}&user_id={user_id}&guest_id={guest_id}&return_url={dest_url}"

    return {
        "ok": True,
        "checkout_url": mock_url,
        "session_id": mock_session_id,
        "mode": "sandbox",
        "plan": plan
    }


async def process_webhook_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Processes incoming Dodo Payments webhooks and updates ledger and plan entitlements."""
    event_type = event.get("type") or event.get("event")
    data = event.get("data") or {}
    metadata = data.get("metadata") or {}

    plan_id = metadata.get("plan_id")
    user_id = metadata.get("user_id")
    guest_id = metadata.get("guest_id")
    payment_id = data.get("payment_id") or data.get("id") or str(int(time.time()))

    log.info("Processing Dodo webhook: %s, plan: %s, user: %s", event_type, plan_id, user_id)

    if event_type in ("payment.succeeded", "checkout.session.completed", "subscription.active"):
        if not plan_id:
            return {"ok": True, "action": "ignored_no_plan"}

        norm_plan_id = plan_id.lower().replace("_", "")
        plan = auth_service.get_plan(norm_plan_id) or auth_service.get_plan(plan_id)
        if not plan:
            return {"ok": False, "error": f"Unknown plan {plan_id}"}
        plan_id = plan["id"]

        if user_id:
            success = auth_service.upgrade_user_plan(user_id, plan_id, dodo_subscription_id=payment_id)
            return {"ok": success, "action": "upgraded_user", "user_id": user_id, "plan": plan_id}
        elif guest_id:
            success = auth_service.upgrade_guest_plan(guest_id, plan_id, dodo_subscription_id=payment_id)
            return {"ok": success, "action": "upgraded_guest", "guest_id": guest_id, "plan": plan_id}

    return {"ok": True, "action": "ignored_event_type"}
