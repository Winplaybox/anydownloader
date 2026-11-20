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
from contextlib import contextmanager
import jwt
import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("wpb.auth")

DB_DIR = os.environ.get("WPB_DATA_DIR") or ("/var/tmp" if os.path.exists("/var/tmp") else os.path.join(os.environ.get("TEMP", "/tmp"), "ovd_data"))
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "auth.db")

def _is_production() -> bool:
    return os.environ.get("WPB_ENV", "").lower() in ("prod", "production") or bool(os.environ.get("RENDER"))


def _load_jwt_secret() -> str:
    secret = (os.environ.get("WPB_JWT_SECRET") or "").strip()
    if len(secret) >= 32:
        return secret
    if _is_production():
        raise RuntimeError("WPB_JWT_SECRET (32+ random characters) must be set in production.")
    # Development only: an ephemeral per-process secret, never a shared hard-coded value.
    log.warning("WPB_JWT_SECRET not set; using an ephemeral development secret (sessions reset on restart).")
    return secrets.token_urlsafe(48)


JWT_SECRET = _load_jwt_secret()
JWT_ISSUER = "ovd.winplaybox.in"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30
GUEST_EXPIRY_DAYS = 7

# Default Plan Seeds (Monthly, Yearly, 24-Hour Day Pass, Credit Packs)
DEFAULT_PLANS = [
    {"id": "free", "name": "Free (480p SD)", "price_inr": 0, "price_usd": 0, "max_res": 480, "max_duration": 30, "credits": 2, "voices_tier": "standard", "captions_tier": "basic", "dodo_product_id": ""},
    {"id": "plan1", "name": "Starter (720p)", "price_inr": 299, "price_usd": 4, "max_res": 720, "max_duration": 60, "credits": 30, "voices_tier": "standard", "captions_tier": "standard", "dodo_product_id": "pdt_0NsD5gB9BVgr9HcXQ1bZn"},
    {"id": "plan2", "name": "Creator (1080p)", "price_inr": 599, "price_usd": 8, "max_res": 1080, "max_duration": 90, "credits": 75, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsD6LN0JNlPsYDKDC68B"},
    {"id": "plan3", "name": "Pro (2K)", "price_inr": 999, "price_usd": 13, "max_res": 1440, "max_duration": 120, "credits": 150, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsD6LSzzhmCeUJSD6xal"},
    {"id": "plan4", "name": "Studio (3K)", "price_inr": 1699, "price_usd": 22, "max_res": 1800, "max_duration": 180, "credits": 300, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsD6LZhTr5YKnO2ofQtH"},
    {"id": "plan5", "name": "Agency (4K)", "price_inr": 2999, "price_usd": 40, "max_res": 2160, "max_duration": 300, "credits": 600, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsD6LqMzHo26g2eV0eC1"},
    {"id": "plan6", "name": "Enterprise (8K)", "price_inr": 5999, "price_usd": 80, "max_res": 4320, "max_duration": 300, "credits": 1500, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsD6M6kJNKNQ83qBKNVn"},

    # 24-Hour Creator Day Pass (One-off projects, expires in 24 hours)
    {"id": "day_pass", "name": "24-Hour Creator Pass", "price_inr": 99, "price_usd": 1.5, "max_res": 1080, "max_duration": 90, "credits": 15, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTUmxEe6Wbzz5hsp7L"},

    # One-Time Credit Top-Up Packs (Never Expire)
    {"id": "pack_100", "name": "100 Credits Top-up", "price_inr": 299, "price_usd": 4, "max_res": 1080, "max_duration": 90, "credits": 100, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTrR0ewxQK6PTTP98G"},
    {"id": "pack_300", "name": "300 Credits Top-up", "price_inr": 699, "price_usd": 9, "max_res": 1440, "max_duration": 120, "credits": 300, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTrWv3ibp4UavYQ6wF"},
    {"id": "pack_500", "name": "500 Credits Top-up", "price_inr": 999, "price_usd": 13, "max_res": 2160, "max_duration": 180, "credits": 500, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0Ns7d19f2M1B7GslZEnKA"},
    {"id": "pack_1500", "name": "1500 Credits Pro Top-up", "price_inr": 2499, "price_usd": 33, "max_res": 4320, "max_duration": 300, "credits": 1500, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTrfAWJD4RrbM3SuwL"},

    # Yearly Subscription Plans (Save ~20% / 2 Months Free)
    {"id": "plan1_yearly", "name": "Starter (Yearly)", "price_inr": 2870, "price_usd": 38, "max_res": 720, "max_duration": 60, "credits": 30, "voices_tier": "standard", "captions_tier": "standard", "dodo_product_id": "pdt_0NsDTroXSQKLLqwaoMNV1"},
    {"id": "plan2_yearly", "name": "Creator (Yearly)", "price_inr": 5750, "price_usd": 76, "max_res": 1080, "max_duration": 90, "credits": 75, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTrwOilW0LIcdiNcly"},
    {"id": "plan3_yearly", "name": "Pro (Yearly)", "price_inr": 9590, "price_usd": 124, "max_res": 1440, "max_duration": 120, "credits": 150, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTs3x8Y7ZbeE07bawr"},
    {"id": "plan4_yearly", "name": "Studio (Yearly)", "price_inr": 16300, "price_usd": 210, "max_res": 1800, "max_duration": 180, "credits": 300, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTsB84lRbmGgk3mUx8"},
    {"id": "plan5_yearly", "name": "Agency (Yearly)", "price_inr": 28790, "price_usd": 380, "max_res": 2160, "max_duration": 300, "credits": 600, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTsHILc59bPNfawC6Q"},
    {"id": "plan6_yearly", "name": "Enterprise (Yearly)", "price_inr": 57590, "price_usd": 760, "max_res": 4320, "max_duration": 300, "credits": 1500, "voices_tier": "all", "captions_tier": "all", "dodo_product_id": "pdt_0NsDTsOBDIg9hEZUM9oAG"},
]


_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_REGEX = re.compile(r"^[a-z0-9_]{3,24}$")
_RESERVED_USERNAMES = {
    "admin", "administrator", "root", "support", "help", "api", "ovd", "winplaybox", "system",
    "billing", "payments", "security", "staff", "moderator", "owner", "null", "undefined",
}

FREE_GUEST_CREDITS = max(0, int(os.environ.get("FREE_GUEST_CREDITS", "2")))
FREE_USER_DAILY_FLOOR = max(0, int(os.environ.get("FREE_USER_DAILY_FLOOR", "2")))
SIGNUP_BONUS_CREDITS = max(0, int(os.environ.get("SIGNUP_BONUS_CREDITS", "5")))
GUESTS_PER_IP_PER_DAY = max(1, int(os.environ.get("GUESTS_PER_IP_PER_DAY", "3")))
MIN_PASSWORD_LENGTH = 8
PBKDF2_ITERATIONS = 310_000
_LEGACY_PBKDF2_ITERATIONS = 100_000

# Ledger event types that may exist at most once per reference (job id / payment id).
_UNIQUE_LEDGER_EVENTS = ("job_render_debit", "job_refund", "payment_grant", "payment_reversal", "yearly_monthly_grant")
DAY_PASS_SECONDS = 86400
MONTH_SECONDS = 30 * 86400


def hash_password(password: str) -> str:
    """Derives a salted PBKDF2-HMAC-SHA256 hash (iteration count is stored with the hash)."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a password against both the current and the legacy `salt:hex` hash format."""
    if not stored_hash or password is None:
        return False
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, key_hex = stored_hash.split("$", 3)
            rounds = int(iterations)
        except ValueError:
            return False
    elif ":" in stored_hash:
        salt, _, key_hex = stored_hash.partition(":")
        rounds = _LEGACY_PBKDF2_ITERATIONS
    else:
        return False
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), rounds)
    return hmac.compare_digest(key.hex(), key_hex)


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #

@contextmanager
def _connect(immediate: bool = False):
    """One short-lived connection. WAL + busy_timeout make API and worker processes share the file safely.

    immediate=True takes the write lock up front so read-modify-write sequences (credit balances)
    cannot interleave with another process.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield conn
        if conn.in_transaction:
            conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def _add_column(conn: sqlite3.Connection, table: str, ddl: str) -> None:
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
    except sqlite3.OperationalError:
        pass


_db_ready = False


def _init_db(force: bool = False) -> None:
    global _db_ready
    if _db_ready and not force:
        return
    try:
        raw = sqlite3.connect(DB_PATH, timeout=30)
        try:
            raw.execute("PRAGMA journal_mode=WAL")
        finally:
            raw.close()
        with _connect(immediate=True) as conn:
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
            for ddl in ("password_hash TEXT", "dodo_subscription_id TEXT", "username TEXT", "google_sub TEXT",
                        "email_verified INTEGER DEFAULT 0", "session_version INTEGER DEFAULT 1",
                        "plan_status TEXT DEFAULT 'active'", "plan_renews_at REAL", "is_disabled INTEGER DEFAULT 0"):
                _add_column(conn, "users", ddl)
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
            for ddl in ("plan TEXT DEFAULT 'free'", "max_resolution INTEGER DEFAULT 480", "dodo_subscription_id TEXT",
                        "converted_to_user_id TEXT"):
                _add_column(conn, "guest_sessions", ddl)
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
            # Verified payment-provider events, processed exactly once (webhook-id is the key).
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_webhook_events (
                    webhook_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    received_at REAL NOT NULL,
                    result TEXT
                )
            """)
            # One row per paid provider payment: who got what, so refunds/disputes can be reversed.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_grants (
                    payment_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    credits INTEGER NOT NULL,
                    subscription_id TEXT,
                    amount_minor INTEGER,
                    currency TEXT,
                    status TEXT NOT NULL DEFAULT 'granted',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    next_billing_at REAL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_tokens (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    scopes TEXT NOT NULL,
                    created_by TEXT,
                    created_at REAL NOT NULL,
                    expires_at REAL,
                    last_used_at REAL,
                    revoked_at REAL
                )
            """)
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username) WHERE username IS NOT NULL")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_ledger_entity ON credit_ledger(entity_type, entity_id, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_guest_ip_created ON guest_sessions(ip, created_at)")
            try:
                events = ",".join(f"'{e}'" for e in _UNIQUE_LEDGER_EVENTS)
                conn.execute(f"""
                    CREATE UNIQUE INDEX IF NOT EXISTS ux_ledger_once ON credit_ledger(event_type, entity_type, entity_id, reference_id)
                    WHERE reference_id IS NOT NULL AND event_type IN ({events})
                """)
            except sqlite3.IntegrityError:
                log.error("credit_ledger has historical duplicate debits/refunds; uniqueness index not created")

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
                """, (p["id"], p["name"], p["price_inr"], p["price_usd"], p["max_res"], p["max_duration"], p["credits"],
                      p["voices_tier"], p["captions_tier"], _env_product_id(p["id"]) or p["dodo_product_id"]))

            # Backfill usernames for accounts created before usernames existed.
            for row in conn.execute("SELECT id, name, email FROM users WHERE username IS NULL").fetchall():
                conn.execute("UPDATE users SET username = ? WHERE id = ?",
                             (_unique_username(conn, row["name"] or "", row["email"] or ""), row["id"]))
        _db_ready = True
    except Exception as e:
        log.error("Failed to initialize auth database: %s", e)
        if _is_production():
            raise


def _env_product_id(plan_id: str) -> str:
    """Live product IDs come from the environment (DODO_PRODUCT_<PLAN_ID>), never from code defaults."""
    key = "DODO_PRODUCT_" + re.sub(r"[^A-Z0-9]", "_", plan_id.upper())
    return os.environ.get(key, "").strip()


def _record_ledger(conn: sqlite3.Connection, entity_type: str, entity_id: str, amount: int, balance_after: int,
                   event_type: str, reference_id: Optional[str] = None, description: Optional[str] = None) -> None:
    conn.execute("""
        INSERT INTO credit_ledger (entity_type, entity_id, amount, balance_after, event_type, reference_id, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (entity_type, entity_id, amount, balance_after, event_type, reference_id, description, time.time()))


def _entity(identity: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    if identity.get("authenticated") and identity.get("user_id"):
        return "user", identity["user_id"]
    if identity.get("is_guest") and identity.get("guest_id"):
        return "guest", identity["guest_id"]
    return None


def _table(entity_type: str) -> Tuple[str, str]:
    return ("users", "id") if entity_type == "user" else ("guest_sessions", "guest_id")


def _change_balance(conn: sqlite3.Connection, entity_type: str, entity_id: str, delta: int, event_type: str,
                    reference_id: Optional[str], description: str, allow_negative: bool = False) -> Optional[int]:
    """Applies delta inside the caller's IMMEDIATE transaction. Returns the new balance or None."""
    table, key = _table(entity_type)
    row = conn.execute(f"SELECT credits FROM {table} WHERE {key} = ?", (entity_id,)).fetchone()
    if not row:
        return None
    current = int(row["credits"] or 0)
    new_bal = current + delta
    if new_bal < 0 and not allow_negative:
        if delta < 0 and event_type == "payment_reversal":
            new_bal = 0  # claw back what is left; never go negative
        else:
            return None
    conn.execute(f"UPDATE {table} SET credits = ? WHERE {key} = ?", (new_bal, entity_id))
    _record_ledger(conn, entity_type, entity_id, new_bal - current, new_bal, event_type, reference_id, description)
    return new_bal


# --------------------------------------------------------------------------- #
# Plans
# --------------------------------------------------------------------------- #

def get_all_plans() -> List[Dict[str, Any]]:
    _init_db()
    try:
        with _connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM plans WHERE is_active = 1").fetchall()]
    except Exception as e:
        log.error("get_all_plans error: %s", e)
        return DEFAULT_PLANS


def get_plan(plan_id: str, default_to_free: bool = False) -> Optional[Dict[str, Any]]:
    plans = {p["id"]: p for p in get_all_plans()}
    for p in DEFAULT_PLANS:
        if p["id"] not in plans:
            plans[p["id"]] = p

    plan_id = str(plan_id or "")
    if plan_id in plans:
        return plans[plan_id]

    norm = plan_id.lower().replace("_", "")
    for k, v in plans.items():
        if k.lower().replace("_", "") == norm:
            return v

    return plans.get("free") if default_to_free else None


def plan_kind(plan_id: str) -> str:
    """'pack' = one-time credits (plan unchanged), 'pass' = 24h access, 'subscription' = recurring plan."""
    pid = (plan_id or "").lower()
    if pid.startswith("pack"):
        return "pack"
    if pid in ("day_pass", "daypass"):
        return "pass"
    return "subscription"


def find_plan_by_product(product_id: str) -> Optional[Dict[str, Any]]:
    if not product_id:
        return None
    for p in get_all_plans():
        if p.get("dodo_product_id") and p["dodo_product_id"] == product_id:
            return p
    return None


# --------------------------------------------------------------------------- #
# Usernames
# --------------------------------------------------------------------------- #

def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9_]+", "_", (value or "").lower()).strip("_")
    value = re.sub(r"_+", "_", value)
    return value[:16]


def _unique_username(conn: sqlite3.Connection, name: str, email: str) -> str:
    base = _slug(name) or _slug((email or "").split("@")[0]) or "creator"
    if len(base) < 3:
        base = (base + "creator")[:16]
    if base in _RESERVED_USERNAMES:
        base = f"{base}_user"[:16]
    for _ in range(50):
        candidate = f"{base}_{secrets.randbelow(9000) + 1000}"
        if not conn.execute("SELECT 1 FROM users WHERE username = ?", (candidate,)).fetchone():
            return candidate
    return f"{base}_{secrets.token_hex(4)}"


def validate_username(username: str) -> Optional[str]:
    u = (username or "").strip().lower()
    if not _USERNAME_REGEX.match(u):
        return "Username must be 3–24 characters: lowercase letters, numbers and underscore."
    if u in _RESERVED_USERNAMES:
        return "That username is reserved."
    return None


def change_username(user_id: str, username: str) -> Tuple[bool, Optional[str]]:
    err = validate_username(username)
    if err:
        return False, err
    u = username.strip().lower()
    try:
        with _connect(immediate=True) as conn:
            taken = conn.execute("SELECT id FROM users WHERE username = ? AND id != ?", (u, user_id)).fetchone()
            if taken:
                return False, "That username is already taken."
            conn.execute("UPDATE users SET username = ?, updated_at = ? WHERE id = ?", (u, time.time(), user_id))
        return True, None
    except sqlite3.IntegrityError:
        return False, "That username is already taken."


# --------------------------------------------------------------------------- #
# Guests
# --------------------------------------------------------------------------- #

def _guest_identity(r: Dict[str, Any]) -> Dict[str, Any]:
    plan_id = r.get("plan") or "free"
    plan_info = get_plan(plan_id) or get_plan("free") or {}
    return {
        "guest_id": r["guest_id"],
        "is_guest": True,
        "authenticated": False,
        "plan": plan_id,
        "plan_name": plan_info.get("name", "Free"),
        "credits": int(r.get("credits") or 0),
        "max_resolution": r.get("max_resolution") or plan_info.get("max_res", 480),
        "max_duration": plan_info.get("max_duration", 30),
        "converted_to": r.get("converted_to_user_id"),
        "name": "Guest Visitor",
        "email": None,
        "username": None,
        "avatar": None,
    }


def create_guest_session(ip: str) -> Dict[str, Any]:
    """Creates a guest with free trial credits. Clearing cookies does not mint unlimited credits:
    after GUESTS_PER_IP_PER_DAY new guests from one IP, further guests start with 0 credits."""
    _init_db()
    guest_id = f"gst_{uuid.uuid4().hex}"
    now = time.time()
    expires_at = now + (GUEST_EXPIRY_DAYS * 86400)
    credits = FREE_GUEST_CREDITS
    try:
        with _connect(immediate=True) as conn:
            recent = conn.execute(
                "SELECT COUNT(*) AS n FROM guest_sessions WHERE ip = ? AND created_at > ?", (ip, now - 86400)
            ).fetchone()["n"]
            if ip and recent >= GUESTS_PER_IP_PER_DAY:
                credits = 0
            conn.execute("""
                INSERT INTO guest_sessions (guest_id, ip, credits, last_daily_reset, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guest_id, ip, credits, now, now, expires_at))
            if credits:
                _record_ledger(conn, "guest", guest_id, credits, credits, "guest_trial_grant", None, "Free trial credits")
    except Exception as e:
        log.error("create_guest_session error: %s", e)
    return _guest_identity({"guest_id": guest_id, "plan": "free", "credits": credits, "max_resolution": 480})


def get_guest_session(guest_id: str) -> Optional[Dict[str, Any]]:
    if not guest_id or not re.fullmatch(r"gst_[0-9a-f]{32}", guest_id):
        return None
    try:
        with _connect(immediate=True) as conn:
            row = conn.execute("SELECT * FROM guest_sessions WHERE guest_id = ?", (guest_id,)).fetchone()
            if not row:
                return None
            r = dict(row)
            now = time.time()
            if r.get("expires_at") and r["expires_at"] < now and not r.get("converted_to_user_id"):
                return None
            # Free guests are topped back up to the daily allowance; purchased credits are never reset.
            if now - (r.get("last_daily_reset") or 0) > 86400:
                if (r.get("plan") or "free") == "free" and int(r.get("credits") or 0) < FREE_GUEST_CREDITS:
                    _change_balance(conn, "guest", guest_id, FREE_GUEST_CREDITS - int(r.get("credits") or 0),
                                    "daily_reset", None, "Daily free credit renewal")
                    r["credits"] = FREE_GUEST_CREDITS
                conn.execute("UPDATE guest_sessions SET last_daily_reset = ? WHERE guest_id = ?", (now, guest_id))
            return _guest_identity(r)
    except Exception as e:
        log.error("get_guest_session error: %s", e)
    return None


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #

def _user_identity(u: Dict[str, Any]) -> Dict[str, Any]:
    plan = u.get("plan") or "free"
    specs = get_plan(plan) or get_plan("free") or {}
    return {
        "id": u["id"],
        "user_id": u["id"],
        "email": u["email"],
        "username": u.get("username"),
        "name": u.get("name"),
        "avatar": u.get("avatar"),
        "plan": plan,
        "plan_name": specs.get("name", plan),
        "plan_status": u.get("plan_status") or "active",
        "credits": int(u.get("credits") or 0),
        "max_resolution": specs.get("max_res", 480),
        "max_duration": specs.get("max_duration", 30),
        "email_verified": bool(u.get("email_verified")),
        "has_password": bool(u.get("password_hash")),
        "authenticated": True,
        "is_guest": False,
    }


def _free_user_daily_topup(conn: sqlite3.Connection, u: Dict[str, Any]) -> None:
    """Time-based entitlements, applied lazily whenever the account is used:
    - an expired 24-hour pass falls back to Free;
    - yearly plans receive their monthly credits once per 30 days of the paid year;
    - Free accounts are topped back up to the daily floor."""
    now = time.time()
    plan = u.get("plan") or "free"
    if plan_kind(plan) == "pass" and u.get("plan_renews_at") and float(u["plan_renews_at"]) < now:
        conn.execute("UPDATE users SET plan = 'free', plan_status = 'expired', updated_at = ? WHERE id = ?", (now, u["id"]))
        u["plan"], u["plan_status"] = "free", "expired"
        plan = "free"
    if plan.endswith("_yearly"):
        g = conn.execute("""SELECT payment_id, credits, created_at FROM payment_grants
                            WHERE entity_type='user' AND entity_id=? AND plan_id=? AND status='granted'
                            ORDER BY created_at DESC LIMIT 1""", (u["id"], plan)).fetchone()
        if g:
            months = min(11, int((now - float(g["created_at"])) // MONTH_SECONDS))
            for k in range(1, months + 1):
                ref = f"{g['payment_id']}:m{k}"
                if not conn.execute("SELECT 1 FROM credit_ledger WHERE event_type='yearly_monthly_grant' AND entity_type='user' "
                                    "AND entity_id=? AND reference_id=?", (u["id"], ref)).fetchone():
                    new_bal = _change_balance(conn, "user", u["id"], int(g["credits"]), "yearly_monthly_grant", ref,
                                              f"Monthly credits (month {k + 1} of yearly plan)")
                    if new_bal is not None:
                        u["credits"] = new_bal
    if now - (u.get("last_daily_reset") or 0) <= 86400:
        return
    if plan == "free" and int(u.get("credits") or 0) < FREE_USER_DAILY_FLOOR:
        new_bal = _change_balance(conn, "user", u["id"], FREE_USER_DAILY_FLOOR - int(u.get("credits") or 0),
                                  "daily_reset", None, "Daily free credit renewal")
        if new_bal is not None:
            u["credits"] = new_bal
    conn.execute("UPDATE users SET last_daily_reset = ? WHERE id = ?", (now, u["id"]))


def _merge_guest(conn: sqlite3.Connection, user: Dict[str, Any], guest_id: Optional[str]) -> None:
    """Moves a guest's purchased plan and any credits above the free allowance to the account, once."""
    if not guest_id:
        return
    grow = conn.execute("SELECT * FROM guest_sessions WHERE guest_id = ?", (guest_id,)).fetchone()
    if not grow or grow["converted_to_user_id"]:
        return
    g = dict(grow)
    if g.get("plan") and g["plan"] != "free" and (user.get("plan") or "free") == "free":
        conn.execute("UPDATE users SET plan = ?, dodo_subscription_id = ? WHERE id = ?",
                     (g["plan"], g.get("dodo_subscription_id"), user["id"]))
        conn.execute("UPDATE subscriptions SET entity_type = 'user', entity_id = ? WHERE entity_type = 'guest' AND entity_id = ?",
                     (user["id"], guest_id))
        user["plan"] = g["plan"]
    extra = max(0, int(g.get("credits") or 0) - (FREE_GUEST_CREDITS if (g.get("plan") or "free") == "free" else 0))
    if extra > 0:
        _change_balance(conn, "guest", guest_id, -extra, "guest_transfer_out", user["id"], "Moved to account")
        new_bal = _change_balance(conn, "user", user["id"], extra, "guest_transfer", guest_id,
                                  "Transferred remaining credits from guest session")
        if new_bal is not None:
            user["credits"] = new_bal
    conn.execute("UPDATE guest_sessions SET converted_to_user_id = ? WHERE guest_id = ?", (user["id"], guest_id))


def google_client_ids() -> List[str]:
    raw = os.environ.get("GOOGLE_CLIENT_IDS") or os.environ.get("GOOGLE_CLIENT_ID") or ""
    return [c.strip() for c in raw.split(",") if c.strip()]


async def verify_google_credential(credential: str) -> Optional[Dict[str, Any]]:
    """Verifies a Google ID token: signature (by Google), audience = our client ID, issuer, expiry, verified email."""
    if not credential or len(credential) > 8192:
        return None
    audiences = google_client_ids()
    if not audiences:
        log.error("GOOGLE_CLIENT_ID is not configured; refusing Google sign-in")
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": credential})
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception as e:
        log.error("Google token verification failed: %s", e)
        return None
    if data.get("aud") not in audiences:
        log.warning("Google token rejected: audience mismatch")
        return None
    if data.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        return None
    try:
        if int(data.get("exp", 0)) < time.time():
            return None
    except (TypeError, ValueError):
        return None
    if str(data.get("email_verified", "")).lower() != "true" or not data.get("email") or not data.get("sub"):
        return None
    return {
        "sub": str(data["sub"]),
        "email": str(data["email"]).lower().strip(),
        "name": data.get("name") or str(data["email"]).split("@")[0],
        "avatar": data.get("picture", ""),
        "email_verified": True,
    }


def upsert_user_from_google(google_data: Dict[str, Any], guest_id: Optional[str] = None) -> Dict[str, Any]:
    """Signs in with a verified Google identity; links an existing same-email account safely."""
    _init_db()
    email = google_data["email"]
    sub = google_data.get("sub")
    name = (google_data.get("name") or "User")[:120]
    avatar = (google_data.get("avatar") or "")[:500]
    now = time.time()

    with _connect(immediate=True) as conn:
        row = None
        if sub:
            row = conn.execute("SELECT * FROM users WHERE google_sub = ?", (sub,)).fetchone()
        if not row:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if row:
            u = dict(row)
            if u.get("is_disabled"):
                raise PermissionError("This account is disabled.")
            if not u.get("email_verified") and u.get("password_hash"):
                # A password account nobody proved they own the email for. Google proves ownership now, so
                # drop that unverified password and end any sessions created with it (pre-hijack defence).
                conn.execute("""UPDATE users SET password_hash = NULL, session_version = COALESCE(session_version, 1) + 1
                                WHERE id = ?""", (u["id"],))
                u["password_hash"] = None
                u["session_version"] = int(u.get("session_version") or 1) + 1
            conn.execute("""UPDATE users SET name = COALESCE(NULLIF(name, ''), ?), avatar = ?, google_sub = ?,
                            email_verified = 1, updated_at = ? WHERE id = ?""", (name, avatar, sub, now, u["id"]))
            u.update({"avatar": avatar, "google_sub": sub, "email_verified": 1, "name": u.get("name") or name})
        else:
            user_id = f"usr_{uuid.uuid4().hex}"
            username = _unique_username(conn, name, email)
            conn.execute("""
                INSERT INTO users (id, email, username, google_sub, email_verified, name, avatar, plan, credits,
                                   daily_credits, last_daily_reset, session_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, 'free', 0, 2, ?, 1, ?, ?)
            """, (user_id, email, username, sub, name, avatar, now, now, now))
            if SIGNUP_BONUS_CREDITS:
                _change_balance(conn, "user", user_id, SIGNUP_BONUS_CREDITS, "signup_bonus", None, "Welcome bonus credits")
            u = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

        _merge_guest(conn, u, guest_id)
        _free_user_daily_topup(conn, u)
        u = dict(conn.execute("SELECT * FROM users WHERE id = ?", (u["id"],)).fetchone())
    return _user_identity(u)


def register_user_with_email(email: str, password: str, name: str = "", guest_id: Optional[str] = None,
                             username: str = "") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Registers a new email+password account. A username is generated unless a valid one is supplied."""
    _init_db()
    email = (email or "").strip().lower()
    if not email or len(email) > 254 or not _EMAIL_REGEX.match(email):
        return None, "Please enter a valid email address."
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return None, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    if len(password) > 256:
        return None, "Password is too long."
    if username:
        err = validate_username(username)
        if err:
            return None, err

    name = ((name or "").strip() or email.split("@")[0].capitalize())[:120]
    now = time.time()
    pwd_hash = hash_password(password)
    avatar = "https://api.dicebear.com/7.x/initials/svg?seed=" + re.sub(r"[^A-Za-z0-9]", "", name)[:32]

    try:
        with _connect(immediate=True) as conn:
            if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                return None, "An account with this email already exists. Please sign in."
            if username and conn.execute("SELECT 1 FROM users WHERE username = ?", (username.strip().lower(),)).fetchone():
                return None, "That username is already taken."
            final_username = username.strip().lower() if username else _unique_username(conn, name, email)
            user_id = f"usr_{uuid.uuid4().hex}"
            conn.execute("""
                INSERT INTO users (id, email, username, password_hash, email_verified, name, avatar, plan, credits,
                                   daily_credits, last_daily_reset, session_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, ?, 'free', 0, 2, ?, 1, ?, ?)
            """, (user_id, email, final_username, pwd_hash, name, avatar, now, now, now))
            if SIGNUP_BONUS_CREDITS:
                _change_balance(conn, "user", user_id, SIGNUP_BONUS_CREDITS, "signup_bonus", None, "Welcome bonus credits")
            u = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
            _merge_guest(conn, u, guest_id)
            u = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    except sqlite3.IntegrityError:
        return None, "An account with this email or username already exists."
    return _user_identity(u), None


_DUMMY_HASH = hash_password(secrets.token_hex(16))


def login_user_with_email(identifier: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Signs in with email OR username + password. Errors never reveal which accounts exist."""
    _init_db()
    ident = (identifier or "").strip().lower()
    if not ident or not password:
        return None, "Email/username and password are required."
    generic = "Incorrect email/username or password."
    with _connect(immediate=True) as conn:
        column = "email" if "@" in ident else "username"
        row = conn.execute(f"SELECT * FROM users WHERE {column} = ?", (ident,)).fetchone()
        if not row:
            verify_password(password, _DUMMY_HASH)  # equalise timing
            return None, generic
        u = dict(row)
        if not u.get("password_hash"):
            verify_password(password, _DUMMY_HASH)
            return None, "This account uses Sign in with Google."
        if not verify_password(password, u["password_hash"]):
            return None, generic
        if u.get("is_disabled"):
            return None, "This account is disabled."
        if not str(u["password_hash"]).startswith(f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"):
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), u["id"]))
        _free_user_daily_topup(conn, u)
        u = dict(conn.execute("SELECT * FROM users WHERE id = ?", (u["id"],)).fetchone())
    return _user_identity(u), None


def issue_session_jwt(user: Dict[str, Any]) -> str:
    now = int(time.time())
    user_id = user.get("id") or user.get("user_id")
    sv = user.get("session_version")
    if sv is None:
        try:
            with _connect() as conn:
                row = conn.execute("SELECT session_version FROM users WHERE id = ?", (user_id,)).fetchone()
                sv = int(row["session_version"] or 1) if row else 1
        except Exception:
            sv = 1
    payload = {
        "sub": user_id,
        "sv": int(sv),
        "iss": JWT_ISSUER,
        "typ": "session",
        "iat": now,
        "exp": now + (JWT_EXPIRY_DAYS * 86400),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_user_from_jwt(token: str) -> Optional[Dict[str, Any]]:
    if not token or len(token) > 4096:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], issuer=JWT_ISSUER,
                             options={"require": ["exp", "iat", "sub", "iss"]})
    except jwt.PyJWTError:
        return None
    if payload.get("typ") != "session":
        return None
    try:
        with _connect(immediate=True) as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)).fetchone()
            if not row:
                return None
            u = dict(row)
            if u.get("is_disabled") or int(u.get("session_version") or 1) != int(payload.get("sv") or 0):
                return None
            _free_user_daily_topup(conn, u)
    except Exception as e:
        log.error("get_user_from_jwt error: %s", e)
        return None
    return _user_identity(u)


def revoke_all_sessions(user_id: str) -> None:
    with _connect(immediate=True) as conn:
        conn.execute("UPDATE users SET session_version = COALESCE(session_version, 1) + 1 WHERE id = ?", (user_id,))


def resolve_request_identity(request: Request, create_guest: bool = True) -> Dict[str, Any]:
    """Resolves whether caller is an authenticated user or a guest."""
    token = request.headers.get("authorization", "")
    token = token[7:].strip() if token.startswith("Bearer ") else ""
    if not token:
        token = request.cookies.get("wpb_session", "")
    if token:
        user = get_user_from_jwt(token)
        if user:
            return user

    guest_id = request.headers.get("x-guest-id") or request.cookies.get("wpb_guest", "")
    guest = get_guest_session(guest_id)
    if guest and not guest.get("converted_to"):
        return guest

    if not create_guest:
        return {"is_guest": False, "authenticated": False, "credits": 0, "plan": "free"}
    try:
        from backend.security.zero_trust import client_ip
    except (ModuleNotFoundError, ImportError):  # pragma: no cover
        from security.zero_trust import client_ip  # type: ignore
    return create_guest_session(client_ip(request))


# --------------------------------------------------------------------------- #
# Credits
# --------------------------------------------------------------------------- #

def deduct_credit_for_job(identity: Dict[str, Any], cost: int = 1, job_id: Optional[str] = None) -> bool:
    """Atomically debits credits once per job (a retried request with the same job id is not charged twice)."""
    ent = _entity(identity)
    if not ent or cost < 0:
        return False
    if cost == 0:
        return True
    entity_type, entity_id = ent
    try:
        with _connect(immediate=True) as conn:
            if job_id and conn.execute(
                "SELECT 1 FROM credit_ledger WHERE event_type='job_render_debit' AND entity_type=? AND entity_id=? AND reference_id=?",
                (entity_type, entity_id, job_id),
            ).fetchone():
                return True
            label = "Guest video render job" if entity_type == "guest" else "Video render job"
            return _change_balance(conn, entity_type, entity_id, -int(cost), "job_render_debit", job_id,
                                   f"{label} {job_id or ''}".strip()) is not None
    except Exception as e:
        log.error("deduct_credit_for_job error: %s", e)
        return False


def refund_credit_for_job(identity: Dict[str, Any], amount: int = 1, job_id: Optional[str] = None,
                          reason: str = "Render failed") -> bool:
    """Refunds a job's debit exactly once, and never more than was actually debited for that job."""
    ent = _entity(identity)
    if not ent or amount <= 0:
        return False
    entity_type, entity_id = ent
    try:
        with _connect(immediate=True) as conn:
            if job_id:
                debit = conn.execute(
                    "SELECT -amount AS cost FROM credit_ledger WHERE event_type='job_render_debit' AND entity_type=? AND entity_id=? AND reference_id=?",
                    (entity_type, entity_id, job_id),
                ).fetchone()
                if not debit:
                    return False
                if conn.execute(
                    "SELECT 1 FROM credit_ledger WHERE event_type='job_refund' AND entity_type=? AND entity_id=? AND reference_id=?",
                    (entity_type, entity_id, job_id),
                ).fetchone():
                    return False
                amount = min(int(amount), int(debit["cost"]))
            return _change_balance(conn, entity_type, entity_id, int(amount), "job_refund", job_id, reason) is not None
    except Exception as e:
        log.error("refund_credit_for_job error: %s", e)
        return False


def get_credit_history(entity_type: str, entity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the append-only ledger transaction history."""
    try:
        with _connect() as conn:
            rows = conn.execute("""
                SELECT id, amount, balance_after, event_type, reference_id, description, created_at FROM credit_ledger
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC, id DESC LIMIT ?
            """, (entity_type, entity_id, max(1, min(int(limit), 200)))).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        log.error("get_credit_history error: %s", e)
        return []


def add_credits_to_identity(identity: Dict[str, Any], amount: int, reason: str, reference_id: Optional[str] = None) -> bool:
    """Adds credits to a user or guest, recorded in ledger (admin grants and promotions)."""
    ent = _entity(identity)
    if not ent or amount <= 0:
        return False
    try:
        with _connect(immediate=True) as conn:
            return _change_balance(conn, ent[0], ent[1], int(amount), "credit_grant", reference_id, reason) is not None
    except Exception as e:
        log.error("add_credits_to_identity error: %s", e)
        return False


# --------------------------------------------------------------------------- #
# Payments (called only from verified webhooks)
# --------------------------------------------------------------------------- #

def _owner_exists(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> bool:
    table, key = _table(entity_type)
    return bool(conn.execute(f"SELECT 1 FROM {table} WHERE {key} = ?", (entity_id,)).fetchone())


def resolve_owner(conn: sqlite3.Connection, user_id: str = "", guest_id: str = "", subscription_id: str = "",
                  email: str = "") -> Optional[Tuple[str, str]]:
    if user_id and _owner_exists(conn, "user", user_id):
        return "user", user_id
    if guest_id:
        g = conn.execute("SELECT converted_to_user_id FROM guest_sessions WHERE guest_id = ?", (guest_id,)).fetchone()
        if g:
            return ("user", g["converted_to_user_id"]) if g["converted_to_user_id"] else ("guest", guest_id)
    if subscription_id:
        s = conn.execute("SELECT entity_type, entity_id FROM subscriptions WHERE subscription_id = ?", (subscription_id,)).fetchone()
        if s:
            return s["entity_type"], s["entity_id"]
    if email:
        u = conn.execute("SELECT id FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if u:
            return "user", u["id"]
    return None


def grant_payment(payment_id: str, owner: Tuple[str, str], plan: Dict[str, Any], subscription_id: str = "",
                  amount_minor: Optional[int] = None, currency: str = "") -> Dict[str, Any]:
    """Applies one verified successful payment exactly once (keyed by provider payment id)."""
    entity_type, entity_id = owner
    kind = plan_kind(plan["id"])
    now = time.time()
    with _connect(immediate=True) as conn:
        if conn.execute("SELECT 1 FROM payment_grants WHERE payment_id = ?", (payment_id,)).fetchone():
            return {"ok": True, "action": "duplicate_payment"}
        if not _owner_exists(conn, entity_type, entity_id):
            return {"ok": False, "error": "owner_not_found"}
        credits = int(plan.get("credits") or 0)
        conn.execute("""
            INSERT INTO payment_grants (payment_id, entity_type, entity_id, plan_id, credits, subscription_id,
                                        amount_minor, currency, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'granted', ?, ?)
        """, (payment_id, entity_type, entity_id, plan["id"], credits, subscription_id or None, amount_minor,
              currency or None, now, now))
        table, key = _table(entity_type)
        if kind in ("subscription", "pass"):
            if entity_type == "user":
                if kind == "pass":
                    conn.execute("""UPDATE users SET plan = ?, plan_status = 'active', dodo_subscription_id = NULL,
                                    plan_renews_at = ?, updated_at = ? WHERE id = ?""",
                                 (plan["id"], now + DAY_PASS_SECONDS, now, entity_id))
                else:
                    conn.execute("""UPDATE users SET plan = ?, plan_status = 'active',
                                    dodo_subscription_id = COALESCE(?, dodo_subscription_id), updated_at = ? WHERE id = ?""",
                                 (plan["id"], subscription_id or None, now, entity_id))
            else:
                conn.execute("""UPDATE guest_sessions SET plan = ?, max_resolution = ?, dodo_subscription_id = COALESCE(?, dodo_subscription_id)
                                WHERE guest_id = ?""", (plan["id"], plan["max_res"], subscription_id or None, entity_id))
            if subscription_id:
                conn.execute("""
                    INSERT INTO subscriptions (subscription_id, entity_type, entity_id, plan_id, status, updated_at)
                    VALUES (?, ?, ?, ?, 'active', ?)
                    ON CONFLICT(subscription_id) DO UPDATE SET plan_id = excluded.plan_id, status = 'active', updated_at = excluded.updated_at
                """, (subscription_id, entity_type, entity_id, plan["id"], now))
        new_bal = _change_balance(conn, entity_type, entity_id, credits, "payment_grant", payment_id,
                                  f"Payment for {plan['name']}")
    return {"ok": True, "action": "granted", "entity_type": entity_type, "plan": plan["id"], "credits": credits,
            "balance": new_bal}


def reverse_payment(payment_id: str, reason: str) -> Dict[str, Any]:
    """Refund or dispute: claws back the credits granted by that payment (never below zero), once."""
    now = time.time()
    with _connect(immediate=True) as conn:
        g = conn.execute("SELECT * FROM payment_grants WHERE payment_id = ?", (payment_id,)).fetchone()
        if not g:
            return {"ok": True, "action": "no_grant_for_payment"}
        if g["status"] != "granted":
            return {"ok": True, "action": "already_reversed"}
        conn.execute("UPDATE payment_grants SET status = ?, updated_at = ? WHERE payment_id = ?",
                     ("reversed:" + reason[:40], now, payment_id))
        _change_balance(conn, g["entity_type"], g["entity_id"], -int(g["credits"]), "payment_reversal", payment_id,
                        f"Payment {reason}")
        if plan_kind(g["plan_id"]) != "pack":
            _set_plan_free(conn, g["entity_type"], g["entity_id"], "refunded")
    return {"ok": True, "action": "reversed"}


def _set_plan_free(conn: sqlite3.Connection, entity_type: str, entity_id: str, status: str) -> None:
    if entity_type == "user":
        conn.execute("UPDATE users SET plan = 'free', plan_status = ?, updated_at = ? WHERE id = ?", (status, time.time(), entity_id))
    else:
        conn.execute("UPDATE guest_sessions SET plan = 'free', max_resolution = 480 WHERE guest_id = ?", (entity_id,))


def update_subscription_status(subscription_id: str, status: str, owner: Optional[Tuple[str, str]] = None,
                               plan_id: str = "", next_billing_at: Optional[float] = None) -> Dict[str, Any]:
    """Tracks provider subscription state. Ending states downgrade the plan; remaining credits are kept."""
    now = time.time()
    ending = status in ("cancelled", "expired", "failed", "on_hold", "paused")
    with _connect(immediate=True) as conn:
        row = conn.execute("SELECT * FROM subscriptions WHERE subscription_id = ?", (subscription_id,)).fetchone()
        if row:
            entity_type, entity_id, current_plan = row["entity_type"], row["entity_id"], row["plan_id"]
        elif owner:
            entity_type, entity_id = owner
            current_plan = plan_id or "free"
        else:
            return {"ok": True, "action": "unknown_subscription"}
        conn.execute("""
            INSERT INTO subscriptions (subscription_id, entity_type, entity_id, plan_id, status, next_billing_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subscription_id) DO UPDATE SET status = excluded.status, plan_id = excluded.plan_id,
                next_billing_at = COALESCE(excluded.next_billing_at, subscriptions.next_billing_at), updated_at = excluded.updated_at
        """, (subscription_id, entity_type, entity_id, plan_id or current_plan, status, next_billing_at, now))
        if ending:
            # Only downgrade if this subscription is the one currently attached to the account.
            table, key = _table(entity_type)
            attached = conn.execute(f"SELECT dodo_subscription_id FROM {table} WHERE {key} = ?", (entity_id,)).fetchone()
            if attached and attached["dodo_subscription_id"] == subscription_id:
                _set_plan_free(conn, entity_type, entity_id, status)
        elif entity_type == "user" and plan_id and plan_kind(plan_id) == "subscription":
            conn.execute("""UPDATE users SET plan = ?, plan_status = 'active', dodo_subscription_id = ?, plan_renews_at = COALESCE(?, plan_renews_at)
                            WHERE id = ?""", (plan_id, subscription_id, next_billing_at, entity_id))
    return {"ok": True, "action": f"subscription_{status}"}


# Backwards-compatible helpers used by older callers/tests. They now route through the exactly-once grant path.
def upgrade_user_plan(user_id: str, plan_id: str, dodo_subscription_id: Optional[str] = None) -> bool:
    plan = get_plan(plan_id) or get_plan(plan_id.lower().replace("_", ""))
    if not plan:
        log.error("upgrade_user_plan: unknown plan '%s'", plan_id)
        return False
    ref = dodo_subscription_id or f"manual_{uuid.uuid4().hex}"
    return bool(grant_payment(ref, ("user", user_id), plan).get("ok"))


def upgrade_guest_plan(guest_id: str, plan_id: str, dodo_subscription_id: Optional[str] = None) -> bool:
    plan = get_plan(plan_id) or get_plan(plan_id.lower().replace("_", ""))
    if not plan:
        log.error("upgrade_guest_plan: unknown plan '%s'", plan_id)
        return False
    ref = dodo_subscription_id or f"manual_{uuid.uuid4().hex}"
    return bool(grant_payment(ref, ("guest", guest_id), plan).get("ok"))


def claim_webhook_event(webhook_id: str, event_type: str) -> bool:
    """Returns True the first time a webhook id is seen; False for a replay/retry already processed."""
    try:
        with _connect(immediate=True) as conn:
            conn.execute("INSERT INTO payment_webhook_events (webhook_id, event_type, received_at) VALUES (?, ?, ?)",
                         (webhook_id, event_type, time.time()))
        return True
    except sqlite3.IntegrityError:
        return False


def finish_webhook_event(webhook_id: str, result: str) -> None:
    with _connect(immediate=True) as conn:
        conn.execute("UPDATE payment_webhook_events SET result = ? WHERE webhook_id = ?", (result[:500], webhook_id))


def release_webhook_event(webhook_id: str) -> None:
    """Processing failed: forget the claim so the provider's retry is processed."""
    with _connect(immediate=True) as conn:
        conn.execute("DELETE FROM payment_webhook_events WHERE webhook_id = ?", (webhook_id,))


# --------------------------------------------------------------------------- #
# Service tokens (Make.com / n8n / Colab / cron): scoped, hashed, revocable
# --------------------------------------------------------------------------- #

SERVICE_TOKEN_PREFIX = "ovd_st_"
SERVICE_SCOPES = ("media:resolve", "media:download", "media:upload", "editor:render", "editor:read", "admin:read")


def _token_hash(token: str) -> str:
    pepper = (os.environ.get("SERVICE_TOKEN_PEPPER") or JWT_SECRET).encode()
    return hmac.new(pepper, token.encode(), hashlib.sha256).hexdigest()


def create_service_token(name: str, scopes: List[str], created_by: str, ttl_days: Optional[int] = None) -> Dict[str, Any]:
    clean = sorted({s for s in scopes if s in SERVICE_SCOPES})
    if not clean:
        raise ValueError("At least one valid scope is required: " + ", ".join(SERVICE_SCOPES))
    name = re.sub(r"[^\w .:-]", "", name or "")[:80] or "integration"
    token = SERVICE_TOKEN_PREFIX + secrets.token_urlsafe(32)
    tid = f"st_{uuid.uuid4().hex[:16]}"
    now = time.time()
    expires = now + ttl_days * 86400 if ttl_days else None
    with _connect(immediate=True) as conn:
        conn.execute("""INSERT INTO service_tokens (id, name, token_hash, scopes, created_by, created_at, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""", (tid, name, _token_hash(token), ",".join(clean), created_by, now, expires))
    # The plain token is shown exactly once.
    return {"id": tid, "name": name, "scopes": clean, "token": token, "expires_at": expires}


def list_service_tokens() -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("""SELECT id, name, scopes, created_by, created_at, expires_at, last_used_at, revoked_at
                               FROM service_tokens ORDER BY created_at DESC""").fetchall()
    return [dict(r) | {"scopes": (r["scopes"] or "").split(",")} for r in rows]


def revoke_service_token(token_id: str) -> bool:
    with _connect(immediate=True) as conn:
        cur = conn.execute("UPDATE service_tokens SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL", (time.time(), token_id))
        return cur.rowcount == 1


def verify_service_token(token: str, scope: str) -> Optional[Dict[str, Any]]:
    if not token or not token.startswith(SERVICE_TOKEN_PREFIX) or len(token) > 128:
        return None
    _init_db()
    now = time.time()
    try:
        with _connect() as conn:
            row = conn.execute("SELECT * FROM service_tokens WHERE token_hash = ?", (_token_hash(token),)).fetchone()
            if not row or row["revoked_at"] or (row["expires_at"] and row["expires_at"] < now):
                return None
            scopes = set((row["scopes"] or "").split(","))
            if scope not in scopes:
                return None
            if not row["last_used_at"] or now - row["last_used_at"] > 300:
                conn.execute("UPDATE service_tokens SET last_used_at = ? WHERE id = ?", (now, row["id"]))
            return {"id": row["id"], "name": row["name"], "scopes": sorted(scopes)}
    except Exception as e:
        log.error("verify_service_token error: %s", e)
        return None


_init_db()
