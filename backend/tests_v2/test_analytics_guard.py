"""Analytics events + admin endpoint + YouTube circuit breaker."""
import asyncio
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.setdefault("WPB_VAULT_SECRET", "test_secret_key_" + "x" * 40)
os.environ.setdefault("WPB_ADMIN_KEY", "admin_key_for_tests_" + "y" * 30)

from starlette.testclient import TestClient  # noqa: E402

from backend.services import analytics, yt_guard  # noqa: E402


def test_breaker_opens_after_three_blocks_then_closes_on_success():
    assert yt_guard.retry_after() == 0
    for _ in range(3):
        yt_guard.failure()
    assert yt_guard.retry_after() > 0 and yt_guard.state()["open"]
    yt_guard.success()
    assert yt_guard.retry_after() == 0 and not yt_guard.state()["open"]


def test_breaker_two_blocks_do_not_open():
    yt_guard.failure(); yt_guard.failure()
    assert yt_guard.retry_after() == 0


def test_parse_ua_and_platform():
    assert analytics.parse_ua("Mozilla/5.0 (iPhone; CPU iPhone OS 17) Safari/605")["device"] == "mobile"
    assert analytics.parse_ua("curl/8.0")["device"] == "bot"
    assert analytics.parse_ua("Mozilla/5.0 (Windows NT 10) Chrome/120 Safari/537")["browser"] == "Chrome"
    assert analytics.platform_from_url("https://youtu.be/abc") == "youtube"
    assert analytics.platform_from_url("https://www.instagram.com/reel/x") == "instagram"
    assert analytics.platform_from_url("https://example.org/v.mp4") == "other"


def _client():
    from backend.main import app
    return TestClient(app)


ORIGIN = {"Origin": "https://ovd.winplaybox.in"}
OWNER = "owner@example.com"


def test_download_error_is_tracked_and_dashboard_requires_login(monkeypatch):
    import backend.main as m
    c = _client()
    r = c.get("/api/download_video", params={"url": "http://127.0.0.1/x", "height": "720"})
    assert r.status_code == 400
    time.sleep(0.2)
    assert analytics._MEM and analytics._MEM[-1]["kind"] == "download" and analytics._MEM[-1]["status"] == "fail"
    assert analytics._MEM[-1]["code"] == "URL_INVALID"

    assert c.get("/api/ovd/analytics", headers=ORIGIN).status_code == 401      # no login

    async def fake(request):                                                   # Google login check result
        return OWNER if request.headers.get("authorization") == "Bearer good.token.x" else None
    monkeypatch.setattr(m, "_google_admin_email", fake)
    assert c.get("/api/ovd/analytics", headers={**ORIGIN, "Authorization": "Bearer other.token.x"}).status_code == 401
    ok = c.get("/api/ovd/analytics", headers={**ORIGIN, "Authorization": "Bearer good.token.x"}, params={"days": 7})
    assert ok.status_code == 200
    j = ok.json()
    assert j["ok"] and j["source"] == "memory" and j["storage_warning"]
    assert j["totals"]["downloads"] == 1 and j["errors"][0]["code"] == "URL_INVALID"
    assert j["youtube"]["breaker"]["open"] is False
    assert len(j["daily"]) == 7 and sum(j["hourly_ist"]) == 1
    assert "127.0.0.1" not in str(j["recent"])      # no IPs leak into the dashboard payload


def test_google_admin_allowlist(monkeypatch):
    import backend.main as m
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc")
    monkeypatch.setenv("WPB_ADMIN_EMAILS", OWNER)
    users = {"t1.a.b": {"email": OWNER, "email_confirmed_at": "2026-01-01"},
             "t2.a.b": {"email": "intruder@example.com", "email_confirmed_at": "2026-01-01"},
             "t3.a.b": {"email": OWNER, "email_confirmed_at": None}}

    class R:
        status_code = 200
        def __init__(self, tok): self.tok = tok
        def json(self): return users[self.tok]

    class C:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, headers=None): return R(headers["Authorization"].split()[1])

    monkeypatch.setattr(m.httpx, "AsyncClient", C)
    m._ADMIN_TOKEN_CACHE.clear()

    class Req:
        def __init__(self, t): self.headers = {"authorization": f"Bearer {t}"}
    assert asyncio.run(m._google_admin_email(Req("t1.a.b"))) == OWNER
    assert asyncio.run(m._google_admin_email(Req("t2.a.b"))) is None
    assert asyncio.run(m._google_admin_email(Req("t3.a.b"))) is None
    assert asyncio.run(m._google_admin_email(Req("garbage"))) is None


def test_youtube_download_skipped_while_cooling_down(monkeypatch):
    import backend.main as m
    monkeypatch.setattr(m, "_is_public_http_url", lambda u: True)   # sandbox has no DNS
    for _ in range(3):
        yt_guard.failure()
    r = _client().get("/api/download_video", params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "height": "720"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "SOURCE_BLOCKED"
    assert int(r.headers["Retry-After"]) >= 1


def test_summarize_rates():
    now = analytics.datetime.now(analytics.timezone.utc).isoformat()
    rows = [
        {"ts": now, "kind": "resolve", "platform": "youtube", "status": "ok", "visitor": "a", "url": "u1", "title": "T"},
        {"ts": now, "kind": "download", "platform": "youtube", "status": "ok", "visitor": "a", "url": "u1", "title": "T", "device": "mobile"},
        {"ts": now, "kind": "download", "platform": "youtube", "status": "fail", "code": "SOURCE_BLOCKED", "visitor": "b", "url": "u2"},
    ]
    s = analytics.summarize(rows, 1)
    assert s["totals"]["visitors"] == 2 and s["totals"]["download_ok_pct"] == 50.0
    assert s["youtube"]["ok_pct_24h"] == 50.0 and s["top_content"][0]["url"] == "u1"
