import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import ytdlp_opts as yo


def test_web_embedded_is_first_by_default(monkeypatch):
    monkeypatch.delenv("YTDLP_PLAYER_CLIENTS", raising=False)
    clients = yo.player_clients()
    assert clients[0] == "web_embedded"
    assert "default" in clients and "tv" in clients


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("YTDLP_PLAYER_CLIENTS", "tv,mweb")
    assert yo.player_clients() == ["tv", "mweb"]


def test_failure_reason_classes():
    assert yo.failure_reason("Sign in to confirm you're not a bot") == "youtube_block"
    assert yo.failure_reason("ffmpeg not found") == "ffmpeg"
    assert yo.failure_reason("Requested format is not available") == "format"
    assert yo.failure_reason("[Errno 28] No space left on device") == "disk"
    assert yo.failure_reason("Unsupported URL: x") == "unsupported"
    assert yo.failure_reason("something odd") == "unknown"
    # never echoes the raw text
    assert "odd" not in yo.failure_reason("something odd")
