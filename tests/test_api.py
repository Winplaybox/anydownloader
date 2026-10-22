import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from backend.main import app
from backend.utils.security import sign_download_token

class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, headers={"Origin": "https://ovd.winplaybox.in"})

    def test_resolve_empty_body(self):
        resp = self.client.post("/api/resolve", json={})
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "URL_MISSING")
        self.assertEqual(data["error"]["message"], "Paste a link to get started.")

    def test_resolve_invalid_url(self):
        resp = self.client.post("/api/resolve", json={"url": "just words without domain"})
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "URL_INVALID")

    def test_resolve_unsupported_platform(self):
        resp = self.client.post("/api/resolve", json={"url": "https://unknownsite.xyz/page"})
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "PLATFORM_UNSUPPORTED")

    @patch("httpx.AsyncClient.get")
    def test_resolve_twitter_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000000",
                "text": "Rocket launch clip",
                "author": {"name": "SpaceX", "screen_name": "SpaceX"},
                "media": {
                    "videos": [{
                        "type": "video",
                        "thumbnail_url": "https://pbs.twimg.com/thumb.jpg",
                        "variants": [
                            {"content_type": "video/mp4", "bitrate": 1000, "url": "https://video.twimg.com/clip.mp4"}
                        ]
                    }]
                }
            }
        }
        mock_get.return_value = mock_resp

        resp = self.client.post("/api/resolve", json={"url": "https://x.com/SpaceX/status/1800000000"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        result = data["data"]
        self.assertEqual(result["platform"], "twitter")
        self.assertEqual(result["title"], "Rocket launch clip")
        self.assertEqual(len(result["items"]), 1)
        self.assertTrue(result["items"][0]["variants"][0]["downloadUrl"].startswith("/api/download?token="))

    def test_download_missing_token(self):
        resp = self.client.get("/api/download")
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["error"]["code"], "URL_INVALID")

    def test_download_invalid_token(self):
        resp = self.client.get("/api/download?token=fake.tampered_signature")
        self.assertEqual(resp.status_code, 403)
        data = resp.json()
        self.assertEqual(data["error"]["code"], "PRIVATE_OR_RESTRICTED")

if __name__ == "__main__":
    unittest.main()
