"""Regression tests for the LIVE-launch blockers: auth, Dodo webhooks, credits, service tokens, render worker."""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient

from backend.main import app
from backend.services import auth_service, dodo_service

ORIGIN = {"Origin": "https://ovd.winplaybox.in"}
SECRET_RAW = b"0123456789abcdef0123456789abcdef"
WHSEC = "whsec_" + base64.b64encode(SECRET_RAW).decode()


def _sign(body: bytes, wid: str = None, ts: int = None):
    wid = wid or f"msg_{uuid.uuid4().hex}"
    ts = int(time.time()) if ts is None else ts
    sig = base64.b64encode(hmac.new(SECRET_RAW, f"{wid}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
    return {"webhook-id": wid, "webhook-timestamp": str(ts), "webhook-signature": f"v1,{sig}",
            "content-type": "application/json"}


def _new_user(**kw):
    email = kw.pop("email", f"u{uuid.uuid4().hex[:10]}@example.com")
    user, err = auth_service.register_user_with_email(email, kw.pop("password", "correct horse battery"), **kw)
    assert user, err
    return user


class TestAuth(unittest.TestCase):
    def test_signup_generates_username_and_login_by_username_or_email(self):
        user = _new_user(name="Sagar Mistry")
        self.assertRegex(user["username"], r"^sagar_mistry_\d{4}$")
        by_name, err = auth_service.login_user_with_email(user["username"], "correct horse battery")
        self.assertIsNotNone(by_name, err)
        by_mail, _ = auth_service.login_user_with_email(user["email"].upper(), "correct horse battery")
        self.assertEqual(by_mail["id"], user["id"])
        bad, err = auth_service.login_user_with_email(user["username"], "wrong password")
        self.assertIsNone(bad)
        self.assertEqual(err, "Incorrect email/username or password.")
        missing, err2 = auth_service.login_user_with_email("nobody_9999", "whatever123")
        self.assertEqual(err, err2)  # no account enumeration

    def test_short_password_and_reserved_username_rejected(self):
        self.assertIsNone(auth_service.register_user_with_email("a@b.co", "short")[0])
        self.assertIsNone(auth_service.register_user_with_email("c@d.co", "longenough123", username="admin")[0])

    def test_username_change_is_unique(self):
        a, b = _new_user(), _new_user()
        ok, _ = auth_service.change_username(a["id"], "unique_name_x1")
        self.assertTrue(ok)
        ok2, err = auth_service.change_username(b["id"], "unique_name_x1")
        self.assertFalse(ok2)
        self.assertIn("taken", err)

    def test_legacy_password_hash_still_verifies_and_is_upgraded(self):
        salt = "abcd" * 8
        legacy = f"{salt}:{hashlib.pbkdf2_hmac('sha256', b'oldpassword1', salt.encode(), 100_000).hex()}"
        self.assertTrue(auth_service.verify_password("oldpassword1", legacy))
        self.assertFalse(auth_service.verify_password("nope", legacy))

    def test_google_rejects_wrong_audience_and_unverified_email(self):
        good = {"aud": "test-client.apps.googleusercontent.com", "iss": "accounts.google.com", "exp": str(int(time.time()) + 600),
                "email": "g@example.com", "email_verified": "true", "sub": "123"}
        for override, expect_ok in (({}, True), ({"aud": "someone-else.apps.googleusercontent.com"}, False),
                                    ({"email_verified": "false"}, False), ({"iss": "evil.example"}, False),
                                    ({"exp": str(int(time.time()) - 10)}, False)):
            payload = dict(good, **override)
            resp = MagicMock(status_code=200)
            resp.json.return_value = payload
            client = AsyncMock()
            client.__aenter__.return_value.get = AsyncMock(return_value=resp)
            with patch("backend.services.auth_service.httpx.AsyncClient", return_value=client):
                result = asyncio.run(auth_service.verify_google_credential("x.y.z"))
            self.assertEqual(result is not None, expect_ok, override)

    def test_google_login_takes_over_unverified_password_account_and_kills_its_sessions(self):
        squatter = _new_user(email="victim@example.com")
        old_token = auth_service.issue_session_jwt(squatter)
        self.assertIsNotNone(auth_service.get_user_from_jwt(old_token))
        user = auth_service.upsert_user_from_google({"sub": "g-victim", "email": "victim@example.com", "name": "Victim"})
        self.assertEqual(user["id"], squatter["id"])
        self.assertTrue(user["email_verified"])
        self.assertFalse(user["has_password"])
        self.assertIsNone(auth_service.get_user_from_jwt(old_token))
        self.assertIsNone(auth_service.login_user_with_email("victim@example.com", "correct horse battery")[0])

    def test_jwt_must_be_ours(self):
        import jwt
        forged = jwt.encode({"sub": "usr_x", "exp": int(time.time()) + 60, "iat": int(time.time())}, "guess", algorithm="HS256")
        self.assertIsNone(auth_service.get_user_from_jwt(forged))

    def test_logout_all_revokes_tokens(self):
        user = _new_user()
        tok = auth_service.issue_session_jwt(user)
        auth_service.revoke_all_sessions(user["id"])
        self.assertIsNone(auth_service.get_user_from_jwt(tok))

    def test_http_register_login_flow(self):
        c = TestClient(app, headers=ORIGIN)
        email = f"h{uuid.uuid4().hex[:8]}@example.com"
        r = c.post("/api/auth/register", json={"email": email, "password": "goodpassword9", "name": "Http User"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["user"]["username"].startswith("http_user_"))
        r2 = c.post("/api/auth/login", json={"identifier": r.json()["user"]["username"], "password": "goodpassword9"})
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertIn("token", r2.json())
        cfg = c.get("/api/auth/config").json()
        self.assertEqual(cfg["google_client_id"], "test-client.apps.googleusercontent.com")


class TestGuestCredits(unittest.TestCase):
    def test_purchased_guest_credits_survive_daily_reset(self):
        g = auth_service.create_guest_session("198.51.100.10")
        plan = auth_service.get_plan("pack_100")
        auth_service.grant_payment(f"pay_{uuid.uuid4().hex}", ("guest", g["guest_id"]), plan)
        with auth_service._connect(immediate=True) as conn:
            conn.execute("UPDATE guest_sessions SET last_daily_reset = 0 WHERE guest_id = ?", (g["guest_id"],))
        again = auth_service.get_guest_session(g["guest_id"])
        self.assertGreaterEqual(again["credits"], 100)

    def test_guest_farming_from_one_ip_is_capped(self):
        ip = f"203.0.113.{uuid.uuid4().int % 250}"
        with patch.object(auth_service, "GUESTS_PER_IP_PER_DAY", 2):
            credits = [auth_service.create_guest_session(ip)["credits"] for _ in range(4)]
        self.assertEqual(credits[:2], [auth_service.FREE_GUEST_CREDITS] * 2)
        self.assertEqual(credits[2:], [0, 0])

    def test_debit_once_and_refund_once(self):
        user = _new_user()
        ident = {"authenticated": True, "user_id": user["id"]}
        start = user["credits"]
        self.assertTrue(auth_service.deduct_credit_for_job(ident, 2, "job-a"))
        self.assertTrue(auth_service.deduct_credit_for_job(ident, 2, "job-a"))  # idempotent retry, no 2nd charge
        self.assertTrue(auth_service.refund_credit_for_job(ident, 5, "job-a"))   # capped at what was debited
        self.assertFalse(auth_service.refund_credit_for_job(ident, 2, "job-a"))  # never twice
        self.assertFalse(auth_service.refund_credit_for_job(ident, 2, "job-never-debited"))
        self.assertEqual(auth_service.get_user_from_jwt(auth_service.issue_session_jwt(user))["credits"], start)


class TestDodoWebhook(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"DODO_PAYMENTS_WEBHOOK_SECRET": WHSEC})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(app)
        self.user = _new_user()

    def _post(self, event, headers=None, body=None):
        body = body if body is not None else json.dumps(event).encode()
        return self.client.post("/api/payments/dodo/webhook", content=body, headers=headers or _sign(body))

    def _credits(self):
        return auth_service.get_user_from_jwt(auth_service.issue_session_jwt(self.user))["credits"]

    def _payment(self, plan_id="pack_100", pay_id=None, sub_id=None, **meta):
        data = {"payment_id": pay_id or f"pay_{uuid.uuid4().hex}", "total_amount": 29900, "currency": "INR",
                "metadata": {"app": "ovd_editor", "plan_id": plan_id, "user_id": self.user["id"], **meta}}
        if sub_id:
            data["subscription_id"] = sub_id
        return {"type": "payment.succeeded", "data": data}

    def test_rejects_bad_signature_stale_timestamp_and_missing_secret(self):
        event = self._payment()
        body = json.dumps(event).encode()
        bad = _sign(body)
        bad["webhook-signature"] = "v1," + base64.b64encode(b"x" * 32).decode()
        self.assertEqual(self._post(event, bad, body).status_code, 401)
        self.assertEqual(self._post(event, _sign(body, ts=int(time.time()) - 3600), body).status_code, 401)
        with patch.dict(os.environ, {"DODO_PAYMENTS_WEBHOOK_SECRET": "", "DODO_WEBHOOK_SECRET": ""}):
            self.assertEqual(self._post(event, _sign(body), body).status_code, 401)

    def test_pack_grants_credits_once_and_keeps_plan(self):
        before = self._credits()
        event = self._payment("pack_100")
        body = json.dumps(event).encode()
        headers = _sign(body)
        self.assertEqual(self._post(event, headers, body).status_code, 200)
        self.assertEqual(self._post(event, headers, body).json().get("duplicate"), True)       # same webhook-id replay
        self.assertEqual(self._post(event).status_code, 200)                                   # new id, same payment
        self.assertEqual(self._credits(), before + 100)
        self.assertEqual(auth_service.get_user_from_jwt(auth_service.issue_session_jwt(self.user))["plan"], "free")

    def test_subscription_events_do_not_double_grant_and_cancel_downgrades(self):
        before = self._credits()
        sub = f"sub_{uuid.uuid4().hex}"
        self.assertEqual(self._post(self._payment("plan2", sub_id=sub)).status_code, 200)
        active = {"type": "subscription.active", "data": {"subscription_id": sub, "metadata": {"app": "ovd_editor",
                  "plan_id": "plan2", "user_id": self.user["id"]}, "next_billing_date": "2026-12-20T00:00:00Z"}}
        self.assertEqual(self._post(active).status_code, 200)
        me = auth_service.get_user_from_jwt(auth_service.issue_session_jwt(self.user))
        self.assertEqual(me["plan"], "plan2")
        self.assertEqual(me["credits"], before + 75)
        # renewal: a new payment for the same subscription without our metadata still resolves owner + plan
        renewal = {"type": "payment.succeeded", "data": {"payment_id": f"pay_{uuid.uuid4().hex}", "subscription_id": sub,
                                                         "metadata": {"app": "ovd_editor"}}}
        self.assertEqual(self._post(renewal).status_code, 200)
        self.assertEqual(self._credits(), before + 150)
        cancelled = {"type": "subscription.cancelled", "data": {"subscription_id": sub, "metadata": {"app": "ovd_editor"}}}
        self.assertEqual(self._post(cancelled).status_code, 200)
        me = auth_service.get_user_from_jwt(auth_service.issue_session_jwt(self.user))
        self.assertEqual(me["plan"], "free")
        self.assertEqual(me["credits"], before + 150)  # paid credits are kept

    def test_refund_claws_back_once(self):
        before = self._credits()
        pay = f"pay_{uuid.uuid4().hex}"
        self._post(self._payment("pack_100", pay_id=pay))
        refund = {"type": "refund.succeeded", "data": {"payment_id": pay, "refund_id": "rf_1", "metadata": {"app": "ovd_editor"}}}
        self._post(refund)
        self._post(refund)
        self.assertEqual(self._credits(), before)

    def test_studio_events_are_ignored(self):
        event = {"type": "payment.succeeded", "data": {"payment_id": "pay_studio", "metadata": {"order_id": "ord_1"}}}
        self.assertEqual(self._post(event).status_code, 200)
        with auth_service._connect() as conn:
            self.assertIsNone(conn.execute("SELECT 1 FROM payment_grants WHERE payment_id='pay_studio'").fetchone())

    def test_unknown_owner_asks_dodo_to_retry(self):
        event = self._payment("pack_100", user_id="usr_does_not_exist")
        self.assertEqual(self._post(event).status_code, 503)


class TestCheckout(unittest.TestCase):
    def test_guest_must_sign_in_and_live_needs_env_product_ids(self):
        c = TestClient(app, headers=ORIGIN)
        r = c.post("/api/payments/dodo/checkout", json={"plan_id": "plan1"})
        self.assertEqual(r.status_code, 401)
        self.assertTrue(r.json()["auth_required"])
        with patch.object(dodo_service, "DODO_ENV", "live"), patch.dict(os.environ, {"DODO_PRODUCT_PLAN1": ""}):
            self.assertEqual(dodo_service.product_id_for("plan1"), "")
        with patch.object(dodo_service, "DODO_ENV", "live"), patch.dict(os.environ, {"DODO_PRODUCT_PLAN1": "pdt_live_1"}):
            self.assertEqual(dodo_service.product_id_for("plan1"), "pdt_live_1")

    def test_return_url_cannot_leave_our_site(self):
        self.assertEqual(dodo_service.safe_return_url("https://evil.example/steal"), dodo_service.SUCCESS_RETURN_URL)
        self.assertEqual(dodo_service.safe_return_url("https://ovd.winplaybox.in/ai-video-editor?x=1"),
                         "https://ovd.winplaybox.in/ai-video-editor?x=1")


class TestServiceTokens(unittest.TestCase):
    def test_scoped_hashed_revocable(self):
        created = auth_service.create_service_token("make.com dhrusa", ["media:resolve"], "admin:test")
        tok = created["token"]
        self.assertTrue(tok.startswith("ovd_st_"))
        self.assertIsNotNone(auth_service.verify_service_token(tok, "media:resolve"))
        self.assertIsNone(auth_service.verify_service_token(tok, "editor:render"))
        with auth_service._connect() as conn:
            self.assertIsNone(conn.execute("SELECT 1 FROM service_tokens WHERE token_hash = ?", (tok,)).fetchone())
        auth_service.revoke_service_token(created["id"])
        self.assertIsNone(auth_service.verify_service_token(tok, "media:resolve"))

    def test_admin_api_and_middleware(self):
        from tests.conftest import TEST_ADMIN_KEY
        c = TestClient(app)
        with patch("backend.routes_admin_ops.record_admin_failure"), \
                patch("backend.security.zero_trust.record_admin_failure"):  # keep the shared lockout counter clean
            self.assertEqual(c.post("/admin/ovd/service-tokens", json={"name": "x", "scopes": ["media:resolve"]}).status_code, 401)
        r = c.post("/admin/ovd/service-tokens", json={"name": "n8n", "scopes": ["editor:read"]},
                   headers={"X-Admin-Key": TEST_ADMIN_KEY})
        self.assertEqual(r.status_code, 200, r.text)
        tok = r.json()["token"]["token"]
        # editor:read lets a server read options without a browser Origin; a POST needs editor:render
        self.assertEqual(c.get("/api/editor/options", headers={"X-API-Key": tok}).status_code, 200)
        self.assertEqual(c.post("/api/editor/jobs", headers={"X-API-Key": tok}).status_code, 403)
        self.assertEqual(c.get("/api/editor/options", headers={"X-API-Key": "ovd_st_bogus"}).status_code, 403)
        self.assertEqual(c.get("/api/editor/options").status_code, 403)  # no origin, no token


class TestWorker(unittest.TestCase):
    def setUp(self):
        import fakeredis
        import tempfile
        from backend import editor_worker
        from backend.services.video_editor import pipeline
        self.pipeline, self.worker = pipeline, editor_worker
        self.r = fakeredis.FakeRedis(decode_responses=True)
        wd = patch.object(pipeline, "WORK_DIR", tempfile.mkdtemp(prefix="wk_"))
        wd.start()
        self.addCleanup(wd.stop)
        self.user = _new_user()
        self.ident = {"authenticated": True, "user_id": self.user["id"]}

    def _job(self, cost=1):
        job = self.pipeline.new_job({"language": "en"}, "ck")
        src = os.path.join(self.pipeline.job_dir(job["id"]), "source.mp4")
        open(src, "wb").write(b"\x00")
        auth_service.deduct_credit_for_job(self.ident, cost, job["id"])
        job["billing"] = {"entity_type": "user", "entity_id": self.user["id"], "cost": cost}
        job["source_path"] = src
        self.pipeline.save_job(job)
        return job

    def _credits(self):
        return auth_service.get_user_from_jwt(auth_service.issue_session_jwt(self.user))["credits"]

    def test_failed_render_refunds_once(self):
        job = self._job(cost=2)
        before = self._credits()

        async def boom(j, src, on_finish):
            self.pipeline._update(j, status="failed", error="x")
            await on_finish(j)
        self.r.lpush(self.pipeline.PROCESSING_KEY, job["id"])
        with patch.object(self.pipeline, "_run", boom):
            asyncio.run(self.worker.run_job(self.r, job["id"]))
        self.worker.settle(self.pipeline.load_job(job["id"]))  # second settle is a no-op
        self.assertEqual(self._credits(), before + 2)
        self.assertEqual(self.r.llen(self.pipeline.PROCESSING_KEY), 0)

    def test_orphan_is_requeued_then_failed_and_refunded(self):
        job = self._job(cost=1)
        before = self._credits()
        self.r.lpush(self.pipeline.PROCESSING_KEY, job["id"])  # worker died: no lease key
        self.assertEqual(self.worker.reap_orphans(self.r), 1)
        self.assertEqual(self.r.lrange(self.pipeline.QUEUE_KEY, 0, -1), [job["id"]])
        j = self.pipeline.load_job(job["id"])
        j["attempts"] = self.worker.MAX_ATTEMPTS
        self.pipeline.save_job(j)
        self.r.delete(self.pipeline.QUEUE_KEY)
        self.r.lpush(self.pipeline.PROCESSING_KEY, job["id"])
        self.worker.reap_orphans(self.r)
        self.assertEqual(self.pipeline.load_job(job["id"])["status"], "failed")
        self.assertEqual(self._credits(), before + 1)

    def test_live_lease_is_not_reaped(self):
        job = self._job()
        self.r.lpush(self.pipeline.PROCESSING_KEY, job["id"])
        self.r.set(self.pipeline.LEASE_PREFIX + job["id"], "w", ex=60)
        self.assertEqual(self.worker.reap_orphans(self.r), 0)


class TestTimedEntitlements(unittest.TestCase):
    def _me(self, user):
        return auth_service.get_user_from_jwt(auth_service.issue_session_jwt(user))

    def test_day_pass_expires_after_24h(self):
        user = _new_user()
        auth_service.grant_payment(f"pay_{uuid.uuid4().hex}", ("user", user["id"]), auth_service.get_plan("day_pass"))
        self.assertEqual(self._me(user)["plan"], "day_pass")
        with auth_service._connect(immediate=True) as conn:
            conn.execute("UPDATE users SET plan_renews_at = ? WHERE id = ?", (time.time() - 1, user["id"]))
        self.assertEqual(self._me(user)["plan"], "free")

    def test_yearly_plan_gets_monthly_credits_once_per_month(self):
        user = _new_user()
        pay = f"pay_{uuid.uuid4().hex}"
        auth_service.grant_payment(pay, ("user", user["id"]), auth_service.get_plan("plan1_yearly"), subscription_id="sub_y")
        start = self._me(user)["credits"]
        with auth_service._connect(immediate=True) as conn:
            conn.execute("UPDATE payment_grants SET created_at = ? WHERE payment_id = ?", (time.time() - 65 * 86400, pay))
        self.assertEqual(self._me(user)["credits"], start + 2 * 30)
        self.assertEqual(self._me(user)["credits"], start + 2 * 30)  # not granted again


if __name__ == "__main__":
    unittest.main()
