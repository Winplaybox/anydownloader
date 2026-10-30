import pytest
from starlette.testclient import TestClient
from backend.main import app

def test_v1_voice_list():
    client = TestClient(app)
    res = client.get("/api/v1/voice/list")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert isinstance(data.get("voices"), list)
    assert len(data.get("voices")) >= 8

def test_v1_channels_list():
    client = TestClient(app)
    res = client.get("/api/v1/channels/list")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert isinstance(data.get("channels"), list)
    assert len(data.get("channels")) >= 6
    # Verify TigerVlogs exists
    names = [c["id"] for c in data["channels"]]
    assert "TigerVlogs-2026" in names

def test_v1_token_lifecycle_and_single_use_burn():
    client = TestClient(app)
    
    # 1. Unauthenticated request without token must fail with 401
    unauth_res = client.post("/api/v1/voice/synthesize", json={"text": "Hello"})
    assert unauth_res.status_code == 401
    assert unauth_res.json().get("ok") is False

    # 2. Issue single-use token for allowed domain with proper Origin header
    token_res = client.post("/api/v1/auth/token", json={
        "scope": "voice:tts"
    }, headers={"Origin": "https://winplaybox.in"})
    assert token_res.status_code == 200
    token = token_res.json().get("token")
    assert token.startswith("wpb")

    # 3. Call endpoint with token (1st time -> must succeed and burn token)
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://winplaybox.in"
    }
    call_1 = client.post("/api/v1/voice/synthesize", json={"text": "Testing voice synthesis"}, headers=auth_headers)
    assert call_1.status_code == 200
    assert call_1.json().get("ok") is True

    # 4. Replay attack with same burned token -> MUST BE BLOCKED WITH 401
    call_2 = client.post("/api/v1/voice/synthesize", json={"text": "Testing replay attack"}, headers=auth_headers)
    assert call_2.status_code == 401
    assert "already used" in call_2.json().get("reason", "").lower() or "already been consumed" in call_2.json().get("reason", "").lower()
