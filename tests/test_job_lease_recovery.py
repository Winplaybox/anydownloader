"""Lease expiry and recovery regression tests for the SQLite job queue."""
import os
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_job_manager_" + "z" * 32)

import backend.job_manager as job_module
from backend.utils.security import sign_download_token


class TestLeaseRecovery(unittest.IsolatedAsyncioTestCase):
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

    async def create_job(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            return await self.manager.create_job([self.token], "merge", height=720)

    async def test_expired_lease_is_reclaimed_and_attempt_counter_increments(self):
        job_id, _ = await self.create_job()
        first = self.manager._claim_next_job()
        self.assertEqual(first["id"], job_id)
        self.assertEqual(first["attempts"], 1)

        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET lease_expires_at=? WHERE id=?", (time.time() - 1, job_id))
            conn.commit()

        second = self.manager._claim_next_job()
        self.assertIsNotNone(second)
        self.assertEqual(second["id"], job_id)
        self.assertEqual(second["attempts"], 2)
        self.assertNotEqual(first["lease_owner"], second["lease_owner"])

    async def test_expired_lease_at_attempt_limit_is_marked_failed(self):
        job_id, _ = await self.create_job()
        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET max_attempts=1 WHERE id=?", (job_id,))
            conn.commit()

        first = self.manager._claim_next_job()
        self.assertEqual(first["attempts"], 1)
        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET lease_expires_at=? WHERE id=?", (time.time() - 1, job_id))
            conn.commit()

        self.assertIsNone(self.manager._claim_next_job())
        persisted = self.manager.get_job(job_id)
        self.assertEqual(persisted["status"], "failed")
        self.assertIn("maximum attempts", persisted["error"])
        self.assertIsNone(persisted["lease_owner"])
        self.assertIsNone(persisted["lease_expires_at"])
