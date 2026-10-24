import unittest
from backend.platform_registry import PlatformRegistry
from backend.schema import NormalizedResult, VideoVariant, Stats

class TestRegistryV3(unittest.TestCase):
    def setUp(self):
        self.reg = PlatformRegistry()

    def test_platforms_loaded(self):
        self.assertGreaterEqual(len(self.reg.platforms), 8)
        yt = self.reg.get_platform("youtube")
        self.assertIsNotNone(yt)
        self.assertEqual(yt["tier"], "A")
        self.assertIn("video", yt["routes"])

    def test_url_matching_youtube(self):
        p, ctype, mid = self.reg.match("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(p["id"], "youtube")
        self.assertEqual(ctype, "video")
        self.assertEqual(mid, "dQw4w9WgXcQ")

    def test_url_matching_youtube_shorts(self):
        p, ctype, mid = self.reg.match("https://www.youtube.com/shorts/kJQP7kiw5Fk")
        self.assertEqual(p["id"], "youtube")
        self.assertEqual(ctype, "short")
        self.assertEqual(mid, "kJQP7kiw5Fk")

    def test_url_matching_instagram_reel(self):
        p, ctype, mid = self.reg.match("https://www.instagram.com/reel/De1j7WADf_8/")
        self.assertEqual(p["id"], "instagram")
        self.assertEqual(ctype, "reel")
        self.assertEqual(mid, "De1j7WADf_8")

    def test_url_matching_tiktok(self):
        p, ctype, mid = self.reg.match("https://www.tiktok.com/@creator/video/7106594312292453678")
        self.assertEqual(p["id"], "tiktok")
        self.assertEqual(ctype, "video")
        self.assertEqual(mid, "7106594312292453678")

    def test_schema_honest_stats_omission(self):
        stats = Stats(views=1000, likes=50)
        d = stats.to_dict()
        self.assertEqual(d["views"], 1000)
        self.assertEqual(d["likes"], 50)
        # comments, shares, etc. should be omitted, NEVER fake 0
        self.assertNotIn("comments", d)
        self.assertNotIn("shares", d)

if __name__ == "__main__":
    unittest.main()
