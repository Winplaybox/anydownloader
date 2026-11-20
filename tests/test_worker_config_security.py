"""Regression tests for optional remote-worker configuration validation."""
import os
from unittest.mock import patch

from backend.utils.worker_config import get_worker_config, worker_headers


def test_worker_config_missing_secret_disables_worker():
    with patch.dict(os.environ, {"WORKER_URL": "https://worker.example.com", "WORKER_SECRET": ""}, clear=False):
        assert get_worker_config() is None


def test_worker_config_accepts_https_and_secret():
    with patch.dict(os.environ, {"WORKER_URL": "https://worker.example.com", "WORKER_SECRET": "secret"}, clear=False):
        assert get_worker_config() == ("https://worker.example.com", "secret")


def test_worker_config_rejects_http():
    with patch.dict(os.environ, {"WORKER_URL": "http://worker.example.com", "WORKER_SECRET": "secret"}, clear=False):
        assert get_worker_config() is None


def test_worker_config_rejects_credentials():
    with patch.dict(os.environ, {"WORKER_URL": "https://user:pass@worker.example.com", "WORKER_SECRET": "secret"}, clear=False):
        assert get_worker_config() is None


def test_worker_config_rejects_query_and_fragment():
    for url in ("https://worker.example.com?x=1", "https://worker.example.com/#frag"):
        with patch.dict(os.environ, {"WORKER_URL": url, "WORKER_SECRET": "secret"}, clear=False):
            assert get_worker_config() is None


def test_worker_config_rejects_invalid_port():
    with patch.dict(os.environ, {"WORKER_URL": "https://worker.example.com:99999", "WORKER_SECRET": "secret"}, clear=False):
        assert get_worker_config() is None


def test_worker_headers_send_shared_secret():
    headers = worker_headers("test-secret")
    assert headers["X-Worker-Key"] == "test-secret"
    assert headers["Authorization"] == "Bearer test-secret"
