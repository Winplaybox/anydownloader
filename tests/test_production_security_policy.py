import os
import unittest
from unittest.mock import patch

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_policy_" + "z" * 32)

from backend.security import zero_trust
from backend.security import token_vault
from backend.utils import security


class BrokenStore:
    def incr(self, key, ttl):
        raise RuntimeError("store unavailable")

    def get(self, key):
        raise RuntimeError("store unavailable")


class TestProductionSecurityPolicies(unittest.TestCase):
    def test_studio_admin_routes_are_middleware_guarded(self):
        protected = "/api/v1/studio/admin/"
        self.assertIn(protected, zero_trust.ADMIN_ONLY_PATH_PREFIXES)
        for path in (
            "/api/v1/studio/admin/users",
            "/api/v1/studio/admin/activity",
            "/api/v1/studio/admin/settings",
            "/api/v1/studio/admin/platforms",
        ):
            self.assertTrue(path.startswith(zero_trust.ADMIN_ONLY_PATH_PREFIXES))

    def test_admin_lockout_fails_closed_in_production(self):
        original = zero_trust.store
        zero_trust.store = BrokenStore()
        try:
            with patch.object(zero_trust, "IS_PRODUCTION", True):
                self.assertTrue(zero_trust.admin_locked("203.0.113.10"))
        finally:
            zero_trust.store = original

    def test_admin_lockout_remains_available_in_development(self):
        original = zero_trust.store
        zero_trust.store = BrokenStore()
        try:
            with patch.object(zero_trust, "IS_PRODUCTION", False):
                self.assertFalse(zero_trust.admin_locked("203.0.113.10"))
        finally:
            zero_trust.store = original

    def test_production_requires_shared_token_store(self):
        with patch.object(token_vault, "IS_PRODUCTION", True), \
             patch.object(token_vault, "_RedisStore", side_effect=RuntimeError("no redis")), \
             patch.object(token_vault, "_UpstashStore", side_effect=RuntimeError("no upstash")), \
             patch.dict(os.environ, {"REDIS_URL": "", "UPSTASH_REDIS_REST_URL": "", "UPSTASH_REDIS_REST_TOKEN": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                token_vault._build_store()

    def test_dns_mixed_public_and_private_answers_are_rejected(self):
        public = ("93.184.216.34", 80)
        private = ("127.0.0.1", 80)
        records = [
            (2, 1, 6, "", (public[0], public[1])),
            (2, 1, 6, "", (private[0], private[1])),
        ]
        with patch.object(security.socket, "getaddrinfo", return_value=records):
            self.assertFalse(security.verify_public_dns_resolution("https://example.com/media.mp4"))

    def test_dns_public_answer_is_accepted(self):
        records = [(2, 1, 6, "", ("93.184.216.34", 443))]
        with patch.object(security.socket, "getaddrinfo", return_value=records):
            self.assertTrue(security.verify_public_dns_resolution("https://example.com/media.mp4"))


if __name__ == "__main__":
    unittest.main()
