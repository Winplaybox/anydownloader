"""AutoClip unit + API tests. Run: python -m pytest backend/autoclip/tests -q"""
import os
import sys
import tempfile
import time

_TMP = tempfile.mkdtemp(prefix="autoclip_test_")
os.environ["AUTOCLIP_DATA_DIR"] = _TMP
os.environ["AUTOCLIP_WORKER_MODE"] = "remote"          # no inline worker during API tests
os.environ["AUTOCLIP_WORKER_KEY"] = "w" * 40
os.environ["AUTOCLIP_SECRET"] = "s" * 40
os.environ["AUTOCLIP_DAILY_LIMIT"] = "2"
os.environ["AUTOCLIP_LEASE_SECONDS"] = "60"
os.environ.setdefault("WPB_RATE_LIMIT_FAIL_OPEN", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import pytest  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from backend.autoclip import brain, config, media, store  # noqa: E402
from backend.routes_autoclip import routes_autoclip  # noqa: E402

ORIGIN = {"Origin": "https://winplaybox.github.io"}
WKEY = {"X-Worker-Key": "w" * 40}


def _words(text, start=0.0, step=0.4):
    out, t = [], start
    for w in text.split():
        out.append({"w": w, "s": round(t, 2), "e": round(t + step * 0.9, 2)})
        t += step
    return out


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    """Config is read at import; other test modules may import it first with other env. Pin it here."""
    monkeypatch.setattr(config, "DATA_DIR", _TMP)
    monkeypatch.setattr(config, "DB_PATH", os.path.join(_TMP, "autoclip.db"))
    monkeypatch.setattr(config, "WORKER_KEY", "w" * 40)
    monkeypatch.setattr(config, "WORKER_MODE", "remote")
    monkeypatch.setattr(config, "SECRET", "s" * 40)
    monkeypatch.setattr(config, "DAILY_LIMIT", 2)
    monkeypatch.setattr(config, "LEASE_SECONDS", 60)
    monkeypatch.setattr(config, "MAX_QUEUED", 1000)
    yield


@pytest.fixture()
def client():
    import uuid
    # fresh client IP per test so rate-limit buckets don't leak between tests
    return TestClient(Starlette(routes=routes_autoclip), client=(f"10.9.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}", 5000))


# --------------------------------------------------------------------------- #
# settings / links
# --------------------------------------------------------------------------- #

def test_clean_settings_clamps_and_defaults():
    s = config.clean_settings({"max_clips": 99, "min_len": 2, "max_len": 1000, "caption_style": "x",
                               "layout": "face", "accent": "red", "resolution": "720p", "focus": "a" * 999})
    assert s["max_clips"] == 12 and s["min_len"] == 8 and s["max_len"] == 180
    assert s["caption_style"] == "pop" and s["layout"] == "face" and s["accent"] == "#FFE500"
    assert s["resolution"] == 720 and len(s["focus"]) == 300


@pytest.mark.parametrize("url", ["http://127.0.0.1/x", "file:///etc/passwd", "https://evil.com/v.mp4",
                                 "https://user:pw@youtube.com/watch?v=1", "https://youtube.com:8080/x",
                                 "https://notyoutube.com/watch"])
def test_check_url_rejects(url):
    with pytest.raises(media.SourceError):
        media.check_url(url)


def test_check_url_accepts_subdomains():
    assert media.check_url("https://www.youtube.com/watch?v=abc#t=3").startswith("https://www.youtube.com/watch")
    assert media.check_url("https://youtu.be/abc")


def test_origin_rules():
    assert config.origin_allowed("https://winplaybox.github.io")
    assert config.origin_allowed("https://clip.winplaybox.in")
    assert not config.origin_allowed("https://winplaybox.in.evil.com")
    assert not config.origin_allowed("https://evil.github.io")


# --------------------------------------------------------------------------- #
# brain
# --------------------------------------------------------------------------- #

def test_snap_moves_to_sentence_bounds():
    words = _words("Intro words here. This is the setup of the story and it goes on. Then the payoff lands hard. "
                   "More talk after that keeps going on and on.")
    se = brain.snap(5.0, 9.0, words, min_len=3, max_len=20, duration=60)
    assert se
    s, e = se
    first = next(w for w in words if abs(w["s"] - (s + 0.12)) < 0.02)
    assert first["w"] == "This"
    assert any(abs(w["e"] - (e - 0.35)) < 0.02 and w["w"].endswith(".") for w in words)


def test_dedupe_keeps_best_non_overlapping():
    clips = [{"start": 0, "end": 30, "score": 60}, {"start": 2, "end": 31, "score": 90},
             {"start": 40, "end": 70, "score": 70}]
    out = brain.dedupe(clips, 5)
    assert [c["score"] for c in out] == [90, 70]


def test_fallback_without_ai_returns_valid_clips():
    words = _words(" ".join(f"word{i}." if i % 12 == 11 else f"word{i}" for i in range(400)))
    z = [0.0] * 170
    for t in range(100, 120):
        z[t] = 3.0
    st = config.clean_settings({"max_clips": 3, "min_len": 15, "max_len": 40})
    out = brain.fallback(words, z, 165.0, st)
    assert out and len(out) <= 3
    assert all(14 <= c["end"] - c["start"] <= 41 for c in out)
    assert any(c["start"] <= 110 <= c["end"] for c in out)   # the loud part is chosen


def test_find_clips_uses_ai_and_validates(monkeypatch):
    import asyncio

    words = _words(" ".join(f"w{i}." if i % 8 == 7 else f"w{i}" for i in range(300)))

    class R:
        provider, model = "gemini", "test"

    async def fake(system, user, **kw):
        return {"clips": [{"start": 10, "end": 40, "score": 120, "hook": "a b c d e f g h i", "title": "T",
                           "hashtags": "#one, two"}, {"start": "bad", "end": None}]}, R()

    monkeypatch.setattr(brain.llm_router, "complete_json", fake)
    clips, info = asyncio.run(brain.find_clips(words, [], 120.0,
                                               config.clean_settings({"min_len": 15, "max_len": 45}),
                                               allow_server_ai=True))
    assert info["engine"] == "ai" and len(clips) == 1
    c = clips[0]
    assert c["score"] == 100 and len(c["hook"].split()) <= 7 and c["hashtags"] == ["one", "two"]


# --------------------------------------------------------------------------- #
# store: lease + fencing
# --------------------------------------------------------------------------- #

def test_lease_fencing_and_requeue():
    j = store.create(source_kind="url", source_url="https://youtu.be/x", source_name=None,
                     settings=config.clean_settings({}), client="c")
    # drain anything older from other tests
    got = store.claim("A")
    while got and got["id"] != j["id"]:
        store.fail(got["id"], "A", "x")
        got = store.claim("A")
    assert got["status"] == "running"
    assert store.heartbeat(j["id"], "B")["ok"] is False          # other worker is fenced
    assert store.complete(j["id"], "B", {"clips": []}) is False
    # expire lease -> requeue -> new owner
    with store._conn() as c:
        c.execute("UPDATE jobs SET lease_until=? WHERE id=?", (time.time() - 1, j["id"]))
    got2 = store.claim("B")
    assert got2["id"] == j["id"] and got2["attempts"] == 2
    assert store.heartbeat(j["id"], "A")["ok"] is False          # stale worker lost it
    assert store.complete(j["id"], "B", {"clips": [1]}) is True
    assert store.get(j["id"])["status"] == "done"


def test_uploading_jobs_are_not_claimed():
    j = store.create(source_kind="upload", source_url=None, source_name="a.mp4", settings={}, client="c",
                     status="uploading")
    got = store.claim("Z")
    assert not got or got["id"] != j["id"]
    if got:
        store.fail(got["id"], "Z", "x")
    store.mark_queued(j["id"])
    assert store.get(j["id"])["status"] == "queued"
    store.request_cancel(j["id"])
    assert store.get(j["id"])["status"] == "cancelled"


def test_tokens():
    j = store.create(source_kind="url", source_url="https://youtu.be/y", source_name=None, settings={}, client="c")
    store.request_cancel(j["id"])
    assert store.token_ok(j["id"], store.job_token(j["id"]))
    assert not store.token_ok(j["id"], "nope")
    assert not store.valid_artifact("../x.mp4") and store.valid_artifact("clip_01.mp4")


# --------------------------------------------------------------------------- #
# HTTP API
# --------------------------------------------------------------------------- #

def test_health_and_options(client):
    assert client.get("/api/autoclip/health").json()["service"] == "autoclip"
    o = client.get("/api/autoclip/options").json()
    assert o["ok"] and o["caption_styles"]


def test_create_requires_origin(client):
    r = client.post("/api/autoclip/jobs", json={"url": "https://youtu.be/abc"})
    assert r.status_code == 403


def test_create_url_job_and_poll_and_daily_limit(client):
    r = client.post("/api/autoclip/jobs", json={"url": "https://youtu.be/abc", "settings": {"max_clips": 2}},
                    headers=ORIGIN)
    assert r.status_code == 201, r.text
    d = r.json()
    jid, tok = d["job"]["id"], d["token"]
    assert d["job"]["settings"]["max_clips"] == 2
    assert client.get(f"/api/autoclip/jobs/{jid}").status_code == 404           # no token
    assert client.get(f"/api/autoclip/jobs/{jid}", headers={"X-Job-Token": tok}).json()["job"]["status"] == "queued"
    assert client.post(f"/api/autoclip/jobs/{jid}/cancel", headers={"X-Job-Token": tok}).json()["job"]["status"] == "cancelled"
    assert client.post("/api/autoclip/jobs", json={"url": "https://youtu.be/b"}, headers=ORIGIN).status_code == 201
    r3 = client.post("/api/autoclip/jobs", json={"url": "https://youtu.be/c"}, headers=ORIGIN)
    assert r3.status_code == 429 and r3.json()["code"] == "DailyLimit"


def test_bad_link_rejected(client, monkeypatch):
    monkeypatch.setattr(config, "DAILY_LIMIT", 0)
    r = client.post("/api/autoclip/jobs", json={"url": "https://evil.example/v"}, headers=ORIGIN)
    assert r.status_code == 400 and r.json()["code"] == "BadLink"


def test_upload_job_and_full_remote_worker_flow(client, monkeypatch):
    monkeypatch.setattr(config, "DAILY_LIMIT", 0)
    # clear queue
    while (j := store.claim("cleanup")):
        store.fail(j["id"], "cleanup", "x")
    data = b"\x00" * 20000
    r = client.post("/api/autoclip/jobs", files={"file": ("talk.mp4", data, "video/mp4")},
                    data={"settings": '{"max_clips": 1}'}, headers=ORIGIN)
    assert r.status_code == 201, r.text
    jid, tok = r.json()["job"]["id"], r.json()["token"]
    assert r.json()["job"]["status"] == "queued"

    assert client.post("/api/autoclip/workers/claim", json={"worker_id": "w1"}).status_code == 401
    c = client.post("/api/autoclip/workers/claim", json={"worker_id": "w1"}, headers=WKEY)
    assert c.status_code == 200 and c.json()["job"]["id"] == jid and c.json()["job"]["source_ext"] == ".mp4"
    src = client.get(f"/api/autoclip/workers/jobs/{jid}/source", params={"worker_id": "w1"}, headers=WKEY)
    assert src.content == data
    assert client.get(f"/api/autoclip/workers/jobs/{jid}/source", params={"worker_id": "w2"}, headers=WKEY).status_code == 409
    hb = client.post(f"/api/autoclip/workers/jobs/{jid}/heartbeat", headers=WKEY,
                     json={"worker_id": "w1", "stage": "rendering", "progress": 70, "title": "Hello"})
    assert hb.json() == {"ok": True, "cancel": False}
    bad = client.post(f"/api/autoclip/workers/jobs/{jid}/artifact", params={"worker_id": "w1", "name": "../../x"},
                      headers=WKEY, content=b"x")
    assert bad.status_code == 400
    early = client.post(f"/api/autoclip/workers/jobs/{jid}/complete", headers=WKEY,
                        json={"worker_id": "w1", "result": {"clips": [{"files": {"video": "clip_01.mp4"}}]}})
    assert early.status_code == 409
    up = client.post(f"/api/autoclip/workers/jobs/{jid}/artifact", params={"worker_id": "w1", "name": "clip_01.mp4"},
                     headers=WKEY, content=b"MP4DATA" * 300)
    assert up.json()["ok"]
    done = client.post(f"/api/autoclip/workers/jobs/{jid}/complete", headers=WKEY, json={
        "worker_id": "w1", "result": {"title": "Hello", "duration": 10,
                                      "clips": [{"index": 1, "files": {"video": "clip_01.mp4"}}]}})
    assert done.json()["ok"]
    job = client.get(f"/api/autoclip/jobs/{jid}", headers={"X-Job-Token": tok}).json()["job"]
    assert job["status"] == "done" and job["progress"] == 100 and job["clips"][0]["index"] == 1
    f = client.get(f"/api/autoclip/jobs/{jid}/files/clip_01.mp4", params={"t": tok})
    assert f.status_code == 200 and f.content.startswith(b"MP4DATA")
    assert client.get(f"/api/autoclip/jobs/{jid}/files/clip_01.mp4").status_code == 404
    z = client.get(f"/api/autoclip/jobs/{jid}/zip", params={"t": tok})
    assert z.status_code == 200 and z.content[:2] == b"PK"
