"""WinPlayBox Authentication, Plans & Credit Ledger Management.

Handles:
- Guest-first onboarding: instant guest identity with Free trial credits.
- Google OAuth 2.0 verification (One-Tap & Popup).
- Append-only credit ledger with atomic reservation/debit/refund transactions.
- Configurable plan catalog (Free, Plan 1–6) stored in SQLite.
- Secure signed JWT session cookies and Bearer token verification.
"""
from __future__ import annotations

import os
import time
import uuid
import sqlite3
import logging
import hashlib
import hmac
import re
import secrets
from typing import Any, Dict, List, Optional, Tuple
import jwt
import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("wpb.auth")

DB_DIR = os.environ.get("WPB_DATA_DIR") or ("/var/tmp" if os.path.exists("/var/tmp") else os.path.join(os.environ.get("TEMP", "/tmp"), "ovd_data"))
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "auth.db")

JWT_SECRET = os.environ.get("WPB_JWT_SECRET") or os.environ.get("WPB_VAULT_SECRET") or "wpb_jwt_production_signing_key_48bytes"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30
GUEST_EXPIRY_DAYS = 7

# Default Plan Seeds
DEFAULT_PLANS = [
    {"id": "free", "name": "Free (480p SD)", "price_inr": 0, "price_usd": 0, "max_res": 480, "max_duration": 30, "credits": 2, "voices_tier": "standard", "captions_tier": "basic", "dodo_product_id": ""},
    {"id": "plan1", "name": "Starter (720p)", "price_inr": 299, "price_usd": 4, "max_res": 720, "max_duration": 60, "credits": 30, "voices_tier": "standard", "captions_tier": "standard", "dodo_product_id": "p_starter_720"},
    {"id": "plan2", "name": "Creator (1080p)", "price_inr": 599, "price_usd": 8, "max_res": 1080, "max_duration": 90, "credits": 75, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "p_creator_1080"},
    {"id": "plan3", "name": "Pro (2K)", "price_inr": 999, "price_usd": 13, "max_res": 1440, "max_duration": 120, "credits": 150, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "p_pro_2k"},
    {"id": "plan4", "name": "Studio (3K)", "price_inr": 1699, "price_usd": 22, "max_res": 1800, "max_duration": 180, "credits": 300, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "p_studio_3k"},
    {"id": "plan5", "name": "Business (4K)", "price_inr": 2999, "price_usd": 40, "max_res": 2160, "max_duration": 300, "credits": 600, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "p_business_4k"},
    {"id": "plan6", "name": "Enterprise (8K)", "price_inr": 5999, "price_usd": 80, "max_res": 4320, "max_duration": 300, "credits": 1500, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "p_enterprise_8k"},
]


_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    """Derives a salted PBKDF2-HMAC-SHA256 hash."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies password matches stored salted PBKDF2 hash."""
    if not stored_hash or ":" not in stored_hash:
        return False
    salt, _, key_hex = stored_hash.partition(":")
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(key.hex(), key_hex)


def _init_db() -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    name TEXT,
                    avatar TEXT,
                    plan TEXT DEFAULT 'free',
                    credits INTEGER DEFAULT 2,
                    daily_credits INTEGER DEFAULT 2,
                    last_daily_reset REAL,
                    dodo_customer_id TEXT,
                    dodo_subscription_id TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            try:
                conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE users ADD COLUMN dodo_subscription_id TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE guest_sessions ADD COLUMN plan TEXT DEFAULT 'free'")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE guest_sessions ADD COLUMN max_resolution INTEGER DEFAULT 480")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE guest_sessions ADD COLUMN dodo_subscription_id TEXT")
            except sqlite3.OperationalError:
                pass
            conn.execute("""
                CREATE TABLE IF NOT EXISTS guest_sessions (
                    guest_id TEXT PRIMARY KEY,
                    ip TEXT,
                    plan TEXT DEFAULT 'free',
                    max_resolution INTEGER DEFAULT 480,
                    credits INTEGER DEFAULT 2,
                    last_daily_reset REAL,
                    dodo_subscription_id TEXT,
                    converted_to_user_id TEXT,
                    created_at REAL,
                    expires_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credit_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    reference_id TEXT,
                    description TEXT,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price_inr INTEGER NOT NULL,
                    price_usd INTEGER NOT NULL,
                    max_res INTEGER NOT NULL,
                    max_duration INTEGER NOT NULL,
                    credits INTEGER NOT NULL,
                    voices_tier TEXT NOT NULL,
                    captions_tier TEXT NOT NULL,
                    dodo_product_id TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Seed or sync plans
            for p in DEFAULT_PLANS:
                conn.execute("""
                    INSERT INTO plans (id, name, price_inr, price_usd, max_res, max_duration, credits, voices_tier, captions_tier, dodo_product_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        price_inr = excluded.price_inr,
                        price_usd = excluded.price_usd,
                        max_res = excluded.max_res,
                        max_duration = excluded.max_duration,
                        credits = excluded.credits,
                        voices_tier = excluded.voices_tier,
                        captions_tier = excluded.captions_tier,
                        dodo_product_id = excluded.dodo_product_id
                """, (p["id"], p["name"], p["price_inr"], p["price_usd"], p["max_res"], p["max_duration"], p["credits"], p["voices_tier"], p["captions_tier"], p["dodo_product_id"]))

            conn.commit()
    except Exception as e:
        log.error("Failed to initialize auth database: %s", e)


_init_db()


def _record_ledger(conn: sqlite3.Connection, entity_type: str, entity_id: str, amount: int, balance_after: int, event_type: str, reference_id: Optional[str] = None, description: Optional[str] = None) -> None:
    conn.execute("""
        INSERT INTO credit_ledger (entity_type, entity_id, amount, balance_after, event_type, reference_id, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (entity_type, entity_id, amount, balance_after, event_type, reference_id, description, time.time()))


def get_all_plans() -> List[Dict[str, Any]]:
    _init_db()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plans WHERE is_active = 1")
            return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        log.error("get_all_plans error: %s", e)
        return DEFAULT_PLANS


def get_plan(plan_id: str) -> Dict[str, Any]:
    plans = {p["id"]: p for p in get_all_plans()}
    return plans.get(plan_id, plans.get("free", DEFAULT_PLANS[0]))


def create_guest_session(ip: str) -> Dict[str, Any]:
    _init_db()
    guest_id = f"gst_{uuid.uuid4().hex}"
    now = time.time()
    expires_at = now + (GUEST_EXPIRY_DAYS * 86400)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO guest_sessions (guest_id, ip, credits, last_daily_reset, created_at, expires_at)
                VALUES (?, ?, 2, ?, ?, ?)
            """, (guest_id, ip, now, now, expires_at))
            _record_ledger(conn, "guest", guest_id, 2, 2, "guest_trial_grant", None, "Daily free trial credits")
            conn.commit()
    except Exception as e:
        log.error("create_guest_session error: %s", e)

    return {
        "guest_id": guest_id,
        "is_guest": True,
        "authenticated": False,
        "plan": "free",
        "credits": 2,
        "max_resolution": 480,
        "max_duration": 30,
        "name": "Guest Visitor",
        "email": None,
        "avatar": None
    }


def get_guest_session(guest_id: str) -> Optional[Dict[str, Any]]:
    if not guest_id or not guest_id.startswith("gst_"):
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guest_sessions WHERE guest_id = ?", (guest_id,))
            row = cursor.fetchone()
            if row:
                r = dict(row)
                now = time.time()
                # Daily reset logic: if more than 24h passed, reset to 2 daily credits
                if now - r.get("last_daily_reset", 0) > 86400:
                    conn.execute("UPDATE guest_sessions SET credits = 2, last_daily_reset = ? WHERE guest_id = ?", (now, guest_id))
                    _record_ledger(conn, "guest", guest_id, 2, 2, "daily_reset", None, "Daily credit renewal")
                    conn.commit()
                    r["credits"] = 2
                plan_id = r.get("plan") or "free"
                plan_info = get_plan(plan_id)
                max_res = r.get("max_resolution") or (plan_info.get("max_res") if plan_info else 480)
                return {
                    "guest_id": guest_id,
                    "is_guest": True,
                    "authenticated": False,
                    "plan": plan_id,
                    "plan_name": plan_info.get("name") if plan_info else "Free Trial (480p SD)",
                    "credits": r.get("credits", 2),
                    "max_resolution": max_res,
                    "max_duration": plan_info.get("max_duration", 30) if plan_info else 30,
                    "converted_to": r.get("converted_to_user_id"),
                    "name": "Guest Visitor",
                    "email": None,
                    "avatar": None
                }
    except Exception as e:
        log.error("get_guest_session error: %s", e)
    return None


async def verify_google_credential(credential: str) -> Optional[Dict[str, Any]]:
    """Verifies a Google ID token with Google's public tokeninfo endpoint."""
    if not credential:
        return None
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if "email" in data:
                    return {
                        "sub": data.get("sub"),
                        "email": data.get("email", "").lower().strip(),
                        "name": data.get("name", "User"),
                        "avatar": data.get("picture", ""),
                        "email_verified": data.get("email_verified", "true") == "true"
                    }
    except Exception as e:
        log.error("Google token verification failed: %s", e)
    return None


def upsert_user_from_google(google_data: Dict[str, Any], guest_id: Optional[str] = None) -> Dict[str, Any]:
    """Creates or updates user record and migrates any eligible guest credits/jobs."""
    email = google_data["email"]
    name = google_data.get("name") or "User"
    avatar = google_data.get("avatar") or ""
    now = time.time()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()

        if existing:
            user = dict(existing)
            conn.execute("UPDATE users SET name = ?, avatar = ?, updated_at = ? WHERE id = ?", (name, avatar, now, user["id"]))
            conn.commit()
        else:
            user_id = f"usr_{uuid.uuid4().hex}"
            initial_credits = 5  # 5 Welcome bonus credits!
            conn.execute("""
                INSERT INTO users (id, email, name, avatar, plan, credits, daily_credits, last_daily_reset, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'free', ?, 2, ?, ?, ?)
            """, (user_id, email, name, avatar, initial_credits, now, now, now))
            _record_ledger(conn, "user", user_id, initial_credits, initial_credits, "signup_bonus", None, "Welcome bonus credits")
            conn.commit()
            user = {
                "id": user_id,
                "email": email,
                "name": name,
                "avatar": avatar,
                "plan": "free",
                "credits": initial_credits
            }

        # If converted from guest, link guest session and migrate upgraded plan or credits
        if guest_id:
            cursor.execute("SELECT plan, max_resolution, credits, dodo_subscription_id FROM guest_sessions WHERE guest_id = ?", (guest_id,))
            grow = cursor.fetchone()
            if grow:
                gdata = dict(grow)
                if gdata.get("plan") and gdata["plan"] != "free":
                    conn.execute("UPDATE users SET plan = ?, dodo_subscription_id = ? WHERE id = ?", (gdata["plan"], gdata.get("dodo_subscription_id"), user["id"]))
                    user["plan"] = gdata["plan"]
                extra_credits = max(0, (gdata.get("credits") or 0) - 2)
                if extra_credits > 0:
                    conn.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (extra_credits, user["id"]))
                    user["credits"] = (user.get("credits") or 0) + extra_credits
                    _record_ledger(conn, "user", user["id"], extra_credits, user["credits"], "guest_transfer", guest_id, "Transferred remaining credits from guest session")
            conn.execute("UPDATE guest_sessions SET converted_to_user_id = ? WHERE guest_id = ?", (user["id"], guest_id))
            conn.commit()

    return user


def register_user_with_email(email: str, password: str, name: str = "", guest_id: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Registers a new user with valid email and password, giving 5 welcome credits."""
    email = (email or "").strip().lower()
    if not email or not _EMAIL_REGEX.match(email):
        return None, "Please enter a valid email address."
    if not password or len(password) < 6:
        return None, "Password must be at least 6 characters long."

    name = (name or "").strip() or email.split("@")[0].capitalize()
    now = time.time()
    pwd_hash = hash_password(password)
    avatar = f"https://api.dicebear.com/7.x/initials/svg?seed={name}"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return None, "An account with this email already exists. Please sign in."

        # Check if converting from an upgraded guest
        target_plan = 'free'
        dodo_sub = None
        extra_credits = 0
        if guest_id:
            cursor.execute("SELECT plan, max_resolution, credits, dodo_subscription_id FROM guest_sessions WHERE guest_id = ?", (guest_id,))
            grow = cursor.fetchone()
            if grow:
                gdata = dict(grow)
                if gdata.get("plan") and gdata["plan"] != "free":
                    target_plan = gdata["plan"]
                    dodo_sub = gdata.get("dodo_subscription_id")
                extra_credits = max(0, (gdata.get("credits") or 0) - 2)

        user_id = f"usr_{uuid.uuid4().hex}"
        initial_credits = 5  # 5 Welcome bonus credits!
        total_credits = initial_credits + extra_credits
        conn.execute("""
            INSERT INTO users (id, email, password_hash, name, avatar, plan, credits, daily_credits, dodo_subscription_id, last_daily_reset, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 2, ?, ?, ?, ?)
        """, (user_id, email, pwd_hash, name, avatar, target_plan, total_credits, dodo_sub, now, now, now))
        _record_ledger(conn, "user", user_id, initial_credits, total_credits, "signup_bonus", None, "Welcome bonus credits")
        if extra_credits > 0:
            _record_ledger(conn, "user", user_id, extra_credits, total_credits, "guest_transfer", guest_id, "Transferred remaining credits from guest session")

        if guest_id:
            conn.execute("UPDATE guest_sessions SET converted_to_user_id = ? WHERE guest_id = ?", (user_id, guest_id))
        conn.commit()

        plan_info = get_plan(target_plan)
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "avatar": avatar,
            "plan": target_plan,
            "plan_name": plan_info.get("name") if plan_info else "Free Trial (480p SD)",
            "credits": total_credits,
            "max_resolution": plan_info.get("max_res") if plan_info else 480,
            "authenticated": True,
            "is_guest": False
        }
        return user, None


def login_user_with_email(email: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Authenticates an existing user with email and password."""
    email = (email or "").strip().lower()
    if not email or not password:
        return None, "Email and password are required."

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return None, "No account found with this email. Please sign up."

        u = dict(row)
        stored_hash = u.get("password_hash")
        if not stored_hash or not verify_password(password, stored_hash):
            return None, "Incorrect password. If you signed up with Google, please use Sign in with Google."

        # Daily credit renewal check
        now = time.time()
        credits = u.get("credits", 0)
        if now - (u.get("last_daily_reset") or 0) > 86400:
            if u.get("plan") == "free" and credits < 2:
                credits = 2
                conn.execute("UPDATE users SET credits = ?, last_daily_reset = ? WHERE id = ?", (credits, now, u["id"]))
                _record_ledger(conn, "user", u["id"], 2, 2, "daily_reset", None, "Daily credit renewal")
                conn.commit()
                u["credits"] = credits

        specs = get_plan(u.get("plan", "free"))
        user = {
            "id": u["id"],
            "email": u["email"],
            "name": u["name"],
            "avatar": u.get("avatar"),
            "plan": u.get("plan", "free"),
            "plan_name": specs["name"],
            "credits": u.get("credits", 0),
            "max_resolution": specs["max_res"],
            "max_duration": specs["max_duration"],
            "authenticated": True,
            "is_guest": False
        }
        return user, None


def issue_session_jwt(user: Dict[str, Any]) -> str:
    now = int(time.time())
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user.get("name"),
        "plan": user.get("plan", "free"),
        "iat": now,
        "exp": now + (JWT_EXPIRY_DAYS * 86400)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_user_from_jwt(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                u = dict(row)
                plan = u.get("plan", "free")
                specs = get_plan(plan)
                return {
                    "user_id": u["id"],
                    "email": u["email"],
                    "name": u["name"],
                    "avatar": u.get("avatar"),
                    "plan": plan,
                    "plan_name": specs["name"],
                    "credits": u.get("credits", 0),
                    "max_resolution": specs["max_res"],
                    "max_duration": specs["max_duration"],
                    "authenticated": True,
                    "is_guest": False
                }
    except Exception:
        pass
    return None


def resolve_request_identity(request: Request) -> Dict[str, Any]:
    """Resolves whether caller is an authenticated user or a guest."""
    # 1. Check Bearer token or wpb_session cookie
    token = request.headers.get("authorization", "")
    if token.startswith("Bearer "):
        token = token[7:].strip()
    if not token:
        token = request.cookies.get("wpb_session", "")

    if token:
        user = get_user_from_jwt(token)
        if user:
            return user

    # 2. Check guest session from header or cookie
    guest_id = request.headers.get("x-guest-id") or request.cookies.get("wpb_guest", "")
    guest = get_guest_session(guest_id)
    if guest:
        return guest

    # 3. Create fresh guest session
    from backend.security.zero_trust import client_ip
    ip = client_ip(request)
    return create_guest_session(ip)


def deduct_credit_for_job(identity: Dict[str, Any], cost: int = 1, job_id: Optional[str] = None) -> bool:
    """Atomically deducts credit from user or guest with an append-only ledger audit trail."""
    if identity.get("authenticated") and identity.get("user_id"):
        user_id = identity["user_id"]
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row or row[0] < cost:
                    return False
                new_bal = row[0] - cost
                cursor.execute("UPDATE users SET credits = ? WHERE id = ? AND credits >= ?", (new_bal, user_id, cost))
                if cursor.rowcount > 0:
                    _record_ledger(conn, "user", user_id, -cost, new_bal, "job_render_debit", job_id, f"Video render job {job_id or ''}")
                    conn.commit()
                    return True
        except Exception as e:
            log.error("deduct_credit_for_job error: %s", e)
            return False
    elif identity.get("is_guest") and identity.get("guest_id"):
        guest_id = identity["guest_id"]
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM guest_sessions WHERE guest_id = ?", (guest_id,))
                row = cursor.fetchone()
                if not row or row[0] < cost:
                    return False
                new_bal = row[0] - cost
                cursor.execute("UPDATE guest_sessions SET credits = ? WHERE guest_id = ? AND credits >= ?", (new_bal, guest_id, cost))
                if cursor.rowcount > 0:
                    _record_ledger(conn, "guest", guest_id, -cost, new_bal, "job_render_debit", job_id, f"Guest video render job {job_id or ''}")
                    conn.commit()
                    return True
        except Exception as e:
            log.error("deduct_credit_for_job error: %s", e)
            return False
    return False


def refund_credit_for_job(identity: Dict[str, Any], amount: int = 1, job_id: Optional[str] = None, reason: str = "Render failed") -> None:
    """Refunds credits if a job failed or was rejected, recording to ledger."""
    if identity.get("authenticated") and identity.get("user_id"):
        user_id = identity["user_id"]
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    new_bal = row[0] + amount
                    conn.execute("UPDATE users SET credits = ? WHERE id = ?", (new_bal, user_id))
                    _record_ledger(conn, "user", user_id, amount, new_bal, "job_refund", job_id, reason)
                    conn.commit()
        except Exception:
            pass
    elif identity.get("is_guest") and identity.get("guest_id"):
        guest_id = identity["guest_id"]
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM guest_sessions WHERE guest_id = ?", (guest_id,))
                row = cursor.fetchone()
                if row:
                    new_bal = row[0] + amount
                    conn.execute("UPDATE guest_sessions SET credits = ? WHERE guest_id = ?", (new_bal, guest_id))
                    _record_ledger(conn, "guest", guest_id, amount, new_bal, "job_refund", job_id, reason)
                    conn.commit()
        except Exception:
            pass


def get_credit_history(entity_type: str, entity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the append-only ledger transaction history."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM credit_ledger 
                WHERE entity_type = ? AND entity_id = ? 
                ORDER BY created_at DESC LIMIT ?
            """, (entity_type, entity_id, limit))
            return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        log.error("get_credit_history error: %s", e)
        return []


def upgrade_user_plan(user_id: str, plan_id: str, dodo_subscription_id: Optional[str] = None) -> bool:
    """Upgrades user plan and adds plan credits atomically with ledger entry."""
    norm_plan_id = plan_id.lower().replace("_", "")
    plan = get_plan(norm_plan_id) or get_plan(plan_id)
    if not plan:
        log.error("upgrade_user_plan: unknown plan '%s'", plan_id)
        return False
    plan_id = plan["id"]
    now = time.time()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False
            granted_credits = plan.get("credits", 30)
            new_bal = row["credits"] + granted_credits
            conn.execute("""
                UPDATE users SET plan = ?, credits = ?, dodo_subscription_id = ?, updated_at = ?
                WHERE id = ?
            """, (plan_id, new_bal, dodo_subscription_id, now, user_id))
            _record_ledger(conn, "user", user_id, granted_credits, new_bal, "subscription_upgrade", dodo_subscription_id, f"Upgraded to {plan['name']}")
            conn.commit()
            return True
    except Exception as e:
        log.error("upgrade_user_plan error: %s", e)
        return False


def upgrade_guest_plan(guest_id: str, plan_id: str, dodo_subscription_id: Optional[str] = None) -> bool:
    """Upgrades a guest session with a purchased plan and credits."""
    norm_plan_id = plan_id.lower().replace("_", "")
    plan = get_plan(norm_plan_id) or get_plan(plan_id)
    if not plan:
        log.error("upgrade_guest_plan: unknown plan '%s'", plan_id)
        return False
    plan_id = plan["id"]
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT credits FROM guest_sessions WHERE guest_id = ?", (guest_id,))
            row = cursor.fetchone()
            if not row:
                log.error("upgrade_guest_plan: guest not found %s", guest_id)
                return False
            cur_credits = row["credits"]
            new_credits = cur_credits + plan["credits"]
            conn.execute("""
                UPDATE guest_sessions
                SET plan = ?, max_resolution = ?, credits = ?, dodo_subscription_id = ?
                WHERE guest_id = ?
            """, (plan_id, plan["max_res"], new_credits, dodo_subscription_id, guest_id))
            _record_ledger(conn, "guest", guest_id, plan["credits"], new_credits, "plan_upgrade", dodo_subscription_id, f"Purchased {plan['name']}")
            conn.commit()
            log.info("upgrade_guest_plan: %s -> %s (+%s credits, total=%s)", guest_id, plan_id, plan["credits"], new_credits)
            return True
    except Exception as e:
        log.error("upgrade_guest_plan error: %s", e)
        return False


def add_credits_to_identity(identity: Dict[str, Any], amount: int, reason: str, reference_id: Optional[str] = None) -> bool:
    """Adds credits to a user or guest, recorded in ledger."""
    if identity.get("authenticated") and identity.get("user_id"):
        user_id = identity["user_id"]
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                new_bal = row[0] + amount
                conn.execute("UPDATE users SET credits = ? WHERE id = ?", (new_bal, user_id))
                _record_ledger(conn, "user", user_id, amount, new_bal, "credit_purchase", reference_id, reason)
                conn.commit()
                return True
        except Exception as e:
            log.error("add_credits_to_identity error: %s", e)
            return False
    elif identity.get("is_guest") and identity.get("guest_id"):
        guest_id = identity["guest_id"]
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM guest_sessions WHERE guest_id = ?", (guest_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                new_bal = row[0] + amount
                conn.execute("UPDATE guest_sessions SET credits = ? WHERE guest_id = ?", (new_bal, guest_id))
                _record_ledger(conn, "guest", guest_id, amount, new_bal, "credit_purchase", reference_id, reason)
                conn.commit()
                return True
        except Exception as e:
            log.error("add_credits_to_identity error: %s", e)
            return False
    return False

