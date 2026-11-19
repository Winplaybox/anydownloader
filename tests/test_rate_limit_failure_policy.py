import os
import unittest
from unittest.mock import patch

from backend.security import zero_trust


class BrokenStore:
    def incr(self, key, ttl):
        raise RuntimeError("store unavailable")


class TestRateLimitStoreFailurePolicy(unittest.TestCase):
    def setUp(self):
        self.original_store = zero_trust.store
        zero_trust.store = BrokenStore()



    def tearDown(self):
        zero_trust.store = self.original_store


    def test_production_defaults_fail_closed(self):
        with patch.object(zero_trust, "IS_PRODUCTION", True), patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WPB_RATE_LIMIT_FAIL_OPEN", None)
            allowed, remaining = zero_trust.rate_limit("test", "ip", 10, 60)
            self.assertFalse(allowed)
            self.assertEqual(remaining, 0)


    def test_explicit_fail_open_override(self):
        with patch.object(zero_trust, "IS_PRODUCTION", True), patch.dict(os.environ, {"WPB_RATE_LIMIT_FAIL_OPEN": "1"}, clear=False):
            allowed, remaining = zero_trust.rate_limit("test", "ip", 10, 60)
            self.assertTrue(allowed)
            self.assertEqual(remaining, 10)


    def test_development_defaults_fail_open(self):
        with patch.object(zero_trust, "IS_PRODUCTION", False), patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WPB_RATE_LIMIT_FAIL_OPEN", None)
            allowed, remaining = zero_trust.rate_limit("test", "ip", 10, 60)
            self.assertTrue(allowed)
            self.assertEqual(remaining, 10)


if __name__ == "__main__":
    unittest.main()
