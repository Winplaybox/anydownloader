import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_job_manager_" + "z" * 32)

from backend.utils.security import sign_download_token
import backend.job_manager as job_module


class TestJobCancellationFencing(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_jobs_dir = job_module.JOBS_DIR
        job_module.JOBS_DIR = self.temp.name
        self.manager = job_module.JobManager()
        self.manager.start = lambda: None
        self.token = sign_download_token(
            "https://video.twimg.com/media/test.mp4", "test.mp4", ttl_seconds=3600
        )

    def tearDown(self):
        job_module.JOBS_DIR = self.old_jobs_dir
        self.temp.cleanup()

    async def _create_and_claim(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            job_id, owner_token = await self.manager.create_job([self.token], "merge", height=720)
        claimed = self.manager._claim_next_job()
        self.assertEqual(claimed["id"], job_id)
        return job_id, owner_token, claimed

    async def test_processing_cancel_sets_flag_without_releasing_lease(self):
        job_id, owner_token, claimed = await self._create_and_claim()

        self.assertTrue(self.manager.cancel_job(job_id, owner_token))
        persisted = self.manager.get_job(job_id)
        self.assertEqual(persisted["status"], "processing")
        self.assertEqual(persisted["cancel_requested"], 1)
        self.assertEqual(persisted["lease_owner"], claimed["lease_owner"])
        self.assertTrue(self.manager._is_cancelled(job_id))

    async def test_cancel_request_from_wrong_owner_is_rejected(self):
        job_id, _, _ = await self._create_and_claim()
        self.assertFalse(self.manager.cancel_job(job_id, "wrong-owner-token"))
        persisted = self.manager.get_job(job_id)
        self.assertEqual(persisted["cancel_requested"], 0)
        self.assertEqual(persisted["status"], "processing")

    async def test_stale_worker_owner_cannot_persist_progress(self):
        job_id, _, claimed = await self._create_and_claim()
        stale_job = {
            key: claimed.get(key) for key in (
                "id", "action", "status", "progress", "output_file",
                "download_url", "filename", "error", "created_at", "lease_owner"
            )
        }
        stale_job["lease_owner"] = "worker-that-lost-the-lease"
        stale_job["progress"] = 91

        self.manager._save_job_db(stale_job)
        persisted = self.manager.get_job(job_id)
        self.assertNotEqual(persisted["progress"], 91)
        self.assertEqual(persisted["lease_owner"], claimed["lease_owner"])

    async def test_cancelled_worker_is_not_reported_as_active_by_cancellation_check(self):
        job_id, owner_token, _ = await self._create_and_claim()
        self.assertFalse(self.manager._is_cancelled(job_id))
        self.assertTrue(self.manager.cancel_job(job_id, owner_token))
        self.assertTrue(self.manager._is_cancelled(job_id))


if __name__ == "__main__":
    unittest.main()
