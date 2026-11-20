import os
import tempfile
import unittest
from unittest.mock import patch

from backend import routes_temp_media as temp_media


class TestTemporaryMediaStorageHardening(unittest.TestCase):
    def test_storage_root_is_created_private(self):
        with tempfile.TemporaryDirectory() as parent:
            store = os.path.join(parent, "media")
            with patch.object(temp_media, "STORE_DIR", store):
                temp_media._ensure_store()
                self.assertTrue(os.path.isdir(store))
                if os.name == "posix":
                    self.assertEqual(os.stat(store).st_mode & 0o777, 0o700)

    def test_storage_root_symlink_is_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("Symlinks are unavailable on this platform")
        with tempfile.TemporaryDirectory() as parent:
            target = os.path.join(parent, "target")
            link = os.path.join(parent, "link")
            os.mkdir(target)
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is not permitted")
            with patch.object(temp_media, "STORE_DIR", link):
                with self.assertRaises(RuntimeError):
                    temp_media._ensure_store()


if __name__ == "__main__":
    unittest.main()
