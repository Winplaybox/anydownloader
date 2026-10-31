"""Dodo Payments (merchant of record): products, hosted checkout, subscriptions, customer portal, webhook signatures.

Env: DODO_API_KEY (dodo_test_... or dodo_live_...), DODO_WEBHOOK_SECRET (whsec_...), DODO_MODE=test|live.
Prices are sent in paise (INR x 100).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional

import httpx


class DodoError(RuntimeError):
    pass


def mode() -> str:
    m = os.environ.get("DODO_MODE", "").strip().lower()
    if m in ("test", "live"):
        return m
    return "live" if os.environ.get("DODO_API_KEY", "").strip().startswith("dodo_live_") else "test"


def base_url() -> str:
    return "https://live.dodopayments.com" if mode() == "live" else "https://test.dodopayments.com"


def configured() -> bool:
    return bool(os.environ.get("DODO_API_KEY", "").strip())


async def call(method: str, path: str, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    key = os.environ.get("DODO_API_KEY", "").strip()
    if not key:
        raise DodoError("DODO_API_KEY is not set")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.request(method, base_url() + path, json=body, params=params, headers={"Authorization": f"Bearer {key}"})
    if r.status_code >= 400:
        raise DodoError(f"Dodo {method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else {}


def one_time_product(name: str, price_inr: int, description: str = "") -> Dict[str, Any]:
    return {"name": name, "description": description, "tax_category": "saas",
            "price": {"type": "one_time_price", "currency": "INR", "price": int(price_inr) * 100, "discount": 0, "purchasing_power_parity": False,
                      "tax_inclusive": True}}


def recurring_product(name: str, price_inr: int, interval: str, description: str = "") -> Dict[str, Any]:
    """interval: "Month" or "Year"."""
    return {"name": name, "description": description, "tax_category": "saas",
            "price": {"type": "recurring_price", "currency": "INR", "price": int(price_inr) * 100, "discount": 0, "purchasing_power_parity": False,
                      "tax_inclusive": True, "payment_frequency_interval": interval, "payment_frequency_count": 1,
                      "subscription_period_interval": interval, "subscription_period_count": 10 if interval == "Year" else 120}}


async def product_ids_by_name() -> Dict[str, str]:
    """Existing (non-archived) products in this mode, so a sync never creates duplicates."""
    out: Dict[str, str] = {}
    page = 0
    while True:
        items = (await call("GET", "/products", params={"page_size": 100, "page_number": page, "archived": "false"})).get("items") or []
        for it in items:
            out.setdefault(it.get("name", ""), it["product_id"])
        if len(items) < 100:
            return out
        page += 1


async def create_product(body: Dict[str, Any], existing: Optional[Dict[str, str]] = None) -> str:
    """Reuses a product with the same name (updating its price), otherwise creates one."""
    pid = (existing or {}).get(body["name"])
    if pid:
        await call("PATCH", f"/products/{pid}", {"price": body["price"], "description": body.get("description", "")})
        return pid
    return (await call("POST", "/products", body))["product_id"]


async def checkout(product_id: str, email: str, name: str, return_url: str, metadata: Dict[str, str]) -> Dict[str, Any]:
    """Hosted checkout session -> {"session_id", "checkout_url"}. UPI (intent) and cards for Indian buyers."""
    return await call("POST", "/checkouts", {
        "product_cart": [{"product_id": product_id, "quantity": 1}],
        "customer": {"email": email, "name": name or email.split("@")[0]},
        "return_url": return_url,
        "metadata": metadata,
    })


async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
    body = {"cancel_at_next_billing_date": True} if at_period_end else {"status": "cancelled"}
    return await call("PATCH", f"/subscriptions/{subscription_id}", body)


async def portal_link(customer_id: str, return_url: str) -> str:
    return (await call("POST", f"/customers/{customer_id}/customer-portal/session", params={"return_url": return_url}))["link"]


def verify_webhook(headers: Any, raw: bytes, secret: Optional[str] = None) -> bool:
    """Standard Webhooks: base64(HMAC-SHA256(key, f"{id}.{timestamp}.{body}")), key = base64-decoded secret after "whsec_"."""
    secret = (secret if secret is not None else os.environ.get("DODO_WEBHOOK_SECRET", "")).strip()
    wid, ts, sigs = headers.get("webhook-id", ""), headers.get("webhook-timestamp", ""), headers.get("webhook-signature", "")
    if not (secret and wid and ts.isdigit() and sigs) or abs(time.time() - int(ts)) > 300:
        return False
    try:
        key = base64.b64decode(secret[6:] if secret.startswith("whsec_") else secret)
    except ValueError:
        return False
    expected = base64.b64encode(hmac.new(key, f"{wid}.{ts}.".encode() + raw, hashlib.sha256).digest()).decode()
    for part in sigs.split():
        version, _, sig = part.partition(",")
        if version == "v1" and hmac.compare_digest(sig, expected):
            return True
    return False
