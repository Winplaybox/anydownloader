import os
import tempfile
import unittest
from unittest.mock import patch

from backend.utils.generated_asset import resolve_generated_asset


class TestGeneratedAssetPaths(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = self.temp.name

    def tearDown(self):
        self.temp.cleanup()

    def _touch(self, name):
        path = os.path.join(self.root, name)
        with open(path, "wb") as out:
            out.write(b"media")
        return path

    def test_accepts_only_expected_video_name(self):
        name = "wpb_master_story_1234567890abcdef1234567890abcdef.mp4"
        path = self._touch(name)
        with patch("backend.utils.generated_asset.tempfile.gettempdir", return_value=self.root):
            self.assertEqual(resolve_generated_asset(name, "video"), path)

    def test_rejects_traversal_and_unexpected_files(self):
        self._touch("private.mp4")
        with patch("backend.utils.generated_asset.tempfile.gettempdir", return_value=self.root):
            self.assertIsNone(resolve_generated_asset("../private.mp4", "video"))
            self.assertIsNone(resolve_generated_asset("private.mp4", "video"))

    def test_rejects_expired_file(self):
        name = "wpb_master_reel_1234567890abcdef1234567890abcdef.mp4"
        path = self._touch(name)
        os.utime(path, (1, 1))
        with patch("backend.utils.generated_asset.tempfile.gettempdir", return_value=self.root):
            self.assertIsNone(resolve_generated_asset(name, "video", now=100000))

    def test_audio_is_exact_filename_allowlist(self):
        self._touch("wpb_audio_master.mp3")
        with patch("backend.utils.generated_asset.tempfile.gettempdir", return_value=self.root):
            self.assertIsNotNone(resolve_generated_asset("wpb_audio_master.mp3", "audio"))
            self.assertIsNone(resolve_generated_asset("anything.mp3", "audio"))


if __name__ == "__main__":
    unittest.main()
