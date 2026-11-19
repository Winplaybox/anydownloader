import os
import sys
import unittest
from unittest.mock import SimpleNamespace, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.routes_temp_media import _authorized, _public_base


class TestTempMediaAuthorization(unittest.TestCase):
    def request(self, headers=None):
        return SimpleNamespace(headers=headers or {})

    def test_missing_credentials_deny(self):
        with patch.dict(os.environ, {"AUTOMATION_API_KEY": "", "WORKER_KEY": "", "WORKER_SECRET": ""}, clear=False):
            self.assertFalse(_authorized(self.request()))

    def test_automation_api_key_authorizes(self):
        with patch.dict(os.environ, {"AUTOMATION_API_KEY": "automation-test-secret"}, clear=False):
            self.assertTrue(_authorized(self.request({"x-api-key": "automation-test-secret"})))

    def test_worker_key_authorizes(self):
        with patch.dict(os.environ, {"WORKER_KEY": "worker-test-secret"}, clear=False):
            self.assertTrue(_authorized(self.request({"x-worker-key": "worker-test-secret"})))

    def test_worker_secret_authorizes_compatibly(self):
        with patch.dict(os.environ, {"WORKER_SECRET": "worker-secret-compat"}, clear=False):
            self.assertTrue(_authorized(self.request({"authorization": "Bearer worker-secret-compat"})))

    def test_wrong_key_denies(self):
        with patch.dict(os.environ, {"AUTOMATION_API_KEY": "real-test-secret"}, clear=False):
            self.assertFalse(_authorized(self.request({"x-api-key": "wrong-key"})))

    def test_empty_configured_secrets_never_match_empty_header(self):
        with patch.dict(os.environ, {"AUTOMATION_API_KEY": "", "WORKER_KEY": "", "WORKER_SECRET": ""}, clear=False):
            self.assertFalse(_authorized(self.request({"x-api-key": ""})))


class TestPublicMediaUrl(unittest.TestCase):
    def test_configured_https_url_is_used(self):
        request = SimpleNamespace(headers={}, url=SimpleNamespace(scheme="http"))
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://media.example.com/"}, clear=False):
            self.assertEqual(_public_base(request), "https://media.example.com")

    def test_rejects_credentials_and_query(self):
        request = SimpleNamespace(headers={}, url=SimpleNamespace(scheme="http"))
        for value in ("https://user:pass@example.com", "https://example.com?x=1", "ftp://example.com"):
            with patch.dict(os.environ, {"PUBLIC_BASE_URL": value}, clear=False):
                with self.assertRaises(ValueError):
                    _public_base(request)

    def test_production_requires_https_and_configured_base(self):
        request = SimpleNamespace(headers={"host": "spoofed.example"}, url=SimpleNamespace(scheme="http"))
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "", "WPB_ENV": "production", "RENDER": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                _public_base(request)
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "http://media.example.com", "WPB_ENV": "production", "RENDER": ""}, clear=False):
            with self.assertRaises(ValueError):
                _public_base(request)

    def test_development_fallback_validates_host_and_ignores_forwarded_host(self):
        request = SimpleNamespace(headers={"host": "localhost:8000", "x-forwarded-host": "attacker.example"}, url=SimpleNamespace(scheme="http"))
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "", "WPB_ENV": "", "RENDER": ""}, clear=False):
            self.assertEqual(_public_base(request), "http://localhost:8000")
        request.headers["host"] = "attacker.example/path"
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "", "WPB_ENV": "", "RENDER": ""}, clear=False):
            with self.assertRaises(ValueError):
                _public_base(request)


if __name__ == "__main__":
    unittest.main()
