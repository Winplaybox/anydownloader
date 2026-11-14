import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_guard_and_analytics(monkeypatch):
    from backend.services import yt_guard, analytics
    yt_guard.success()
    analytics._MEM.clear()
    analytics._PENDING.clear()
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    yield
    yt_guard.success()
