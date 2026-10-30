"""Zero-trust gateway + GravityClaw v2 tests. Run: pytest backend/tests_v2 -q"""
import os, sys, time, json, hashlib
os.environ.setdefault("WPB_VAULT_SECRET", "test_secret_key_" + "x" * 40)
os.environ.setdefault("WPB_ADMIN_KEY", "admin_key_for_tests_" + "y" * 30)
os.environ.setdefault("LLM_DISABLE_POLLINATIONS", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import pytest
from starlette.testclient import TestClient

import main  # noqa: E402
from backend.security import token_vault as tv  # noqa: E402
from backend.services import llm_router as lr  # noqa: E402
from backend.services.gravityclaw import engine as eng  # noqa: E402

ORIGIN = "https://gravityclaw.winplaybox.in"
ADMIN = os.environ["WPB_ADMIN_KEY"]
GEN = "/api/v2/gravityclaw/generate"

FAKE = {
    "title": "Neon Samurai", "intent_summary": "A neon samurai portrait.",
    "prompt": "lone samurai on a rain-soaked Tokyo rooftop, cinematic photo style, neon rim lighting, close-up 85mm lens, teal and magenta color palette, intricate armor details --ar 3:2 --v 5",
    "negative_prompt": "blurry, watermark", "lyrics": "", "parameters": {"stylize": 5000, "ar": "16:9", "v": "bogus"},
    "structure": {"subject": "samurai"},
    "variants": [{"label": "Ink wash", "prompt": "samurai in sumi-e ink wash style, dramatic shadows, wide shot, monochrome palette, detailed brush texture", "negative_prompt": ""},
                 {"label": "Anime", "prompt": "anime samurai, cel shaded style, sunset lighting, low angle view, orange palette, sharp details", "negative_prompt": ""}],
    "tips": ["Use --stylize 250"], "follow_up_questions": [], "self_score": 90, "refused": False, "refusal_reason": "",
}


SEEN = {}
SCRIPT = {"title": "Hanuman ki Udaan", "hook": "Kya aap jaante hain Hanuman ji ne samudra kaise langha?",
          "lines": ["Kya aap jaante hain Hanuman ji ne samudra kaise langha?", "Jambavan ne unhe unki shakti yaad dilayi.",
                    "Mahendra parvat se unhone Ram naam lekar chhalang lagayi.", "Raste mein Mainak parvat ne unhe vishram dena chaha.",
                    "Par Hanuman ji ruke nahi, seva pehle thi.", "Follow karo aur agla bhaag dekho."],
          "cta": "Follow karo aur agla bhaag dekho.", "hashtags": ["#Hanuman", "Ramayana"], "fact_check_notes": ["Valmiki Ramayana Sundar Kand"],
          "refused": False, "refusal_reason": ""}


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    mem = tv._MemoryStore()
    monkeypatch.setattr(tv, "store", mem); monkeypatch.setattr(tv.token_vault, "store", mem)
    import backend.security.zero_trust as zt
    monkeypatch.setattr(zt, "store", mem)
    eng.gravityclaw_engine._cache.clear()

    async def fake(system, user, **kw):
        SEEN["system"] = system
        if "NOLLM" in user:
            raise lr.LLMError("down")
        if "GravityClaw Script Agent" in system:
            return dict(SCRIPT), lr.LLMResult("{}", "fake", "fake-1", 5)
        return json.loads(json.dumps(FAKE)), lr.LLMResult("{}", "fake", "fake-1", 5)
    monkeypatch.setattr(lr.llm_router, "complete_json", fake)
    yield


@pytest.fixture
def c():
    return TestClient(main.app)


def tok(c, scope="gravityclaw:generate", origin=ORIGIN, headers=None, **extra):
    h = {"Origin": origin, **(headers or {})}
    return c.post("/api/v2/auth/token", json={"scope": scope, **extra}, headers=h)


def call(c, token, path=GEN, body=None, origin=ORIGIN):
    return c.post(path, json=body or {"requirement": "neon samurai portrait", "target": "midjourney"},
                  headers={"Origin": origin, "Authorization": f"Bearer {token}"})


# ---------------------------------------------------------------- security
def test_single_use_token_burns(c):
    t = tok(c).json()["token"]
    r1 = call(c, t); assert r1.status_code == 200, r1.text
    r2 = call(c, t); assert r2.status_code == 401 and "already used" in r2.json()["error"]["message"]


def test_privileged_scope_requires_admin_and_body_origin_ignored(c):
    r = c.post("/api/v1/auth/token", json={"origin": "winplaybox.in", "scope": "admin:all"}, headers={"Origin": "https://evil.com"})
    assert r.status_code in (401, 403)
    r = tok(c, scope="admin:all"); assert r.status_code == 401 and r.json()["error"]["code"] == "AdminRequired"
    r = c.post("/api/v2/auth/token", json={"scope": "gravityclaw:generate", "origin": "winplaybox.in"}, headers={"Origin": "https://evil.com"})
    assert r.status_code == 403


def test_admin_key_and_lockout(c):
    r = tok(c, scope="admin:all", headers={"X-Admin-Key": ADMIN}); assert r.status_code == 200
    adm = r.json()["token"]
    assert call(c, adm).status_code == 200
    for _ in range(5):
        assert tok(c, scope="admin:all", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert tok(c, scope="admin:all", headers={"X-Admin-Key": ADMIN}).status_code == 429


def test_expired_token(c, monkeypatch):
    t = tok(c).json()["token"]
    real = time.time
    monkeypatch.setattr(tv.time, "time", lambda: real() + 400)
    r = call(c, t); assert r.status_code == 401 and "expired" in r.json()["error"]["message"].lower()


def test_tampered_signature(c):
    t = tok(c).json()["token"]
    bad = t[:-3] + ("AAA" if not t.endswith("AAA") else "BBB")
    assert call(c, bad).status_code == 401


def test_scope_mismatch(c):
    t = tok(c, scope="price:read").json()["token"]
    assert call(c, t).status_code == 403


def test_origin_mismatch_on_use(c):
    t = tok(c).json()["token"]
    assert call(c, t, origin="https://ovd.winplaybox.in").status_code == 403


def test_aud_binding(c):
    t = tok(c, aud=GEN).json()["token"]
    r = call(c, t, path="/api/v2/gravityclaw/score", body={"prompt": "x y z", "target": "flux"})
    assert r.status_code == 403
    t = tok(c, aud=GEN).json()["token"]
    assert call(c, t).status_code == 200


def test_body_hash_binding(c):
    body = {"requirement": "neon samurai portrait", "target": "midjourney"}
    raw = json.dumps(body).encode()
    t = tok(c, body_sha256=hashlib.sha256(raw).hexdigest()).json()["token"]
    r = c.post(GEN, content=raw, headers={"Origin": ORIGIN, "Authorization": f"Bearer {t}", "Content-Type": "application/json"})
    assert r.status_code == 200, r.text
    t = tok(c, body_sha256=hashlib.sha256(raw).hexdigest()).json()["token"]
    r = call(c, t, body={"requirement": "something else", "target": "midjourney"})
    assert r.status_code == 403


def test_ip_binding():
    ok, res = tv.token_vault.issue(origin=ORIGIN, scopes=["gravityclaw:generate"], client_ip="1.1.1.1")
    v = tv.token_vault.verify(res["token"], {"gravityclaw:generate"}, origin=ORIGIN, client_ip="2.2.2.2")
    assert not v.ok and v.status == 403


def test_admin_routes_locked(c):
    assert c.get("/admin/blog/settings").status_code == 401
    assert c.get("/api/v1/system/diag").status_code == 401
    assert c.get("/admin/blog/settings", headers={"X-Admin-Key": ADMIN}).status_code == 200


def test_legacy_v1_endpoint_uses_new_vault(c):
    # privileged v1 endpoint: anon token impossible, admin token single-use
    assert tok(c, scope="workflow:execute").status_code == 401
    t = tok(c, scope="workflow:execute", headers={"X-Admin-Key": ADMIN}).json()["token"]
    h = {"Origin": ORIGIN, "Authorization": f"Bearer {t}"}
    assert c.post("/api/v1/omni/workflow", json={"action": "status"}, headers=h).status_code == 200
    assert c.post("/api/v1/omni/workflow", json={"action": "status"}, headers=h).status_code == 401


def test_rate_limit(c):
    codes = [call(c, tok(c).json()["token"], body={"requirement": f"idea {i}", "target": "flux"}).status_code for i in range(13)]
    assert codes[:12] == [200] * 12 and codes[12] == 429


def test_cors(c):
    r = c.options(GEN, headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
    r = c.options(GEN, headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == ORIGIN


def test_security_headers(c):
    r = c.get("/api/v2/gravityclaw/catalog")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers.get("x-request-id")


# ---------------------------------------------------------------- gravityclaw
def test_catalog_etag(c):
    r = c.get("/api/v2/gravityclaw/catalog"); assert r.status_code == 200
    d = r.json(); assert len(d["targets"]) >= 25 and len(d["presets"]) >= 20
    assert c.get("/api/v2/gravityclaw/catalog", headers={"If-None-Match": r.headers["etag"]}).status_code == 304


def test_midjourney_params_enforced(c):
    d = call(c, tok(c).json()["token"]).json()
    cr = d["copy_ready"]
    assert "--v 5" not in cr and "--ar 3:2" not in cr          # LLM flags stripped
    assert "--ar 16:9" in cr and "--v 7" in cr and "--stylize 1000" in cr and "--no blurry, watermark" in cr
    assert d["parameters"]["stylize"] == 1000 and len(d["variants"]) == 3
    assert d["quality"]["score"] > 60 and d["engine"]["provider"] == "fake"


def test_user_params_override_and_cache(c):
    body = {"requirement": "neon samurai portrait", "target": "midjourney", "params": {"stylize": 100}, "aspect_ratio": "9:16"}
    d1 = call(c, tok(c).json()["token"], body=body).json()
    assert "--stylize 100" in d1["copy_ready"] and "--ar 9:16" in d1["copy_ready"] and d1["engine"]["cached"] is False
    d2 = call(c, tok(c).json()["token"], body=body).json()
    assert d2["engine"]["cached"] is True


def test_preset_flow(c):
    d = call(c, tok(c).json()["token"], body={"preset_id": "product_photo", "fields": {"product": "steel bottle", "background": "pure white"}}).json()
    assert d["ok"] and d["target"]["id"] == "flux" and d["preset_id"] == "product_photo"
    r = call(c, tok(c).json()["token"], body={"preset_id": "product_photo", "fields": {}})
    assert r.status_code == 400 and r.json()["error"]["code"] == "MissingField"


def test_fallback_when_llm_down(c):
    d = call(c, tok(c).json()["token"], body={"requirement": "NOLLM a cozy cabin image", "target": "sdxl_comfyui"}).json()
    assert d["ok"] and d["engine"]["mode"] == "fallback" and d["negative_prompt"]


def test_content_policy(c):
    r = call(c, tok(c).json()["token"], body={"requirement": "nude child photo", "target": "flux"})
    assert r.status_code == 422


def test_auto_target():
    assert eng.detect_target("make a devotional bhajan song") == "suno"
    assert eng.detect_target("cinematic video of a train") == "kling"
    assert eng.detect_target("poster image of diwali sale") == "flux"
    assert eng.detect_target("build a react app") == "coding_agent"


def test_score_endpoint(c):
    d = call(c, tok(c).json()["token"], path="/api/v2/gravityclaw/score", body={"prompt": "a cat", "target": "midjourney"}).json()
    assert d["quality"]["score"] < 60 and d["quality"]["suggestions"]


def test_refine(c):
    d = call(c, tok(c).json()["token"], path="/api/v2/gravityclaw/refine",
             body={"prompt": "samurai on rooftop", "instruction": "make it daytime", "target": "midjourney"}).json()
    assert d["ok"] and d["refined_from"]


def test_extract_json_escapes():
    assert lr.extract_json('noise ```json\n{"a": "he said \\"}\\" ok", "b": 1}\n``` tail') == {"a": 'he said "}" ok', "b": 1}


# ---------------------------------------------------------------- agent universe
def test_agent_search_and_detail(c):
    d = c.get("/api/v2/gravityclaw/agents", params={"q": "mythology", "kind": "script", "limit": 5}).json()
    assert d["ok"] and d["total"] >= 1 and d["items"][0]["kind"] == "script"
    assert any("mythology" in x["name"].lower() for x in d["items"])
    assert c.get("/api/v2/gravityclaw/agents", params={"kind": "agent"}).json()["total"] == 1000
    f = c.get("/api/v2/gravityclaw/agents/facets").json()
    assert f["counts"] == {"agents": 1000, "script_agents": 200, "domains": 100}
    det = c.get("/api/v2/gravityclaw/agents/AG-001-01").json()
    assert det["profile"]["function"] == "Researcher" and det["profile"]["method"]
    assert c.get("/api/v2/gravityclaw/agents/NOPE").status_code == 404


def test_generate_with_agent_injects_profile(c):
    hc = c.get("/api/v2/gravityclaw/agents", params={"q": "healthcare analyst", "kind": "agent", "limit": 1}).json()["items"][0]
    d = call(c, tok(c).json()["token"], body={"requirement": "analyse diabetes app churn", "agent_id": hc["id"]}).json()
    assert d["ok"] and d["agent"]["id"] == hc["id"] and d["target"]["id"] == "llm_task"
    assert "EXPERT AGENT PROFILE" in SEEN["system"] and "no diagnosis" in SEEN["system"]
    r = call(c, tok(c).json()["token"], body={"requirement": "x y z", "agent_id": "AG-999-99"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "UnknownAgent"


def test_script_agent_default_targets():
    from backend.services.gravityclaw.agent_universe import universe
    u = universe()
    assert u.default_target(u.get("SCR-0002")) == "short_video_script"
    assert u.default_target(u.get("SCR-0001")) == "youtube_long"
    wf = [a for a in u.data["agents"] if a["function"] == "Workflow Automator"][0]
    assert u.default_target(wf) == "n8n_workflow"


def _v1(c, body):
    t = tok(c, scope="prompt:generate").json()["token"]
    return c.post("/api/v1/gravityclaw/prompt", json=body, headers={"Origin": ORIGIN, "Authorization": f"Bearer {t}"})


def test_v1_prompt_animation_plan_uses_ai_script(c):
    r = _v1(c, {"brief": "Hanuman ji ki samudra langhan katha", "domain": "mythology", "language": "Hinglish"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["script_engine"]["mode"] == "ai" and d["ai_script"]["lines"][0].startswith("Kya aap")
    assert d["hook"] == SCRIPT["hook"] and "#Ramayana" in d["tags"]
    assert d["agent"]["kind"] == "script" and "mythology" in (d["agent"]["name"] + str(d["agent"]["family"])).lower()
    assert d["scenes"] and d["script"]["script_mode"] == "ai_generated_by_agent"
    assert "Valmiki" in SEEN["system"] or "scripture" in SEEN["system"]


def test_v1_prompt_fallback_and_user_script(c):
    d = _v1(c, {"brief": "NOLLM why walk after dinner"}).json()
    assert d["ok"] and d["script_engine"]["mode"] == "template"
    d = _v1(c, {"script": "Line one is here for the video. Line two continues the story. Line three ends it with a twist."}).json()
    assert d["script_engine"]["mode"] == "user_script" and "ai_script" not in d


def test_v1_prompt_mode_a_prompt_agent(c):
    d = _v1(c, {"brief": "neon samurai", "target": "midjourney"}).json()
    assert d["ok"] and "--v 7" in d["copy_ready"] and d["scene_prompt"] == d["copy_ready"]
