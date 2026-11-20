"""BYO key + language/model options. Run: python -m pytest backend/autoclip/tests -q"""
import asyncio
import json
import os

import pytest

from backend.autoclip.tests.test_autoclip import ORIGIN, client  # noqa: F401  (fixtures)
from backend.autoclip import brain, byo, config, models, store

KEY = "AIzaSy" + "A" * 33
WORDS = [{"w": w, "s": i * 0.4, "e": i * 0.4 + 0.35} for i, w in enumerate(("This is a long enough sentence. " * 30).split())]


def test_build_validates():
    assert byo.build("", "") is None
    assert byo.build("gemini", KEY).provider == "gemini"
    for bad in (("nope", KEY), ("gemini", "short"), ("gemini", "has space " * 4), ("gemini", KEY + "\n$(x)")):
        with pytest.raises(byo.KeyError_):
            byo.build(*bad)
    with pytest.raises(byo.KeyError_):
        byo.build("gemini", KEY, "bad model!")


def test_key_never_in_repr():
    ai = byo.build("openai", "sk-" + "x" * 40)
    assert "x" * 10 not in repr(ai) and "x" * 10 not in str(ai) and "x" * 10 not in json.dumps(ai.public())


def test_vault_roundtrip():
    ai = byo.build("groq", "gsk_" + "k" * 40)
    byo.put("j1", ai)
    assert byo.get("j1") is ai
    byo.drop("j1")
    assert byo.get("j1") is None


def test_brain_no_key_uses_loudness_and_never_calls_server_ai(monkeypatch):
    async def boom(*a, **k):
        raise AssertionError("server AI must not be used without a key")
    monkeypatch.setattr(brain.llm_router, "complete_json", boom)
    st = config.clean_settings({"max_clips": 2})
    picks, eng = asyncio.run(brain.find_clips(WORDS, [], 240.0, st, ai=None, allow_server_ai=False))
    assert eng["reason"] == "no_ai_key" and picks


def test_brain_uses_user_ai():
    class Fake:
        provider, used_model = "gemini", "gemini-2.5-flash"
        async def complete_json(self, *a, **k):
            return {"clips": [{"start": 10, "end": 40, "score": 80, "hook": "Wait what", "title": "T"}]}
        def public(self):
            return {"provider": "gemini", "model": "m", "calls": 1, "input_tokens": 5, "output_tokens": 5}
    st = config.clean_settings({"max_clips": 2})
    picks, eng = asyncio.run(brain.find_clips(WORDS, [], 240.0, st, ai=Fake()))
    assert eng["engine"] == "ai" and eng["byo"] is True and picks[0]["picked_by"] == "ai"


def test_create_job_keeps_key_out_of_db_and_response(client, monkeypatch):
    r = client.post("/api/autoclip/jobs", headers=ORIGIN,
                    json={"url": "https://youtu.be/abc", "ai_provider": "gemini", "ai_key": KEY})
    assert r.status_code == 201, r.text
    assert KEY not in r.text
    jid = r.json()["job"]["id"]
    assert byo.get(jid) is not None
    raw_db = open(config.DB_PATH, "rb").read()
    assert KEY.encode() not in raw_db
    byo.drop(jid)


def test_create_job_rejects_bad_key(client):
    r = client.post("/api/autoclip/jobs", headers=ORIGIN,
                    json={"url": "https://youtu.be/abc", "ai_provider": "gemini", "ai_key": "x"})
    assert r.status_code == 400 and r.json()["code"] == "BadKey"


def test_key_test_endpoint(client, monkeypatch):
    async def ok(ai):
        return {"ok": True, "provider": ai.provider, "model": "m", "ms": 5}
    monkeypatch.setattr(byo, "test", ok)
    r = client.post("/api/autoclip/keys/test", headers=ORIGIN, json={"provider": "gemini", "key": KEY})
    assert r.status_code == 200 and KEY not in r.text
    assert client.post("/api/autoclip/keys/test", json={"provider": "gemini", "key": KEY}).status_code == 403

    async def bad(ai):
        raise byo.LLMError("Google Gemini rejected the API key.")
    monkeypatch.setattr(byo, "test", bad)
    r = client.post("/api/autoclip/keys/test", headers=ORIGIN, json={"provider": "gemini", "key": KEY})
    assert r.status_code == 422 and KEY not in r.text


def test_languages_and_models_listed(client):
    o = client.get("/api/autoclip/options").json()
    assert len(o["languages"]) >= 40 and {m["id"] for m in o["stt_models"]} == {"tiny", "base", "small"}
    assert config.clean_settings({"stt_model": "large-v3"})["stt_model"] == "auto"
    m = client.get("/api/autoclip/models").json()
    assert m["ok"] and len(m["models"]) == 3


def test_model_install_allowlist(client):
    r = client.post("/api/autoclip/models/install", headers=ORIGIN, json={"id": "../../etc"})
    assert r.status_code == 400
    assert client.post("/api/autoclip/models/install", json={"id": "tiny"}).status_code == 403
    assert models.installed("../x") is False
