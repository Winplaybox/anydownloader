import os
import sys
import unittest
from unittest.mock import SimpleNamespace, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.routes_temp_media import _authorized


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


if __name__ == "__main__":
    unittest.main()
