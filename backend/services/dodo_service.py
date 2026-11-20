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

DODO_API_KEY = (os.environ.get("DODO_PAYMENTS_API_KEY") or os.environ.get("DODO_API_KEY") or "").strip()
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


def product_id_for(plan_id: str) -> str:
    """Live checkout uses only product IDs configured in the environment (live and test products differ)."""
    env_id = auth_service._env_product_id(plan_id)
    if env_id:
        return env_id
    if DODO_ENV == "live":
        return ""
    return DODO_PRODUCT_IDS.get(plan_id) or DODO_PRODUCT_IDS.get(plan_id.lower().replace("_", "")) or ""


def safe_return_url(candidate: Optional[str]) -> str:
    """Only return to our own site after checkout (prevents an open redirect through the payment page)."""
    from urllib.parse import urlsplit
    allowed = {h.strip().lower() for h in os.environ.get("CHECKOUT_RETURN_HOSTS", "ovd.winplaybox.in").split(",") if h.strip()}
    if candidate:
        parts = urlsplit(candidate)
        if parts.scheme == "https" and (parts.hostname or "").lower() in allowed and not parts.username:
            return candidate
    return SUCCESS_RETURN_URL


def webhook_secret() -> str:
    return (os.environ.get("DODO_PAYMENTS_WEBHOOK_SECRET") or os.environ.get("DODO_WEBHOOK_SECRET") or "").strip()


WEBHOOK_TOLERANCE_SECONDS = 300


def verify_webhook_signature(payload_bytes: bytes, headers: Dict[str, str]) -> bool:
    """Standard Webhooks: HMAC-SHA256 over "{id}.{timestamp}.{body}", 5-minute replay window.

    A missing secret always fails closed (in every environment).
    """
    secret = webhook_secret()
    webhook_id = headers.get("webhook-id", "")
    webhook_timestamp = headers.get("webhook-timestamp", "")
    signature_header = headers.get("webhook-signature", "")
    if not (secret and webhook_id and webhook_timestamp.isdigit() and signature_header):
        return False
    if abs(time.time() - int(webhook_timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
        return False
    raw_secret = secret[6:] if secret.startswith("whsec_") else secret
    try:
        key = base64.b64decode(raw_secret, validate=True)
    except Exception:
        return False
    to_sign = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + payload_bytes
    expected = base64.b64encode(hmac.new(key, to_sign, hashlib.sha256).digest()).decode("utf-8")
    for part in signature_header.split():
        version, _, sig = part.partition(",")
        if version == "v1" and hmac.compare_digest(sig.strip(), expected):
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
    dest_url = safe_return_url(return_url)
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

    product_id = product_id_for(plan_id)
    if not product_id:
        raise ValueError(f"Checkout for '{plan_id}' is not configured yet.")

    metadata = {
        "app": "ovd_editor",
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
                log.warning("Dodo checkout failed (%s): %s", res.status_code, res.text[:500])
        except Exception as e:
            log.exception("Error calling Dodo Payments API: %s", e)
        raise RuntimeError("Payment provider is unavailable. Please try again in a minute.")

    # Development only: a local mock checkout (never reachable in production).
    if _is_production():
        raise RuntimeError("Payments are not configured.")
    mock_session_id = f"dodo_mock_{int(time.time())}_{plan_id}"
    return {
        "ok": True,
        "checkout_url": f"/api/payments/dodo/mock-checkout?session_id={mock_session_id}&plan_id={plan_id}&user_id={user_id}&guest_id={guest_id}",
        "session_id": mock_session_id,
        "mode": "sandbox",
        "plan": plan,
    }


def _is_production() -> bool:
    return os.environ.get("WPB_ENV", "").lower() in ("prod", "production") or bool(os.environ.get("RENDER"))


def _iso_to_epoch(value: Any) -> Optional[float]:
    if not value:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _plan_from_data(data: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if metadata.get("plan_id"):
        plan = auth_service.get_plan(str(metadata["plan_id"]))
        if plan:
            return plan
    pid = data.get("product_id")
    if not pid:
        cart = data.get("product_cart") or []
        if cart and isinstance(cart, list) and isinstance(cart[0], dict):
            pid = cart[0].get("product_id")
    return auth_service.find_plan_by_product(pid) if pid else None


def _owner_from_data(data: Dict[str, Any], metadata: Dict[str, Any]):
    customer = data.get("customer") or {}
    with auth_service._connect() as conn:
        return auth_service.resolve_owner(
            conn,
            user_id=str(metadata.get("user_id") or ""),
            guest_id=str(metadata.get("guest_id") or ""),
            subscription_id=str(data.get("subscription_id") or ""),
            email=str(customer.get("email") or ""),
        )


def _is_ours(data: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
    """The same Dodo account also serves WinPlayBox Studio; only handle OVD editor purchases here."""
    if metadata.get("app"):
        return metadata.get("app") == "ovd_editor"
    if metadata.get("order_id"):  # Studio orders
        return False
    return bool(metadata.get("plan_id") or data.get("subscription_id") or _plan_from_data(data, metadata))


async def process_webhook_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Applies one verified Dodo event. Credits are granted only by payment.succeeded (exactly once per payment);
    subscription events change plan status only, so a purchase is never credited twice."""
    event_type = str(event.get("type") or "")
    data = event.get("data") or {}
    metadata = data.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    if not _is_ours(data, metadata):
        return {"ok": True, "action": "ignored_other_app"}

    if event_type == "payment.succeeded":
        payment_id = str(data.get("payment_id") or "")
        if not payment_id:
            return {"ok": False, "error": "missing_payment_id"}
        plan = _plan_from_data(data, metadata)
        if not plan and data.get("subscription_id"):
            with auth_service._connect() as conn:
                row = conn.execute("SELECT plan_id FROM subscriptions WHERE subscription_id = ?",
                                   (str(data["subscription_id"]),)).fetchone()
            plan = auth_service.get_plan(row["plan_id"]) if row else None
        if not plan or plan["id"] == "free":
            log.error("payment %s: plan could not be resolved", payment_id)
            return {"ok": False, "error": "unknown_plan", "retry": True}
        owner = _owner_from_data(data, metadata)
        if not owner:
            log.error("payment %s: owner could not be resolved", payment_id)
            return {"ok": False, "error": "unknown_owner", "retry": True}
        amount = data.get("total_amount")
        return auth_service.grant_payment(
            payment_id, owner, plan, subscription_id=str(data.get("subscription_id") or ""),
            amount_minor=int(amount) if isinstance(amount, (int, float)) else None,
            currency=str(data.get("currency") or ""),
        )

    if event_type in ("refund.succeeded", "dispute.opened", "dispute.lost", "dispute.accepted"):
        payment_id = str(data.get("payment_id") or "")
        if not payment_id:
            return {"ok": True, "action": "ignored_no_payment"}
        reason = "refunded" if event_type.startswith("refund") else "disputed"
        return auth_service.reverse_payment(payment_id, reason)

    if event_type.startswith("subscription."):
        sub_id = str(data.get("subscription_id") or "")
        if not sub_id:
            return {"ok": True, "action": "ignored_no_subscription"}
        status = event_type.split(".", 1)[1]
        status = {"active": "active", "renewed": "active", "plan_changed": "active", "updated": "active",
                  "unpaused": "active"}.get(status, status)
        plan = _plan_from_data(data, metadata)
        owner = _owner_from_data(data, metadata)
        return auth_service.update_subscription_status(
            sub_id, status, owner=owner, plan_id=plan["id"] if plan else "",
            next_billing_at=_iso_to_epoch(data.get("next_billing_date")),
        )

    if event_type in ("payment.failed", "payment.cancelled", "payment.processing"):
        return {"ok": True, "action": f"noted_{event_type}"}
    return {"ok": True, "action": "ignored_event_type"}
