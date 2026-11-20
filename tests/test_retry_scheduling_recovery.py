"""Regression tests for retry scheduling and recovery across manager instances."""
import os
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_job_manager_" + "z" * 32)

import backend.job_manager as job_module
from backend.utils.security import sign_download_token


class TestRetrySchedulingRecovery(unittest.IsolatedAsyncioTestCase):
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

    async def _create(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            return await self.manager.create_job([self.token], "merge", height=720)

    async def test_retry_delay_prevents_early_claim_and_allows_claim_when_due(self):
        job_id, _ = await self._create()
        first = self.manager._claim_next_job()
        self.assertEqual(first["id"], job_id)

        retry_at = time.time() + 120
        with self.manager._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status='queued', next_run_at=?, lease_owner=NULL, "
                "lease_expires_at=NULL, error='temporary failure' WHERE id=?",
                (retry_at, job_id),
            )
            conn.commit()

        self.assertIsNone(self.manager._claim_next_job())
        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET next_run_at=? WHERE id=?", (time.time() - 1, job_id))
            conn.commit()

        second = self.manager._claim_next_job()
        self.assertIsNotNone(second)
        self.assertEqual(second["id"], job_id)
        self.assertEqual(second["attempts"], 2)

    async def test_new_manager_recovers_due_queued_job_from_shared_database(self):
        job_id, _ = await self._create()
        first = self.manager._claim_next_job()
        self.assertEqual(first["id"], job_id)

        with self.manager._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status='queued', next_run_at=?, lease_owner=NULL, "
                "lease_expires_at=NULL WHERE id=?",
                (time.time() - 1, job_id),
            )
            conn.commit()

        restarted = job_module.JobManager()
        restarted.db_path = self.manager.db_path
        claim = restarted._claim_next_job()
        self.assertIsNotNone(claim)
        self.assertEqual(claim["id"], job_id)
        self.assertEqual(claim["attempts"], 2)

    async def test_terminal_failure_is_not_claimed_again(self):
        job_id, _ = await self._create()
        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET max_attempts=1 WHERE id=?", (job_id,))
            conn.commit()
        first = self.manager._claim_next_job()
        self.assertEqual(first["attempts"], 1)
        with self.manager._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status='failed', error='retry limit reached', "
                "lease_owner=NULL, lease_expires_at=NULL WHERE id=?",
                (job_id,),
            )
            conn.commit()
        self.assertIsNone(self.manager._claim_next_job())
        self.assertEqual(self.manager.get_job(job_id)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
