"""
Video Studio API (the Autopilot dashboard at winplaybox.in/admin) - signed-in users, per-user data.

Auth: every call carries the user's Supabase session token (Authorization: Bearer <access_token>); the backend
checks it with Supabase Auth and loads the user's profile (role, credits, status). Super admins (role 'admin')
see everything and never pay credits; users see only their own autopilots, videos and accounts. The legacy
X-Admin-Key still works as a super-admin login for scripts.

  GET  /api/v1/studio/me                         profile, credits, plan
  GET  /api/v1/studio/catalog                    styles, captions, formats, qualities, frequencies, niches, characters
  GET  /api/v1/studio/voices?language=
  POST /api/v1/studio/ideas | /script
  GET  /api/v1/studio/autopilots                 POST to create/update, POST /{id}/delete
  GET  /api/v1/studio/jobs?limit=                POST to create (charges credits), GET /{id}
  POST /api/v1/studio/jobs/{id}/regen | /publish | /cancel | /delete  (delete = hard delete incl. files)
  GET  /api/v1/studio/status
  GET  /api/v1/studio/accounts                   connected accounts + which platforms are available
  POST /api/v1/studio/accounts/{id}/delete
  GET  /api/v1/studio/analytics                  live channel/profile stats for connected accounts + usage
  POST /api/v1/studio/requests                   "which platform next?"
  GET  /api/v1/auth/{platform}                   -> {"url"}: start OAuth (YouTube, TikTok, Instagram, Facebook, Threads, X)
  GET  /api/v1/auth/{platform}/callback          public OAuth redirect target (signed, expiring, user-bound state)
  GET  /api/v1/studio/billing                   balance, plan, plans (monthly/yearly) and credit packs
  GET  /api/v1/studio/billing/usage             credit history with video titles
  POST /api/v1/studio/billing/checkout          {kind: pack|plan, id, period} -> {"url"} Dodo hosted checkout
  POST /api/v1/studio/billing/portal | /cancel  Dodo customer portal link | cancel at period end
  POST /api/v1/billing/dodo/webhook             public, Standard Webhooks signature (DODO_WEBHOOK_SECRET)
Super admin only:
  GET  /api/v1/studio/admin/users                POST /admin/users/{id} {role, credits_delta, status, plan_id}
  GET  /api/v1/studio/admin/activity?user=&limit=
  GET  /api/v1/studio/admin/platforms            setup state of each platform's OAuth app (env names, redirect URIs)
  POST /api/v1/studio/admin/billing/sync         create missing Dodo products for packs and plans

Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WPB_VAULT_SECRET; platform app credentials in services/social_oauth.py.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route

try:
    from backend.security.zero_trust import authenticate_admin, client_ip, error, rate_limit
    from backend.services.llm_router import LLMError, llm_router
    from backend.services import social_oauth as social
    from backend.services.studio_catalog import CATALOG
    from backend.services import dodo
    from backend.security.token_vault import body_sha256, token_vault
except (ModuleNotFoundError, ImportError):
    from security.zero_trust import authenticate_admin, client_ip, error, rate_limit  # type: ignore
    from services.llm_router import LLMError, llm_router  # type: ignore
    from services import social_oauth as social  # type: ignore
    from services.studio_catalog import CATALOG  # type: ignore
    from services import dodo  # type: ignore
    from security.token_vault import body_sha256, token_vault  # type: ignore

AUTOPILOT_FIELDS = {"name", "active", "niche", "topics", "style", "language", "voice", "rate", "seconds", "captions",
                    "caption_style", "caption_position", "watermark", "music", "quality", "aspect", "platforms",
                    "schedule", "timezone", "character"}
SPEC_FIELDS = {"topic", "script", "niche", "style", "language", "voice", "rate", "seconds", "captions", "caption_style",
               "caption_position", "watermark", "music", "quality", "aspect", "platforms", "character"}
# Credits per started 30 seconds of video (a 30 s basic short = 24). Mirrors ap_job_cost() in the database.
QUALITY_COST = {"basic": 24, "good": 30, "premium": 45, "max": 70}

API_BASE = os.environ.get("AP_PUBLIC_API_BASE", "https://anydownloader-backend-vvbj.onrender.com").rstrip("/")
DASHBOARD = os.environ.get("AP_DASHBOARD_URL", "https://studio.winplaybox.in/")
# Shared with the Studio server (studio.winplaybox.in). When set, user calls must carry its HMAC signature, so only the
# Studio server can use this API; browsers and scripts calling it directly are refused.
STUDIO_SECRET = os.environ.get("STUDIO_SHARED_SECRET", "").strip().encode()


def _ok(data: Any, status: int = 200) -> JSONResponse:
    return JSONResponse({"ok": True, "data": data}, status_code=status, headers={"Cache-Control": "no-store"})


class Forbidden(Exception):
    pass


class PaymentRequired(Exception):
    pass


# --------------------------------------------------------------------------- Supabase (service role, server side only)

class _DB:
    def __init__(self) -> None:
        self._c: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

    @property
    def url(self) -> str:
        return os.environ.get("SUPABASE_URL", "").rstrip("/")

    def client(self) -> httpx.AsyncClient:
        if self._c is None:
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
            self._c = httpx.AsyncClient(headers={"apikey": key, "Authorization": f"Bearer {key}"},
                                        timeout=httpx.Timeout(30, connect=10))
        return self._c

    async def select(self, table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        r = await self.client().get(f"{self.url}/rest/v1/{table}", params=params)
        r.raise_for_status()
        return r.json()

    async def insert(self, table: str, row: Dict[str, Any], returning: bool = True) -> Dict[str, Any] | None:
        r = await self.client().post(f"{self.url}/rest/v1/{table}", json=row,
                                     headers={"Prefer": "return=representation" if returning else "return=minimal"})
        r.raise_for_status()
        return r.json()[0] if returning else None

    async def update(self, table: str, match: Dict[str, str], fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        r = await self.client().patch(f"{self.url}/rest/v1/{table}", params=match, json=fields,
                                      headers={"Prefer": "return=representation"})
        r.raise_for_status()
        return r.json()

    async def delete(self, table: str, match: Dict[str, str]) -> None:
        r = await self.client().delete(f"{self.url}/rest/v1/{table}", params=match)
        r.raise_for_status()

    async def rpc(self, fn: str, **args: Any) -> Any:
        r = await self.client().post(f"{self.url}/rest/v1/rpc/{fn}", json=args)
        r.raise_for_status()
        return r.json() if r.content else None

    async def sign(self, path: str | None, seconds: int = 3600) -> str | None:
        if not path:
            return None
        r = await self.client().post(f"{self.url}/storage/v1/object/sign/autopilot/{path}", json={"expiresIn": seconds})
        if r.status_code != 200:
            return None
        return f"{self.url}/storage/v1{r.json()['signedURL']}"

    async def remove_files(self, paths: List[str]) -> None:
        paths = [p for p in paths if p]
        if paths:
            await self.client().request("DELETE", f"{self.url}/storage/v1/object/autopilot", json={"prefixes": paths})


db = _DB()


# --------------------------------------------------------------------------- who is calling

_sessions: Dict[str, Any] = {}   # access token hash -> (expires, user)


async def _supabase_user(token: str) -> Optional[Dict[str, Any]]:
    key = hashlib.sha256(token.encode()).hexdigest()
    hit = _sessions.get(key)
    if hit and hit[0] > time.time():
        return hit[1]
    r = await db.client().get(f"{db.url}/auth/v1/user", headers={"Authorization": f"Bearer {token}"})
    user = r.json() if r.status_code == 200 else None
    if len(_sessions) > 5000:
        _sessions.clear()
    _sessions[key] = (time.time() + (60 if user else 10), user)
    return user


async def _profile(user: Dict[str, Any], rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    if rows is None:
        rows = await db.select("ap_profiles", {"user_id": f"eq.{user['id']}", "select": "*"})
    if rows:
        p = rows[0]
        if not p.get("last_seen_at") or p["last_seen_at"] < time.strftime("%Y-%m-%dT%H:%M", time.gmtime(time.time() - 300)):
            asyncio.ensure_future(db.update("ap_profiles", {"user_id": f"eq.{user['id']}"},
                                            {"last_seen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}))
        return p
    # Signed up before the sign-up trigger existed: create a regular free profile.
    meta = user.get("user_metadata") or {}
    plan = (await db.select("ap_plans", {"id": "eq.free", "select": "monthly_credits"}) or [{"monthly_credits": 0}])[0]
    p = await db.insert("ap_profiles", {"user_id": user["id"], "role": "user", "plan_id": "free",
                                        "credits": plan["monthly_credits"], "email": user.get("email"),
                                        "name": meta.get("full_name") or meta.get("name") or (user.get("email") or "").split("@")[0],
                                        "avatar": meta.get("avatar_url")})
    return p


def _token_sub(token: str) -> Optional[str]:
    try:
        payload = token.split(".")[1]
        sub = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("sub")
        ok = isinstance(sub, str) and len(sub) == 36 and all(c in "0123456789abcdef-" for c in sub)
        return sub if ok else None
    except Exception:
        return None


async def _studio_signed(request: Request) -> bool:
    """X-Studio-Sig = HMAC-SHA256(secret, "ts\\nMETHOD\\npath\\nsha256(body)"), at most 5 minutes old."""
    ts = request.headers.get("x-studio-ts", "")
    sig = request.headers.get("x-studio-sig", "")
    if not ts.isdigit() or not sig or abs(time.time() - int(ts)) > 300:
        return False
    body_hash = hashlib.sha256(await request.body()).hexdigest()
    msg = f"{ts}\n{request.method}\n{request.url.path}\n{body_hash}".encode()
    return hmac.compare_digest(hmac.new(STUDIO_SECRET, msg, hashlib.sha256).hexdigest(), sig)


async def caller(request: Request) -> Dict[str, Any]:
    """{"id", "email", "role", "admin", "profile"} or raises Forbidden."""
    if authenticate_admin(request, allow_bearer_jwt=False):
        return {"id": None, "email": "admin-key", "role": "admin", "admin": True, "profile": None}
    if STUDIO_SECRET and not await _studio_signed(request):
        raise Forbidden("Use studio.winplaybox.in")
    auth = request.headers.get("authorization", "")
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if not token or token.startswith("wpb"):
        raise Forbidden("Sign in required")
    # The login check (Supabase Auth) and the profile read run side by side: the token's own user id names the
    # profile, and it is only used after Supabase confirms that same id.
    sub = _token_sub(token)
    user, rows = await asyncio.gather(
        _supabase_user(token),
        db.select("ap_profiles", {"user_id": f"eq.{sub}", "select": "*"}) if sub else asyncio.sleep(0, None))
    if not user or not user.get("id"):
        raise Forbidden("Your session expired. Sign in again.")
    p = await _profile(user, rows if sub and sub == user["id"] else None)
    if p.get("status") == "suspended":
        raise Forbidden("This account is suspended. Contact support.")
    return {"id": user["id"], "email": user.get("email"), "role": p["role"], "admin": p["role"] == "admin", "profile": p}


async def log(request: Request, me: Dict[str, Any], action: str, target: str = "", detail: Dict[str, Any] | None = None) -> None:
    """Audit trail of what each user does (reviewed by super admins). Never stores tokens or secrets."""
    try:
        await db.insert("ap_activity", {"user_id": me.get("id"), "email": me.get("email"), "action": action,
                                        "target": str(target)[:200], "detail": detail or {}, "ip": client_ip(request),
                                        "user_agent": (request.headers.get("user-agent") or "")[:300]}, returning=False)
    except Exception:
        pass


# --------------------------------------------------------------------------- server settings set in the Studio

# Keys the super admin may set on the Platform setup page. Stored encrypted in Supabase Vault (ap_settings); a value
# saved there overrides the same Render variable, and removing it falls back to Render's value.
SETTING_KEYS = sorted({k for v in social.PLATFORMS.values() for k in v["env"]} | {"DODO_API_KEY", "DODO_WEBHOOK_SECRET", "DODO_MODE"})
_ENV_DEFAULTS = {k: os.environ.get(k, "") for k in SETTING_KEYS}
_settings: Dict[str, Any] = {"at": 0.0, "applied": set(), "meta": {}, "ready": False}


async def load_settings(force: bool = False) -> None:
    if not db.configured or (not force and time.time() - _settings["at"] < 60):
        return
    _settings["at"] = time.time()
    try:
        rows = await db.rpc("ap_get_settings") or []
        _settings["ready"] = True
    except Exception:          # settings table not created yet: Render variables only
        _settings["ready"] = False
        return
    seen = set()
    for r in rows:
        if r["key"] in SETTING_KEYS and r.get("value"):
            os.environ[r["key"]] = r["value"]
            seen.add(r["key"])
    for k in _settings["applied"] - seen:
        if _ENV_DEFAULTS.get(k):
            os.environ[k] = _ENV_DEFAULTS[k]
        else:
            os.environ.pop(k, None)
    _settings["applied"] = seen
    _settings["meta"] = {r["key"]: {"updated_at": r.get("updated_at"), "updated_by": r.get("updated_by")} for r in rows}


def route(admin_only: bool = False, needs_db: bool = True):
    def deco(fn):
        async def wrapper(request: Request) -> Response:
            if needs_db and not db.configured:
                return error(request, 503, "NotConfigured", "Backend is missing Supabase settings")
            try:
                await load_settings()
                me = await caller(request)
            except Forbidden as e:
                return error(request, 401, "AuthRequired", str(e))
            if admin_only and not me["admin"]:
                return error(request, 403, "Forbidden", "Super admin only")
            ok, _ = rate_limit("studio", me.get("id") or "admin", 300 if me["admin"] else 120, 60)
            if not ok:
                return error(request, 429, "RateLimited", "Too many requests, slow down a little")
            try:
                return await fn(request, me)
            except Forbidden as e:
                return error(request, 403, "Forbidden", str(e))
            except PaymentRequired as e:
                return error(request, 402, "NoCredits", str(e))
            except httpx.HTTPStatusError as e:
                return error(request, 502, "DatabaseError", e.response.text[:300])
            except LLMError as e:
                return error(request, 503, "LLMUnavailable", str(e))
            except (ValueError, KeyError, TypeError) as e:
                return error(request, 400, "BadRequest", str(e))
        wrapper.__name__ = fn.__name__
        return wrapper
    return deco


async def _body(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    if len(raw) > 256 * 1024:
        raise ValueError("request too large")
    data = json.loads(raw or b"{}")
    if not isinstance(data, dict):
        raise ValueError("JSON object expected")
    return data


def _mine(me: Dict[str, Any], request: Request | None = None) -> Dict[str, str]:
    """Row filter: users see their own rows; super admins see their own unless ?scope=all."""
    if me["admin"] and request is not None and request.query_params.get("scope") == "all":
        return {}
    return {"owner": "is.null"} if me["id"] is None else {"owner": f"eq.{me['id']}"}


async def _own(me: Dict[str, Any], table: str, row_id: str, columns: str = "*") -> Dict[str, Any]:
    rows = await db.select(table, {"id": f"eq.{row_id}", "select": columns + ",owner" if columns != "*" else "*"})
    if not rows:
        raise ValueError("not found")
    if not me["admin"] and rows[0].get("owner") != me["id"]:
        raise Forbidden("Not yours")
    return rows[0]


# --------------------------------------------------------------------------- profile, catalog, AI helpers

@route()
async def me_get(request: Request, me: Dict[str, Any]) -> Response:
    p = me["profile"] or {}
    plan = None
    if p.get("plan_id"):
        plan = (await db.select("ap_plans", {"id": f"eq.{p['plan_id']}", "select": "id,name,monthly_credits"}) or [None])[0]
    return _ok({"id": me["id"], "email": me["email"], "role": me["role"], "admin": me["admin"], "name": p.get("name"),
                "avatar": p.get("avatar"), "credits": None if me["admin"] else p.get("credits", 0), "plan": plan,
                "plan_period": p.get("plan_period"), "plan_renews_at": p.get("plan_renews_at")})


# --------------------------------------------------------------------------- account (profile, devices, delete)

def _session_id(request: Request) -> Optional[str]:
    """The Supabase session behind this call (claim of the already-verified access token)."""
    try:
        payload = request.headers.get("authorization", "")[7:].split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("session_id")
    except Exception:
        return None


def _signed_in(me: Dict[str, Any]) -> None:
    if not me["id"]:
        raise ValueError("Sign in with your account for this")


@route()
async def me_update(request: Request, me: Dict[str, Any]) -> Response:
    _signed_in(me)
    name = " ".join(str((await _body(request)).get("name") or "").split())[:60]
    if len(name) < 2:
        raise ValueError("Use at least 2 characters")
    await db.update("ap_profiles", {"user_id": f"eq.{me['id']}"}, {"name": name})
    await log(request, me, "account.rename", me["id"], {"name": name})
    return _ok({"name": name})


@route()
async def account_sessions(request: Request, me: Dict[str, Any]) -> Response:
    _signed_in(me)
    current = _session_id(request)
    rows = await db.rpc("ap_my_sessions", p_user=me["id"]) or []
    return _ok([{**r, "current": r["id"] == current} for r in rows])


@route()
async def account_session_revoke(request: Request, me: Dict[str, Any]) -> Response:
    _signed_in(me)
    sid = request.path_params["id"]
    if sid == _session_id(request):
        raise ValueError("Use Sign out for this device")
    if not await db.rpc("ap_revoke_session", p_user=me["id"], p_session=sid):
        raise ValueError("That device is already signed out")
    _sessions.clear()                                              # forget cached token checks right away
    await log(request, me, "account.session_revoke", sid)
    return _ok({"revoked": sid})


@route()
async def account_delete(request: Request, me: Dict[str, Any]) -> Response:
    """Permanently deletes the user: their videos' files, then the auth user (all ap_* rows cascade)."""
    _signed_in(me)
    if me["admin"]:
        raise ValueError("A super admin account cannot delete itself. Hand the role to someone else first.")
    if str((await _body(request)).get("confirm") or "").strip().lower() != (me["email"] or "").lower():
        raise ValueError("Type your email address to confirm")
    p = me["profile"] or {}
    if p.get("dodo_subscription_id"):
        try:
            await dodo.cancel_subscription(p["dodo_subscription_id"], at_period_end=False)
        except dodo.DodoError:
            raise PaymentRequired("Could not cancel your subscription. Try again in a minute.")
    jobs = await db.select("ap_jobs", {"owner": f"eq.{me['id']}", "select": "video_path,thumb_path"})
    for i in range(0, len(jobs), 100):
        await db.remove_files([x for j in jobs[i:i + 100] for x in (j.get("video_path"), j.get("thumb_path"))])
    for acc in await db.select("ap_social_accounts", {"owner": f"eq.{me['id']}", "select": "id,platform"}):
        await social.revoke(acc["platform"], await db.rpc("ap_account_token", p_id=acc["id"]) or {})
        await db.rpc("ap_delete_account", p_id=acc["id"])          # also removes the encrypted token from Vault
    await log(request, me, "account.delete", me["id"], {"email": me["email"], "videos": len(jobs)})
    r = await db.client().delete(f"{db.url}/auth/v1/admin/users/{me['id']}")
    r.raise_for_status()
    _sessions.clear()
    return _ok({"deleted": True})


# --------------------------------------------------------------------------- billing (Dodo Payments)

def payment_provider() -> str:
    return os.environ.get("AP_PAYMENT_PROVIDER", "").strip().lower() or ("dodo" if dodo.configured() else "")


def _ledger_kind(reason: str) -> str:
    r = (reason or "").lower()
    if r.startswith("refund"):
        return "refund"
    if r.startswith("payment"):
        return "purchase"
    if r.startswith("monthly"):
        return "subscription"
    if r.startswith("admin") or r.startswith("credit scale"):
        return "adjustment"
    return r.split(":")[0].split(" ")[0] or "video"


def _public(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in row.items() if not k.startswith("dodo_")}


async def _gateway_state() -> Dict[str, Any]:
    plans = await db.select("ap_plans", {"active": "eq.true", "price_inr": "gt.0", "select": "id,dodo_month_product_id,dodo_year_product_id"})
    packs = await db.select("ap_packs", {"active": "eq.true", "select": "id,dodo_product_id"})
    need = len(plans) * 2 + len(packs)
    ready = sum(bool(x["dodo_month_product_id"]) + bool(x["dodo_year_product_id"]) for x in plans) + sum(bool(x["dodo_product_id"]) for x in packs)
    return {"provider": payment_provider() or None, "mode": dodo.mode() if dodo.configured() else None, "configured": dodo.configured(),
            "webhook": bool(os.environ.get("DODO_WEBHOOK_SECRET", "").strip()), "products_ready": ready, "products_needed": need,
            "webhook_url": f"{API_BASE}/api/v1/billing/dodo/webhook"}


@route()
async def billing_get(request: Request, me: Dict[str, Any]) -> Response:
    """Balance, current plan, every plan (monthly and yearly prices) and every one-time pack."""
    plans = await db.select("ap_plans", {"active": "eq.true", "select": "*", "order": "sort.asc"})
    packs = await db.select("ap_packs", {"active": "eq.true", "select": "id,credits,price_inr", "order": "sort.asc"})
    p = me["profile"] or {}
    out = {"credits": None if me["admin"] else p.get("credits", 0), "admin": me["admin"],
           "plan_id": p.get("plan_id") or "free", "plan_period": p.get("plan_period"), "plan_renews_at": p.get("plan_renews_at"),
           "plan_cancel_at": p.get("plan_cancel_at"), "subscription": bool(p.get("dodo_subscription_id")),
           "portal": bool(p.get("dodo_customer_id")), "plans": [_public(x) for x in plans], "packs": packs,
           "short_cost": QUALITY_COST["basic"], "costs": QUALITY_COST, "payments": payment_provider() == "dodo" and dodo.configured()}
    if me["admin"]:
        out["gateway"] = await _gateway_state()
    return _ok(out)


@route()
async def billing_usage(request: Request, me: Dict[str, Any]) -> Response:
    """Credit history, newest first, with the video title for video charges and refunds."""
    if not me["id"]:
        return _ok([])
    rows = await db.select("ap_credit_ledger", {"user_id": f"eq.{me['id']}", "select": "id,delta,reason,kind,title,job_id,created_at",
                                                 "order": "created_at.desc", "limit": "200"})
    job_ids = sorted({r["job_id"] for r in rows if r.get("job_id")})
    titles: Dict[str, str] = {}
    if job_ids:
        jobs = await db.select("ap_jobs", {"id": f"in.({','.join(job_ids)})", "select": "id,title:result->>title,topic:spec->>topic"})
        titles = {j["id"]: j.get("title") or j.get("topic") or "" for j in jobs}
    out = []
    for r in rows:
        kind = r.get("kind") or _ledger_kind(r.get("reason", ""))
        out.append({"id": r["id"], "delta": r["delta"], "kind": kind, "created_at": r["created_at"],
                    "title": r.get("title") or titles.get(r.get("job_id") or "", "")})
    return _ok(out)


@route()
async def billing_checkout(request: Request, me: Dict[str, Any]) -> Response:
    """Creates an order for a pack or a plan and returns the Dodo hosted checkout URL for it."""
    if not me["id"]:
        raise ValueError("The admin key cannot buy credits")
    b = await request.json()
    kind, item = str(b.get("kind") or ""), str(b.get("id") or "")
    if kind == "pack":
        pack = (await db.select("ap_packs", {"id": f"eq.{item}", "active": "eq.true", "select": "*"}) or [None])[0]
        if not pack:
            raise ValueError("Unknown pack")
        order = {"kind": "pack", "item_id": item, "period": None, "amount_inr": pack["price_inr"], "credits": pack["credits"]}
        product = pack.get("dodo_product_id")
    elif kind == "plan":
        period = "year" if b.get("period") == "year" else "month"
        plan = (await db.select("ap_plans", {"id": f"eq.{item}", "active": "eq.true", "select": "*"}) or [None])[0]
        if not plan or not plan["price_inr"]:
            raise ValueError("Unknown plan")
        p = me["profile"] or {}
        if p.get("dodo_subscription_id") and p.get("plan_id") == item and p.get("plan_period") == period and not p.get("plan_cancel_at"):
            raise ValueError("You are already on this plan")
        order = {"kind": "plan", "item_id": item, "period": period,
                 "amount_inr": plan["price_year_inr"] if period == "year" else plan["price_inr"],
                 "credits": plan["monthly_credits"] * (12 if period == "year" else 1)}
        product = plan.get("dodo_year_product_id" if period == "year" else "dodo_month_product_id")
    else:
        raise ValueError("Pick a pack or a plan")
    if payment_provider() != "dodo" or not dodo.configured() or not product:
        await log(request, me, "billing.interest", item, order)
        raise PaymentRequired("Online payments are being set up. Your choice is noted; please try again soon.")
    saved = await db.insert("ap_orders", {**order, "user_id": me["id"], "provider": "dodo"})
    try:
        session = await dodo.checkout(product, me["email"] or "", (me["profile"] or {}).get("name") or "",
                                      f"{DASHBOARD}?billing=done#billing", {"order_id": saved["id"], "user_id": me["id"]})
    except dodo.DodoError as e:
        await db.update("ap_orders", {"id": f"eq.{saved['id']}"}, {"status": "failed"})
        await log(request, me, "billing.error", saved["id"], {"error": str(e)[:300]})
        raise PaymentRequired("Checkout could not start. Please try again in a minute.")
    await log(request, me, "billing.checkout", saved["id"], order)
    return _ok({"url": session["checkout_url"], "order_id": saved["id"]})


@route()
async def billing_portal(request: Request, me: Dict[str, Any]) -> Response:
    """Dodo customer portal: invoices, payment method, subscription."""
    cid = (me["profile"] or {}).get("dodo_customer_id")
    if not cid:
        raise ValueError("No payments yet")
    try:
        return _ok({"url": await dodo.portal_link(cid, f"{DASHBOARD}#billing")})
    except dodo.DodoError:
        raise PaymentRequired("The billing portal is not available right now. Try again in a minute.")


@route()
async def billing_cancel(request: Request, me: Dict[str, Any]) -> Response:
    """Cancels at the end of the paid period; credits already added stay."""
    p = me["profile"] or {}
    sid = p.get("dodo_subscription_id")
    if not sid:
        raise ValueError("You have no active subscription")
    try:
        await dodo.cancel_subscription(sid, at_period_end=True)
    except dodo.DodoError:
        raise PaymentRequired("Could not cancel right now. Try again in a minute.")
    await db.update("ap_profiles", {"user_id": f"eq.{me['id']}"}, {"plan_cancel_at": p.get("plan_renews_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    await log(request, me, "billing.cancel", sid, {"plan": p.get("plan_id")})
    return _ok({"cancel_at": p.get("plan_renews_at")})


@route(admin_only=True)
async def admin_billing_sync(request: Request, me: Dict[str, Any]) -> Response:
    """Creates the Dodo products that are missing (one per pack, one monthly and one yearly per paid plan)."""
    if not dodo.configured():
        raise ValueError("Set DODO_API_KEY on the backend first")
    created = []
    existing = await dodo.product_ids_by_name()
    for pk in await db.select("ap_packs", {"active": "eq.true", "dodo_product_id": "is.null", "select": "*"}):
        pid = await dodo.create_product(dodo.one_time_product(f"WinPlayBox Studio - {pk['credits']:,} credits", pk["price_inr"],
                                                              "One-time credit pack. Credits never expire."), existing)
        await db.update("ap_packs", {"id": f"eq.{pk['id']}"}, {"dodo_product_id": pid})
        created.append(pk["id"])
    for pl in await db.select("ap_plans", {"active": "eq.true", "price_inr": "gt.0", "select": "*"}):
        for period, col, interval, price in (("month", "dodo_month_product_id", "Month", pl["price_inr"]),
                                             ("year", "dodo_year_product_id", "Year", pl["price_year_inr"])):
            if pl.get(col) or not price:
                continue
            credits = pl["monthly_credits"] * (12 if period == "year" else 1)
            pid = await dodo.create_product(dodo.recurring_product(f"WinPlayBox Studio {pl['name']} ({period}ly)", price, interval,
                                                                   f"{credits:,} credits per {period}. Credits never expire."), existing)
            await db.update("ap_plans", {"id": f"eq.{pl['id']}"}, {col: pid})
            created.append(f"{pl['id']}:{period}")
    await log(request, me, "admin.billing_sync", "dodo", {"created": created})
    return _ok({"created": created, **(await _gateway_state())})


def _order_meta(data: Dict[str, Any]) -> Dict[str, Any]:
    return data.get("metadata") or {}


async def _renewal_order(sub_id: str, payment_id: str) -> Optional[str]:
    """A renewal charge of an existing subscription: a new paid order for the next period, same plan."""
    first = (await db.select("ap_orders", {"subscription_id": f"eq.{sub_id}", "select": "*", "order": "created_at.asc", "limit": "1"}) or [None])[0]
    if not first:
        return None
    o = await db.insert("ap_orders", {"user_id": first["user_id"], "kind": "plan", "item_id": first["item_id"], "period": first["period"],
                                      "amount_inr": first["amount_inr"], "credits": first["credits"], "provider": "dodo",
                                      "subscription_id": sub_id})
    return o["id"]


async def dodo_webhook(request: Request) -> Response:
    """Dodo -> us. Signed (Standard Webhooks); idempotent, since Dodo retries."""
    await load_settings()
    raw = await request.body()
    if not dodo.verify_webhook(request.headers, raw):
        return JSONResponse({"ok": False}, status_code=401)
    try:
        event = json.loads(raw)
    except ValueError:
        return JSONResponse({"ok": False}, status_code=400)
    kind, data = event.get("type", ""), event.get("data") or {}
    meta = _order_meta(data)
    customer = data.get("customer") or {}
    try:
        if kind == "payment.succeeded":
            pay_id = data.get("payment_id")
            sub_id = data.get("subscription_id")
            if pay_id and await db.select("ap_orders", {"provider_ref": f"eq.{pay_id}", "select": "id"}):
                return JSONResponse({"ok": True, "duplicate": True})
            order_id = meta.get("order_id")
            order = (await db.select("ap_orders", {"id": f"eq.{order_id}", "select": "*"}) or [None])[0] if order_id else None
            if order and order["status"] != "created" and sub_id:
                order_id = await _renewal_order(sub_id, pay_id)          # metadata of a renewal points at the first order
            elif not order and sub_id:
                order_id = await _renewal_order(sub_id, pay_id)
            if order_id:
                if sub_id:
                    await db.update("ap_orders", {"id": f"eq.{order_id}"}, {"subscription_id": sub_id})
                await db.rpc("ap_apply_order", p_order=order_id, p_provider_ref=pay_id)
                owner = (await db.select("ap_orders", {"id": f"eq.{order_id}", "select": "user_id"}) or [{}])[0].get("user_id")
                if owner and customer.get("customer_id"):
                    await db.update("ap_profiles", {"user_id": f"eq.{owner}"}, {"dodo_customer_id": customer["customer_id"]})
        elif kind == "payment.failed" and meta.get("order_id"):
            await db.update("ap_orders", {"id": f"eq.{meta['order_id']}", "status": "eq.created"}, {"status": "failed"})
        elif kind in ("subscription.active", "subscription.renewed") and meta.get("user_id"):
            uid, sub_id = meta["user_id"], data.get("subscription_id")
            prof = (await db.select("ap_profiles", {"user_id": f"eq.{uid}", "select": "dodo_subscription_id"}) or [{}])[0]
            old = prof.get("dodo_subscription_id")
            if old and sub_id and old != sub_id:                         # switched plan: stop the previous subscription
                try:
                    await dodo.cancel_subscription(old, at_period_end=False)
                except dodo.DodoError:
                    pass
            fields = {"dodo_subscription_id": sub_id, "plan_cancel_at": None}
            if customer.get("customer_id"):
                fields["dodo_customer_id"] = customer["customer_id"]
            if data.get("next_billing_date"):
                fields["plan_renews_at"] = data["next_billing_date"]
            await db.update("ap_profiles", {"user_id": f"eq.{uid}"}, fields)
            if meta.get("order_id") and sub_id:
                await db.update("ap_orders", {"id": f"eq.{meta['order_id']}"}, {"subscription_id": sub_id})
        elif kind in ("subscription.cancelled", "subscription.expired", "subscription.failed") and data.get("subscription_id"):
            rows = await db.select("ap_profiles", {"dodo_subscription_id": f"eq.{data['subscription_id']}", "select": "user_id,plan_renews_at"})
            for r in rows:
                await db.update("ap_profiles", {"user_id": f"eq.{r['user_id']}"},
                                {"plan_cancel_at": r.get("plan_renews_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    except Exception as e:  # tell Dodo to retry later
        print(f"dodo webhook {kind} failed: {e}")
        return JSONResponse({"ok": False}, status_code=500)
    return JSONResponse({"ok": True})


@route(needs_db=False)
async def catalog(request: Request, me: Dict[str, Any]) -> Response:
    return _ok(CATALOG)


_voices: Dict[str, Any] = {"at": 0, "list": []}


@route(needs_db=False)
async def voices(request: Request, me: Dict[str, Any]) -> Response:
    if time.time() - _voices["at"] > 86400 or not _voices["list"]:
        import edge_tts
        raw = await edge_tts.list_voices()
        out = []
        for v in raw:
            friendly = v.get("FriendlyName", "")
            out.append({"id": v["ShortName"], "name": v["ShortName"].split("-")[-1].replace("Neural", ""),
                        "gender": v.get("Gender", ""), "locale": v["Locale"],
                        "language": friendly.split(" - ", 1)[1] if " - " in friendly else v["Locale"]})
        _voices.update(at=time.time(), list=sorted(out, key=lambda x: (x["language"], x["id"])))
    q = (request.query_params.get("language") or "").lower()
    items = [v for v in _voices["list"] if not q or v["language"].lower().startswith(q) or v["locale"].lower() == q]
    return _ok({"count": len(items), "languages": len({v["language"] for v in _voices["list"]}), "voices": items})


IDEAS_SYSTEM = ("You are a short-form video strategist who finds ideas that get views on YouTube Shorts, Instagram "
                "Reels and TikTok. Ideas must be specific, have a curiosity gap, be factually safe, and fit in under "
                "a minute. Reply with JSON only.")
SCRIPT_SYSTEM = ("You write narration for short videos: a hook in the first two seconds, one idea per line, concrete "
                 "examples, a payoff and a short call to action. Facts must be accurate and mainstream; never invent "
                 "study names or numbers. Each line is 1-2 short spoken sentences (5-7 seconds). Reply with JSON only.")


@route(needs_db=False)
async def ideas(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    niche = str(b.get("niche") or "interesting facts")[:300]
    lang = str(b.get("language") or "English")[:40]
    n = max(1, min(int(b.get("count") or 10), 20))
    obj, res = await llm_router.complete_json(
        IDEAS_SYSTEM,
        f"Niche: {niche}\nAudience language: {lang}\nGive {n} fresh video ideas. Write title and hook in {lang}.\n"
        'Return {"ideas": [{"title": "...", "hook": "first spoken line", "why": "why it will get views"}]}',
        temperature=0.9, max_tokens=3000, budget_s=110.0)
    if db.configured:
        await log(request, me, "ideas", niche)
    return _ok({"ideas": obj.get("ideas", [])[:n], "provider": res.provider})


@route(needs_db=False)
async def script(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    topic = str(b.get("topic") or "").strip()[:500]
    if not topic:
        raise ValueError("topic is required")
    lang = str(b.get("language") or "English")[:40]
    seconds = max(15, min(int(b.get("seconds") or 60), 600))
    note = ("Hindi in Devanagari with common English words in English" if lang.lower() == "hindi" else
            "Hinglish: Hindi in Devanagari mixed with English words" if lang.lower() == "hinglish" else
            f"{lang}, natural spoken style, in its own script")
    obj, res = await llm_router.complete_json(
        SCRIPT_SYSTEM,
        f"Topic: {topic}\nNiche: {b.get('niche') or 'general'}\nLanguage: {note}\n"
        f"Length: about {seconds} seconds ({max(4, round(seconds / 6.5))} lines).\n"
        'Return {"title": "...", "lines": ["...", "..."], "description": "...", "hashtags": ["#..."]}',
        temperature=0.85, max_tokens=6000, budget_s=110.0)
    if db.configured:
        await log(request, me, "script", topic)
    return _ok({**obj, "provider": res.provider})


# --------------------------------------------------------------------------- autopilots

@route()
async def autopilots_list(request: Request, me: Dict[str, Any]) -> Response:
    return _ok(await db.select("ap_autopilots", {"select": "*", "order": "created_at.desc", **_mine(me, request)}))


async def _check_accounts(me: Dict[str, Any], platforms: Any) -> None:
    """Users can only post to accounts they connected themselves."""
    ids = [i for c in (platforms or {}).values() if isinstance(c, dict) for i in (c.get("account_ids") or [])]
    if not ids or me["admin"]:
        return
    rows = await db.select("ap_social_accounts", {"id": "in.(" + ",".join(ids) + ")", "select": "id,owner"})
    if len(rows) != len(set(ids)) or any(r["owner"] != me["id"] for r in rows):
        raise Forbidden("You can only post to accounts you connected")


@route()
async def autopilots_save(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    row = {k: v for k, v in b.items() if k in AUTOPILOT_FIELDS}
    await _check_accounts(me, row.get("platforms"))
    if b.get("id"):
        await _own(me, "ap_autopilots", str(b["id"]), "id")
        saved = (await db.update("ap_autopilots", {"id": f"eq.{b['id']}"}, row) or [None])[0]
        await log(request, me, "autopilot.update", b["id"], {"fields": sorted(row)})
        return _ok(saved)
    if not row.get("name"):
        raise ValueError("name is required")
    if not me["admin"]:
        plan = (await db.select("ap_plans", {"id": f"eq.{me['profile']['plan_id']}", "select": "max_autopilots"}) or [{"max_autopilots": 1}])[0]
        count = len(await db.select("ap_autopilots", {"owner": f"eq.{me['id']}", "select": "id"}))
        if plan["max_autopilots"] is not None and count >= plan["max_autopilots"]:
            raise PaymentRequired(f"Your plan allows {plan['max_autopilots']} autopilot(s). Upgrade to add more.")
    row["owner"] = me["id"]
    saved = await db.insert("ap_autopilots", row)
    await log(request, me, "autopilot.create", saved["id"], {"name": row.get("name"), "niche": row.get("niche")})
    return _ok(saved, 201)


@route()
async def autopilots_delete(request: Request, me: Dict[str, Any]) -> Response:
    rid = request.path_params["id"]
    await _own(me, "ap_autopilots", rid, "id")
    await db.delete("ap_autopilots", {"id": f"eq.{rid}"})
    await log(request, me, "autopilot.delete", rid)
    return _ok({"deleted": rid})


# --------------------------------------------------------------------------- jobs (videos)

JOB_LIST_COLUMNS = ("id,owner,autopilot_id,kind,status,progress,stage,error,spec->>topic,spec->>style,spec->>language,"
                    "spec->>aspect,result->>title,result->>duration,publish,thumb_path,created_at,finished_at,attempts")


def job_cost(spec: Dict[str, Any]) -> int:
    halves = max(1, -(-int(spec.get("seconds") or 60) // 30))
    return halves * QUALITY_COST.get(str(spec.get("quality") or "good"), QUALITY_COST["good"])


@route()
async def jobs_list(request: Request, me: Dict[str, Any]) -> Response:
    limit = max(1, min(int(request.query_params.get("limit") or 50), 200))
    params = {"select": JOB_LIST_COLUMNS, "order": "created_at.desc", "limit": str(limit), **_mine(me, request)}
    if request.query_params.get("autopilot"):
        params["autopilot_id"] = f"eq.{request.query_params['autopilot']}"
    rows = await db.select("ap_jobs", params)
    signed = await asyncio.gather(*(db.sign(r.pop("thumb_path", None)) for r in rows))
    for r, url in zip(rows, signed):
        r["thumb_url"] = url
    return _ok(rows)


@route()
async def job_get(request: Request, me: Dict[str, Any]) -> Response:
    job = await _own(me, "ap_jobs", request.path_params["id"])
    job["video_url"], job["thumb_url"] = await asyncio.gather(db.sign(job.get("video_path")), db.sign(job.get("thumb_path")))
    return _ok(job)


# How many videos one user may have queued or rendering at the same time (super admins: no limit). Keeps one
# busy account from filling the queue; the worker also takes users in turn (ap_claim_job).
QUEUE_LIMITS = {"free": 2, "creator": 3, "pro": 5, "studio": 8}
QUEUE_LIMIT_DEFAULT = 15
REGEN_COST = 10   # a regenerate re-renders the whole video


async def _queue_room(me: Dict[str, Any]) -> None:
    if me["admin"] or not me["id"]:
        return
    limit = QUEUE_LIMITS.get((me["profile"] or {}).get("plan_id") or "free", QUEUE_LIMIT_DEFAULT)
    busy = await db.select("ap_jobs", {"owner": f"eq.{me['id']}", "status": "in.(queued,running)", "select": "id"})
    if len(busy) >= limit:
        raise ValueError(f"You already have {len(busy)} video(s) in progress; your plan allows {limit} at a time. "
                         "Start this one when one of them finishes.")


async def _insert_job_or_refund(me: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
    """Credits were taken just before: give them back if the job cannot be saved."""
    try:
        return await db.insert("ap_jobs", row)
    except Exception:
        if row.get("credits"):
            await db.rpc("ap_charge", p_user=me["id"], p_amount=-int(row["credits"]), p_reason="refund: video could not be queued",
                         p_job=None)
        raise


async def _charge(me: Dict[str, Any], cost: int, job_id: str, reason: str) -> int:
    if me["admin"] or cost <= 0:
        return 0
    if not await db.rpc("ap_charge", p_user=me["id"], p_amount=cost, p_reason=reason, p_job=job_id):
        raise PaymentRequired(f"This video needs {cost} credit(s); you have {me['profile'].get('credits', 0)}.")
    return cost


@route()
async def jobs_create(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    spec = {k: v for k, v in (b.get("spec") or {}).items() if k in SPEC_FIELDS}
    if not spec.get("topic") and not spec.get("niche") and not b.get("story"):
        raise ValueError("give a topic, a niche or a story")
    await _check_accounts(me, spec.get("platforms"))
    await _queue_room(me)
    job_id = str(uuid.uuid4())
    credits = await _charge(me, job_cost(spec), job_id, "video")
    row = {"id": job_id, "kind": "make", "spec": spec, "owner": me["id"], "credits": credits}
    if b.get("story"):
        row["story"] = b["story"]
    saved = await _insert_job_or_refund(me, row)
    await log(request, me, "video.create", job_id, {"topic": spec.get("topic"), "style": spec.get("style"), "credits": credits})
    return _ok(saved, 201)


@route()
async def job_regen(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    src = await _own(me, "ap_jobs", request.path_params["id"], "id,spec")
    regen = {k: b[k] for k in ("scene", "say", "image", "new_picture") if k in b}
    await _queue_room(me)
    job_id = str(uuid.uuid4())
    credits = await _charge(me, REGEN_COST, job_id, "regen")
    row: Dict[str, Any] = {"id": job_id, "credits": credits, "kind": "regen", "owner": me["id"] if not me["admin"] else src.get("owner"),
                           "spec": {"source_job": src["id"], "regen": regen,
                                    "overrides": {k: v for k, v in (b.get("overrides") or {}).items() if k in SPEC_FIELDS}}}
    if b.get("story"):
        row["story"] = b["story"]
    saved = await _insert_job_or_refund(me, row)
    await log(request, me, "video.regen", src["id"], {"scene": regen.get("scene")})
    return _ok(saved, 201)


@route()
async def job_publish(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    src = await _own(me, "ap_jobs", request.path_params["id"], "id")
    platforms = b.get("platforms") or {}
    if not isinstance(platforms, dict) or not platforms:
        raise ValueError("choose at least one account")
    await _check_accounts(me, platforms)
    saved = await db.insert("ap_jobs", {"kind": "publish", "owner": src.get("owner"),
                                        "spec": {"source_job": src["id"], "platforms": platforms}})
    await log(request, me, "video.publish", src["id"], {"platforms": sorted(platforms)})
    return _ok(saved, 201)


@route()
async def job_cancel(request: Request, me: Dict[str, Any]) -> Response:
    job = await _own(me, "ap_jobs", request.path_params["id"], "id,status")
    if job["status"] != "queued":
        return error(request, 409, "NotQueued", "only queued videos can be canceled")
    await db.rpc("ap_fail_job", p_job=job["id"], p_error="canceled by user")   # refunds credits
    await db.update("ap_jobs", {"id": f"eq.{job['id']}"}, {"status": "canceled"})
    await log(request, me, "video.cancel", job["id"])
    return _ok({"canceled": job["id"]})


@route()
async def job_delete(request: Request, me: Dict[str, Any]) -> Response:
    """Hard delete: the video, its thumbnail, and its row. Posts already published on platforms stay there."""
    job = await _own(me, "ap_jobs", request.path_params["id"], "id,status,video_path,thumb_path")
    if job["status"] == "running":
        return error(request, 409, "Busy", "This video is being made right now; delete it when it finishes")
    await db.remove_files([job.get("video_path"), job.get("thumb_path")])
    await db.delete("ap_jobs", {"id": f"eq.{job['id']}"})
    await log(request, me, "video.delete", job["id"])
    return _ok({"deleted": job["id"]})


@route()
async def status(request: Request, me: Dict[str, Any]) -> Response:
    rows = await db.select("ap_jobs", {"select": "status", "order": "created_at.desc", "limit": "500", **_mine(me)})
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 600))
    recent = await db.select("ap_jobs", {"select": "worker_id", "heartbeat_at": f"gte.{since}", "worker_id": "not.is.null"})
    return _ok({"counts": counts, "workers_online": len({r["worker_id"] for r in recent}),
                **({"workers": sorted({r["worker_id"] for r in recent})} if me["admin"] else {})})


# --------------------------------------------------------------------------- connected accounts + OAuth

def _redirect_uri(platform: str) -> str:
    return f"{API_BASE}/api/v1/auth/{platform}/callback"


def _sign(body: str) -> str:
    key = (social.env("WPB_VAULT_SECRET") or "dev-only-state-key").encode()
    return base64.urlsafe_b64encode(hmac.new(key, body.encode(), hashlib.sha256).digest()).decode().rstrip("=")


def _make_state(platform: str, nonce: str, user_id: Optional[str], popup: bool = False) -> str:
    body = base64.urlsafe_b64encode(json.dumps(
        {"p": platform, "u": user_id, "n": nonce, "exp": int(time.time()) + 600, "w": 1 if popup else 0}).encode()).decode().rstrip("=")
    return f"{body}.{_sign(body)}"


def _read_state(state: str, platform: str) -> Dict[str, Any] | None:
    try:
        body, sig = state.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body)):
            return None
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        return data if data.get("p") == platform and data.get("exp", 0) > time.time() else None
    except Exception:
        return None


ACCOUNT_COLUMNS = "id,platform,external_id,name,avatar,status,error,created_at,updated_at"


@route()
async def accounts_list(request: Request, me: Dict[str, Any]) -> Response:
    rows = await db.select("ap_social_accounts", {"select": ACCOUNT_COLUMNS, "order": "created_at.asc", **_mine(me, request)})
    platforms = {k: {"label": v["label"], "about": v["about"], "available": social.configured(k)}
                 for k, v in social.PLATFORMS.items()}
    return _ok({"accounts": rows, "platforms": platforms})


@route()
async def oauth_start(request: Request, me: Dict[str, Any]) -> Response:
    """GET /api/v1/auth/{platform} -> {"url"} of the platform's own sign-in page, bound to this user."""
    platform = request.path_params["platform"]
    if platform not in social.PLATFORMS:
        return error(request, 404, "NotFound", "unknown platform")
    if not social.configured(platform):
        return error(request, 503, "Unavailable", f"{social.PLATFORMS[platform]['label']} connections are not available yet")
    nonce, challenge = secrets.token_urlsafe(16), None
    if social.PLATFORMS[platform]["pkce"]:
        verifier, challenge = social.pkce_pair()
        await db.insert("ap_oauth_states", {"nonce": nonce, "platform": platform, "verifier": verifier, "user_id": me["id"]},
                        returning=False)
    await log(request, me, "account.connect_start", platform)
    return _ok({"url": social.authorize_url(platform, _redirect_uri(platform), _make_state(platform, nonce, me["id"], request.query_params.get("popup") == "1"), challenge)})


def _back(platform: str, ok: bool, msg: str = "", popup: bool = False) -> Response:
    """Back to the Studio; "popup=1" tells a sign-in popup to report to the Studio tab and close."""
    q = urlencode({"connected" if ok else "connect_error": platform, **({"msg": msg[:200]} if msg else {}), **({"popup": "1"} if popup else {})})
    return RedirectResponse(f"{DASHBOARD}?{q}#publish", status_code=302)


async def oauth_callback(request: Request) -> Response:
    """Public: the platform sends the browser here. Trust comes from the signed state, which names the user."""
    await load_settings()
    platform = request.path_params["platform"]
    q = request.query_params
    if platform not in social.PLATFORMS:
        return _back(platform, False, "Unknown platform.")
    state = _read_state(q.get("state", ""), platform)
    popup = bool((state or {}).get("w"))
    if not state:
        return _back(platform, False, "This sign-in link expired. Click Connect again.")  # no state: cannot know
    if q.get("error"):
        return _back(platform, False, q.get("error_description") or q.get("error_reason") or q["error"], popup)
    if not db.configured:
        return _back(platform, False, "Service is not available right now.", popup)
    verifier = None
    if social.PLATFORMS[platform]["pkce"]:
        rows = await db.select("ap_oauth_states", {"nonce": f"eq.{state['n']}", "select": "verifier,user_id"})
        if not rows or rows[0].get("user_id") != state.get("u"):
            return _back(platform, False, "This sign-in link was already used. Click Connect again.", popup)
        verifier = rows[0]["verifier"]
        await db.delete("ap_oauth_states", {"nonce": f"eq.{state['n']}"})
    who = {"id": state.get("u"), "email": None}
    try:
        accounts = await social.complete(platform, q.get("code", ""), _redirect_uri(platform), verifier)
        for a in accounts:
            await db.rpc("ap_save_account", p_owner=state.get("u"), p_platform=a["platform"], p_external_id=a["external_id"],
                         p_name=a["name"], p_avatar=a["avatar"], p_token=a["token"])
        await log(request, who, "account.connected", platform, {"accounts": [a["name"] for a in accounts]})
        return _back(platform, True, ", ".join(a["name"] for a in accounts), popup)
    except social.OAuthError as e:
        await log(request, who, "account.connect_failed", platform, {"error": str(e)[:200]})
        return _back(platform, False, str(e), popup)
    except httpx.HTTPError as e:
        return _back(platform, False, f"network error: {type(e).__name__}", popup)


@route()
async def accounts_delete(request: Request, me: Dict[str, Any]) -> Response:
    acc = await _own(me, "ap_social_accounts", request.path_params["id"], "id,platform,name")
    token = await db.rpc("ap_account_token", p_id=acc["id"]) or {}
    revoked = await social.revoke(acc["platform"], token)            # platform side first, then our encrypted copy
    await db.rpc("ap_delete_account", p_id=acc["id"])
    await log(request, me, "account.disconnect", acc["id"], {"platform": acc["platform"], "name": acc["name"], "revoked": revoked})
    return _ok({"deleted": acc["id"]})


@route()
async def platform_request(request: Request, me: Dict[str, Any]) -> Response:
    text = str((await _body(request)).get("text") or "").strip()[:300]
    if len(text) < 2:
        raise ValueError("tell us which platform")
    await db.insert("ap_platform_requests", {"text": text, "owner": me["id"]}, returning=False)
    await log(request, me, "platform.request", text)
    return _ok({"saved": True}, 201)


# --------------------------------------------------------------------------- analytics

_stats_cache: Dict[str, Any] = {}


async def _account_stats(acc: Dict[str, Any]) -> Dict[str, Any]:
    hit = _stats_cache.get(acc["id"])
    if hit and hit[0] > time.time():
        return hit[1]
    token = await db.rpc("ap_account_token", p_id=acc["id"]) or {}
    try:
        stats, fresh = await social.stats(acc["platform"], acc["external_id"], token)
        if fresh:
            await db.rpc("ap_update_account", p_id=acc["id"], p_token=fresh, p_status="connected", p_error=None)
        out = {"ok": True, **stats}
    except social.TokenRevoked as e:
        await db.rpc("ap_update_account", p_id=acc["id"], p_token=None, p_status="expired", p_error=str(e)[:300])
        out = {"ok": False, "error": str(e), "expired": True}
    except Exception as e:
        out = {"ok": False, "error": str(e)[:200]}
    _stats_cache[acc["id"]] = (time.time() + 300, out)
    return out


@route()
async def analytics(request: Request, me: Dict[str, Any]) -> Response:
    accs = await db.select("ap_social_accounts", {"select": ACCOUNT_COLUMNS, "order": "created_at.asc", **_mine(me, request)})
    stats = await asyncio.gather(*(_account_stats(a) for a in accs))
    jobs = await db.select("ap_jobs", {"select": "status,kind,publish,credits,created_at", "order": "created_at.desc",
                                       "limit": "1000", **_mine(me, request)})
    made = [j for j in jobs if j["kind"] == "make"]
    posts = sum(1 for j in jobs for p in (j.get("publish") or {}).values() if isinstance(p, dict)
                for x in (p.get("posts") or [p]) if x.get("status") == "published")
    by_day: Dict[str, int] = {}
    for j in made:
        d = j["created_at"][:10]
        by_day[d] = by_day.get(d, 0) + 1
    return _ok({"accounts": [{**a, "stats": s} for a, s in zip(accs, stats)],
                "usage": {"videos": len(made), "ready": sum(j["status"] == "done" for j in made),
                          "failed": sum(j["status"] == "failed" for j in made), "posts": posts,
                          "credits_used": sum(j.get("credits") or 0 for j in jobs),
                          "credits_left": None if me["admin"] else me["profile"].get("credits"),
                          "per_day": sorted(by_day.items())[-30:]}})


# --------------------------------------------------------------------------- super admin

@route(admin_only=True)
async def admin_users(request: Request, me: Dict[str, Any]) -> Response:
    users = await db.select("ap_profiles", {"select": "user_id,email,name,avatar,role,plan_id,credits,status,created_at,last_seen_at",
                                            "order": "created_at.desc", "limit": "500"})
    return _ok(users)


@route(admin_only=True)
async def admin_user_update(request: Request, me: Dict[str, Any]) -> Response:
    uid = request.path_params["id"]
    b = await _body(request)
    fields = {}
    if b.get("status") in ("active", "suspended"):
        fields["status"] = b["status"]
    if b.get("plan_id"):
        fields["plan_id"] = str(b["plan_id"])
    if b.get("role") in ("admin", "user"):
        if uid == me["id"] and b["role"] != "admin":
            raise ValueError("you cannot remove your own super admin role")
        fields["role"] = b["role"]
    if fields:
        await db.update("ap_profiles", {"user_id": f"eq.{uid}"}, fields)
    delta = int(b.get("credits_delta") or 0)
    if delta:
        p = (await db.select("ap_profiles", {"user_id": f"eq.{uid}", "select": "credits"}) or [{"credits": 0}])[0]
        await db.update("ap_profiles", {"user_id": f"eq.{uid}"}, {"credits": max(0, p["credits"] + delta)})
        await db.insert("ap_credit_ledger", {"user_id": uid, "delta": delta, "reason": f"admin adjustment by {me['email']}"}, returning=False)
    await log(request, me, "admin.user_update", uid, {**fields, "credits_delta": delta})
    return _ok((await db.select("ap_profiles", {"user_id": f"eq.{uid}", "select": "*"}) or [None])[0])


@route(admin_only=True)
async def admin_activity(request: Request, me: Dict[str, Any]) -> Response:
    params = {"select": "*", "order": "created_at.desc", "limit": str(max(1, min(int(request.query_params.get("limit") or 200), 1000)))}
    if request.query_params.get("user"):
        params["user_id"] = f"eq.{request.query_params['user']}"
    if request.query_params.get("action"):
        params["action"] = f"like.{request.query_params['action']}*"
    return _ok(await db.select("ap_activity", params))


@route(admin_only=True, needs_db=False)
async def admin_platforms(request: Request, me: Dict[str, Any]) -> Response:
    """For the site owner only: what each platform's OAuth app still needs (never returns secret values)."""
    return _ok({k: {"label": v["label"], "about": v["about"], "configured": social.configured(k), "env": v["env"], "steps": v["steps"],
                    "note": v["note"], "redirect_uri": _redirect_uri(k)} for k, v in social.PLATFORMS.items()})


def _setting_state(key: str) -> Dict[str, Any]:
    v = os.environ.get(key, "")
    src = "studio" if key in _settings["applied"] else ("server" if v else None)
    return {"set": bool(v), "source": src, "hint": ("••••" + v[-4:]) if len(v) > 8 else ("set" if v else ""),
            **(_settings["meta"].get(key) or {})}


@route(admin_only=True)
async def admin_settings(request: Request, me: Dict[str, Any]) -> Response:
    """Which keys are set and where (Studio or Render). Never returns the values themselves."""
    await load_settings(force=True)
    return _ok({"keys": {k: _setting_state(k) for k in SETTING_KEYS}, "store_ready": _settings["ready"],
                "dodo_webhook_url": f"{API_BASE}/api/v1/billing/dodo/webhook"})


@route(admin_only=True)
async def admin_settings_save(request: Request, me: Dict[str, Any]) -> Response:
    """{"values": {KEY: "value" | ""}}; an empty value removes the Studio copy (Render's value applies again)."""
    values = (await _body(request)).get("values") or {}
    if not isinstance(values, dict) or not values:
        raise ValueError("Nothing to save")
    for k, v in values.items():
        if k not in SETTING_KEYS:
            raise ValueError(f"Unknown setting {k}")
        v = str(v or "").strip()
        if len(v) > 4000:
            raise ValueError(f"{k} is too long")
        if k == "DODO_MODE" and v not in ("", "test", "live"):
            raise ValueError("Mode must be test or live")
    try:
        for k, v in values.items():
            await db.rpc("ap_set_setting", p_key=k, p_value=str(v or "").strip(), p_by=me["email"] or "admin")
    except httpx.HTTPStatusError as e:
        if "ap_set_setting" in e.response.text:
            raise ValueError("The settings store is not set up yet: run supabase/autopilot_settings.sql once.")
        raise
    await load_settings(force=True)
    await log(request, me, "admin.settings", ",".join(sorted(values)), {"keys": sorted(values)})   # names only, never values
    return _ok({"keys": {k: _setting_state(k) for k in SETTING_KEYS}})


@route(admin_only=True)
async def admin_platform_test(request: Request, me: Dict[str, Any]) -> Response:
    platform = request.path_params["platform"]
    if platform == "dodo":
        if not dodo.configured():
            return _ok({"ok": False, "message": "Add the Dodo API key first."})
        try:
            await dodo.call("GET", "/products", params={"page_size": 1})
            return _ok({"ok": True, "message": f"Dodo accepted the key ({dodo.mode()} mode)."})
        except dodo.DodoError as e:
            return _ok({"ok": False, "message": "Dodo rejected the key" + (" (check that Mode matches the key: test or live)" if "401" in str(e) else "") + "."})
    if platform not in social.PLATFORMS:
        raise ValueError("Unknown platform")
    ok, msg = await social.check_app(platform, _redirect_uri(platform))
    await log(request, me, "admin.platform_test", platform, {"ok": ok})
    return _ok({"ok": ok, "message": msg})


# Mission Control (old admin tools, now a super-admin page in the Studio): the Studio relays each tool call here.
# The call is checked like every Studio call (signature + super admin), then run in-process against the old
# endpoint with a normal single-use admin token bound to that endpoint and that exact body.
MISSION_TOOLS = {
    "/api/v1/blog/generate": "POST", "/admin/blog/generate": "POST", "/api/v1/voice/list": "GET", "/api/v1/voice/synthesize": "POST",
    "/api/v1/video/master": "POST", "/api/v1/video/generate-reel": "POST", "/api/v1/omni/workflow": "POST",
    "/api/v1/gravityclaw/prompt": "POST", "/api/v1/channels/list": "GET", "/api/v1/channels/publish": "POST",
    "/api/v1/social/publish": "POST", "/api/v1/visuals/search": "POST", "/api/v1/pricewatch/track": "POST",
    "/api/v1/media/subtitles": "POST", "/api/v1/media/audio": "POST",
}


@route(admin_only=True, needs_db=False)
async def admin_tool(request: Request, me: Dict[str, Any]) -> Response:
    b = await _body(request)
    path, method = str(b.get("path") or ""), str(b.get("method") or "GET").upper()
    if MISSION_TOOLS.get(path) != method:
        raise ValueError("This tool is not available")
    endpoint = next((r.endpoint for r in request.app.routes if getattr(r, "path", None) == path and method in (getattr(r, "methods", None) or ())), None)
    if not endpoint:
        raise ValueError("This tool is not available on this server")
    raw = b"" if method == "GET" else json.dumps(b.get("body") or {}).encode()
    ok, tok = token_vault.issue(origin="", scopes=["admin:all"], client_ip=client_ip(request), subject=f"admin:{me['email'] or 'key'}",
                                is_admin=True, aud=path, body_hash=body_sha256(raw) if raw else None, ttl=60)
    if not ok:
        raise ValueError(tok.get("message", "Could not authorize the tool"))
    query = urlencode({k: str(v) for k, v in (b.get("query") or {}).items()}).encode()
    headers = [(k, v) for k, v in request.scope["headers"] if k not in (b"authorization", b"content-type", b"content-length", b"origin", b"referer")
               and not k.startswith(b"x-studio-")]
    headers += [(b"authorization", f"Bearer {tok['token']}".encode()), (b"content-type", b"application/json"),
                (b"content-length", str(len(raw)).encode())]
    scope = {**request.scope, "method": method, "path": path, "raw_path": path.encode(), "query_string": query, "headers": headers}
    sent = {"done": False}

    async def receive():
        if sent["done"]:
            return {"type": "http.disconnect"}
        sent["done"] = True
        return {"type": "http.request", "body": raw, "more_body": False}

    resp = await endpoint(Request(scope, receive))
    await log(request, me, "admin.tool", path, {"status": resp.status_code})
    if not hasattr(resp, "body"):
        raise ValueError("This tool returns a stream, which Mission Control cannot show")
    return Response(resp.body, status_code=resp.status_code, media_type=resp.media_type or "application/json",
                    headers={"Cache-Control": "no-store"})


routes_studio = [
    Route("/api/v1/studio/me", me_get, methods=["GET"]),
    Route("/api/v1/studio/me", me_update, methods=["POST"]),
    Route("/api/v1/studio/account/sessions", account_sessions, methods=["GET"]),
    Route("/api/v1/studio/account/sessions/{id}/revoke", account_session_revoke, methods=["POST"]),
    Route("/api/v1/studio/account/delete", account_delete, methods=["POST"]),
    Route("/api/v1/studio/catalog", catalog, methods=["GET"]),
    Route("/api/v1/studio/voices", voices, methods=["GET"]),
    Route("/api/v1/studio/ideas", ideas, methods=["POST"]),
    Route("/api/v1/studio/script", script, methods=["POST"]),
    Route("/api/v1/studio/autopilots", autopilots_list, methods=["GET"]),
    Route("/api/v1/studio/autopilots", autopilots_save, methods=["POST"]),
    Route("/api/v1/studio/autopilots/{id}/delete", autopilots_delete, methods=["POST"]),
    Route("/api/v1/studio/jobs", jobs_list, methods=["GET"]),
    Route("/api/v1/studio/jobs", jobs_create, methods=["POST"]),
    Route("/api/v1/studio/jobs/{id}", job_get, methods=["GET"]),
    Route("/api/v1/studio/jobs/{id}/regen", job_regen, methods=["POST"]),
    Route("/api/v1/studio/jobs/{id}/publish", job_publish, methods=["POST"]),
    Route("/api/v1/studio/jobs/{id}/cancel", job_cancel, methods=["POST"]),
    Route("/api/v1/studio/jobs/{id}/delete", job_delete, methods=["POST"]),
    Route("/api/v1/studio/status", status, methods=["GET"]),
    Route("/api/v1/studio/billing", billing_get, methods=["GET"]),
    Route("/api/v1/studio/billing/usage", billing_usage, methods=["GET"]),
    Route("/api/v1/studio/billing/checkout", billing_checkout, methods=["POST"]),
    Route("/api/v1/studio/billing/portal", billing_portal, methods=["POST"]),
    Route("/api/v1/studio/billing/cancel", billing_cancel, methods=["POST"]),
    Route("/api/v1/studio/admin/billing/sync", admin_billing_sync, methods=["POST"]),
    Route("/api/v1/billing/dodo/webhook", dodo_webhook, methods=["POST"]),
    Route("/api/v1/studio/accounts", accounts_list, methods=["GET"]),
    Route("/api/v1/studio/accounts/{id}/delete", accounts_delete, methods=["POST"]),
    Route("/api/v1/studio/analytics", analytics, methods=["GET"]),
    Route("/api/v1/studio/requests", platform_request, methods=["POST"]),
    Route("/api/v1/studio/admin/users", admin_users, methods=["GET"]),
    Route("/api/v1/studio/admin/users/{id}", admin_user_update, methods=["POST"]),
    Route("/api/v1/studio/admin/activity", admin_activity, methods=["GET"]),
    Route("/api/v1/studio/admin/platforms", admin_platforms, methods=["GET"]),
    Route("/api/v1/studio/admin/tool", admin_tool, methods=["POST"]),
    Route("/api/v1/studio/admin/settings", admin_settings, methods=["GET"]),
    Route("/api/v1/studio/admin/settings", admin_settings_save, methods=["POST"]),
    Route("/api/v1/studio/admin/platforms/{platform}/test", admin_platform_test, methods=["POST"]),
    Route("/api/v1/auth/{platform}/callback", oauth_callback, methods=["GET"]),
    Route("/api/v1/auth/{platform}", oauth_start, methods=["GET"]),
]
