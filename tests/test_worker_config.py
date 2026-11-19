import unittest
from unittest.mock import patch

from backend.utils.worker_config import get_worker_config, worker_headers


class TestWorkerConfig(unittest.TestCase):
    def test_missing_secret_disables_worker(self):
        with patch.dict("os.environ", {"WORKER_URL": "https://worker.example.com", "WORKER_SECRET": "", "WORKER_KEY": ""}, clear=False):
            self.assertIsNone(get_worker_config())

    def test_https_worker_uses_configured_secret(self):
        with patch.dict("os.environ", {"WORKER_URL": "https://worker.example.com/", "WORKER_SECRET": "configured-secret", "WORKER_KEY": ""}, clear=False):
            self.assertEqual(get_worker_config(), ("https://worker.example.com", "configured-secret"))

    def test_http_worker_is_rejected(self):
        with patch.dict("os.environ", {"WORKER_URL": "http://worker.example.com", "WORKER_SECRET": "configured-secret"}, clear=False):
            self.assertIsNone(get_worker_config())

    def test_headers_use_only_supplied_secret(self):
        self.assertEqual(worker_headers("secret")["X-Worker-Key"], "secret")
        self.assertEqual(worker_headers("secret")["Authorization"], "Bearer secret")


if __name__ == "__main__":
    unittest.main()
