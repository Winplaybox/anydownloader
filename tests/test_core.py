import sys
import os
os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_tests_" + "z" * 30)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import time
from backend.utils.url_normalizer import normalize_url
from backend.utils.errors import AppError, ErrorCode, get_error_message
from backend.utils.security import (
    sign_download_token,
    verify_download_token,
    is_safe_cdn_host,
    is_ip_allowed
)

class TestCoreContracts(unittest.TestCase):
    def test_normalizer_twitter(self):
        res = normalize_url("https://x.com/u/status/123456789", resolve_redirects=False)
        self.assertEqual(res["platform"], "twitter")
        self.assertEqual(res["url"], "https://x.com/i/status/123456789")

    def test_normalizer_empty(self):
        with self.assertRaises(AppError) as ctx:
            normalize_url("")
        self.assertEqual(ctx.exception.code, ErrorCode.URL_MISSING)
        self.assertEqual(get_error_message(ctx.exception.code), "Paste a link to get started.")

    def test_normalizer_invalid(self):
        with self.assertRaises(AppError) as ctx:
            normalize_url("random text without domain")
        self.assertEqual(ctx.exception.code, ErrorCode.URL_INVALID)
        self.assertEqual(get_error_message(ctx.exception.code), "That doesn't look like a valid link.")

    def test_normalizer_unsupported(self):
        with self.assertRaises(AppError) as ctx:
            normalize_url("https://example.com/item")
        self.assertEqual(ctx.exception.code, ErrorCode.PLATFORM_UNSUPPORTED)

    def test_security_cdn(self):
        self.assertTrue(is_safe_cdn_host("video.twimg.com"))
        self.assertFalse(is_safe_cdn_host("attacker.internal"))

    def test_security_ip(self):
        self.assertFalse(is_ip_allowed("127.0.0.1"))
        self.assertFalse(is_ip_allowed("169.254.169.254"))

    def test_token_lifecycle(self):
        url = "https://video.twimg.com/media/clip.mp4"
        tok = sign_download_token(url, "clip.mp4", ttl_seconds=60)
        verified = verify_download_token(tok)
        self.assertIsNotNone(verified)
        self.assertEqual(verified["variant_url"], url)

    def test_token_tampering_rejected(self):
        url = "https://video.twimg.com/media/clip.mp4"
        token = sign_download_token(url, "clip.mp4", ttl_seconds=60)
        payload, signature = token.split(".", 1)
        tampered = payload[:-1] + ("A" if payload[-1] != "A" else "B") + "." + signature
        self.assertIsNone(verify_download_token(tampered))

    def test_unsigned_payload_rejected(self):
        import base64
        import json
        payload = base64.urlsafe_b64encode(json.dumps({"u": "https://video.twimg.com/media/clip.mp4", "exp": int(time.time()) + 60}).encode()).decode().rstrip("=")
        self.assertIsNone(verify_download_token(payload))

    def test_expired_token_rejected(self):
        url = "https://video.twimg.com/media/clip.mp4"
        token = sign_download_token(url, "clip.mp4", ttl_seconds=-1)
        self.assertIsNone(verify_download_token(token))

if __name__ == "__main__":
    unittest.main()
