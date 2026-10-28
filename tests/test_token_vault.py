import pytest
import time
from backend.security.token_vault import token_vault

def test_token_issuance_allowed_domain():
    ok, res = token_vault.issue_token(origin="https://ovd.winplaybox.in", scope="subtitles:generate")
    assert ok is True
    assert "token" in res
    assert res["token"].startswith("wpb_")
    assert res["expires_in"] == 60
    assert "subtitles:generate" in res["scopes"]

def test_token_issuance_forbidden_domain():
    ok, res = token_vault.issue_token(origin="https://hacker-site.com", scope="subtitles:generate")
    assert ok is False
    assert res["error"] == "ForbiddenDomain"

def test_token_single_use_burn_and_replay_prevention():
    ok, res = token_vault.issue_token(origin="https://winplaybox.in", scope="audio:extract")
    assert ok is True
    token = res["token"]

    # 1. First usage must succeed
    authorized, reason, payload = token_vault.verify_and_burn_token(
        token=token,
        required_scope="audio:extract",
        request_origin="https://winplaybox.in"
    )
    assert authorized is True
    assert "Authorized and token burned" in reason
    assert payload is not None

    # 2. Second usage (Replay Attack) MUST FAIL
    authorized2, reason2, payload2 = token_vault.verify_and_burn_token(
        token=token,
        required_scope="audio:extract",
        request_origin="https://winplaybox.in"
    )
    assert authorized2 is False
    assert "already been consumed" in reason2
    assert payload2 is None

def test_token_scope_enforcement():
    ok, res = token_vault.issue_token(origin="https://pricewatch.winplaybox.in", scope="price:read")
    token = res["token"]

    # Attempt to use price:read token for video:master must be blocked
    authorized, reason, _ = token_vault.verify_and_burn_token(
        token=token,
        required_scope="video:master",
        request_origin="https://pricewatch.winplaybox.in"
    )
    assert authorized is False
    assert "lacks required scope" in reason
