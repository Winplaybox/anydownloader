import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.utils.url_normalizer import normalize_url
from backend.utils.errors import AppError, ErrorCode
from backend.extractors.twitter import TwitterExtractor
from backend.utils.security import verify_download_token

class TestTwitterExtractor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.extractor = TwitterExtractor()

    # T18: empty input
    def test_t18_empty_input(self):
        with self.assertRaises(AppError) as ctx:
            normalize_url("")
        self.assertEqual(ctx.exception.code, ErrorCode.URL_MISSING)

    # T19: garbage text
    def test_t19_garbage_text(self):
        with self.assertRaises(AppError) as ctx:
            normalize_url("random invalid string without url")
        self.assertEqual(ctx.exception.code, ErrorCode.URL_INVALID)

    # T20: unsupported site
    def test_t20_unsupported_platform(self):
        with self.assertRaises(AppError) as ctx:
            normalize_url("https://example.com/not-supported")
        self.assertEqual(ctx.exception.code, ErrorCode.PLATFORM_UNSUPPORTED)

    # T21: profile URL / spaces / lists
    async def test_t21_profile_url(self):
        with self.assertRaises(AppError) as ctx:
            await self.extractor.resolve("https://x.com/elonmusk")
        self.assertEqual(ctx.exception.code, ErrorCode.NO_MEDIA)

    async def test_t21_spaces_url(self):
        with self.assertRaises(AppError) as ctx:
            await self.extractor.resolve("https://x.com/i/spaces/123456789")
        self.assertEqual(ctx.exception.code, ErrorCode.NO_MEDIA)

    # T1: Single video with multiple bitrates
    @patch("httpx.AsyncClient.get")
    async def test_t1_single_video(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000000",
                "text": "Check out this video clip",
                "author": {"name": "NASA", "screen_name": "NASA", "avatar_url": "https://pbs.twimg.com/avatar.jpg"},
                "media": {
                    "videos": [{
                        "type": "video",
                        "thumbnail_url": "https://pbs.twimg.com/thumb.jpg",
                        "duration": 45.0,
                        "variants": [
                            {"content_type": "video/mp4", "bitrate": 2176000, "url": "https://video.twimg.com/vid/1080x1920/clip_1080.mp4"},
                            {"content_type": "video/mp4", "bitrate": 832000, "url": "https://video.twimg.com/vid/720x1280/clip_720.mp4"},
                            {"content_type": "video/mp4", "bitrate": 256000, "url": "https://video.twimg.com/vid/360x640/clip_360.mp4"}
                        ]
                    }]
                }
            }
        }
        mock_get.return_value = mock_resp

        res = await self.extractor.resolve("https://x.com/i/status/1800000000")
        self.assertEqual(res.platform, "twitter")
        self.assertEqual(len(res.items), 1)
        item = res.items[0]
        self.assertEqual(item.kind, "video")
        self.assertEqual(len(item.variants), 3)
        # Check sorted best to worst
        self.assertEqual(item.variants[0].quality, "1080p")
        self.assertEqual(item.variants[1].quality, "720p")
        self.assertEqual(item.variants[2].quality, "360p")
        # Check signed download token generated
        dl_url = item.variants[0].downloadUrl
        self.assertTrue(dl_url.startswith("/api/download?token="))
        token = dl_url.split("token=")[1]
        verified = verify_download_token(token)
        self.assertIsNotNone(verified)
        self.assertEqual(verified["variant_url"], "https://video.twimg.com/vid/1080x1920/clip_1080.mp4")

    # T10: Animated GIF tweet
    @patch("httpx.AsyncClient.get")
    async def test_t10_gif_tweet(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000001",
                "text": "Funny reaction",
                "media": {
                    "videos": [{
                        "type": "gif",
                        "thumbnail_url": "https://pbs.twimg.com/thumb.jpg",
                        "variants": [
                            {"content_type": "video/mp4", "bitrate": 0, "url": "https://video.twimg.com/tweet_video/reaction.mp4"}
                        ]
                    }]
                }
            }
        }
        mock_get.return_value = mock_resp

        res = await self.extractor.resolve("https://x.com/i/status/1800000001")
        self.assertEqual(len(res.items), 1)
        variant = res.items[0].variants[0]
        self.assertEqual(variant.quality, "GIF")
        self.assertFalse(variant.hasAudio)

    # T11: Single Image
    @patch("httpx.AsyncClient.get")
    async def test_t11_single_image(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000002",
                "text": "Stunning photo",
                "media": {
                    "photos": [{
                        "url": "https://pbs.twimg.com/media/photo1.jpg",
                        "width": 3840,
                        "height": 2160
                    }]
                }
            }
        }
        mock_get.return_value = mock_resp

        res = await self.extractor.resolve("https://x.com/i/status/1800000002")
        self.assertEqual(len(res.items), 1)
        item = res.items[0]
        self.assertEqual(item.kind, "image")
        self.assertEqual(len(item.variants), 2)
        self.assertEqual(item.variants[0].quality, "orig")
        self.assertEqual(item.variants[1].quality, "large")

    # T12: 4-image tweet
    @patch("httpx.AsyncClient.get")
    async def test_t12_four_image_tweet(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000003",
                "text": "Gallery",
                "media": {
                    "photos": [
                        {"url": f"https://pbs.twimg.com/media/photo{i}.jpg", "width": 1200, "height": 800}
                        for i in range(1, 5)
                    ]
                }
            }
        }
        mock_get.return_value = mock_resp

        res = await self.extractor.resolve("https://x.com/i/status/1800000003")
        self.assertEqual(len(res.items), 4)
        for idx, item in enumerate(res.items):
            self.assertEqual(item.index, idx + 1)
            self.assertEqual(item.kind, "image")
            self.assertEqual(item.variants[0].quality, "orig")

    # T13: Quote tweet media fallback
    @patch("httpx.AsyncClient.get")
    async def test_t13_quote_tweet_media(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000004",
                "text": "Check this quote",
                "media": {},
                "quote": {
                    "text": "Original content",
                    "author": {"screen_name": "NASA"},
                    "media": {
                        "photos": [{"url": "https://pbs.twimg.com/media/quote_img.jpg"}]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        res = await self.extractor.resolve("https://x.com/i/status/1800000004")
        self.assertEqual(len(res.items), 1)
        self.assertEqual(res.items[0].kind, "image")

    # T15: Text-only tweet -> NO_MEDIA
    @patch("httpx.AsyncClient.get")
    async def test_t15_text_only_tweet(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tweet": {
                "id": "1800000005",
                "text": "Just a thought without any media",
                "media": {}
            }
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(AppError) as ctx:
            await self.extractor.resolve("https://x.com/i/status/1800000005")
        self.assertEqual(ctx.exception.code, ErrorCode.NO_MEDIA)

    # T16: Deleted tweet -> NOT_FOUND
    @patch("httpx.AsyncClient.get")
    async def test_t16_deleted_tweet(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Tweet not found or deleted"
        mock_get.return_value = mock_resp

        with self.assertRaises(AppError) as ctx:
            await self.extractor.resolve("https://x.com/i/status/1800000006")
        self.assertEqual(ctx.exception.code, ErrorCode.NOT_FOUND)

    # T17: Private/restricted tweet -> PRIVATE_OR_RESTRICTED
    @patch("httpx.AsyncClient.get")
    async def test_t17_private_tweet(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Account is protected"
        mock_get.return_value = mock_resp

        with self.assertRaises(AppError) as ctx:
            await self.extractor.resolve("https://x.com/i/status/1800000007")
        self.assertEqual(ctx.exception.code, ErrorCode.PRIVATE_OR_RESTRICTED)

if __name__ == "__main__":
    unittest.main()
