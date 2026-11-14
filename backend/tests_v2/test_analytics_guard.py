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


def test_download_error_is_tracked_and_dashboard_needs_key():
    c = _client()
    KEY = os.environ["WPB_ADMIN_KEY"]
    # invalid/unsafe URL -> tracked as a failed download with its code
    r = c.get("/api/download_video", params={"url": "http://127.0.0.1/x", "height": "720"})
    assert r.status_code == 400
    time.sleep(0.2)
    assert analytics._MEM and analytics._MEM[-1]["kind"] == "download" and analytics._MEM[-1]["status"] == "fail"
    assert analytics._MEM[-1]["code"] == "URL_INVALID"

    assert c.get("/admin/analytics").status_code == 401
    ok = c.get("/admin/analytics", headers={"x-admin-key": KEY}, params={"days": 7})
    assert ok.status_code == 200
    j = ok.json()
    assert j["ok"] and j["source"] == "memory" and j["storage_warning"]
    assert j["totals"]["downloads"] == 1 and j["errors"][0]["code"] == "URL_INVALID"
    assert j["youtube"]["breaker"]["open"] is False
    assert len(j["daily"]) == 7 and sum(j["hourly_ist"]) == 1
    assert "127.0.0.1" not in str(j["recent"])      # no IPs leak into the dashboard payload


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
