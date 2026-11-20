"""Heartbeat lease fencing regression tests."""
import os
import tempfile
import time
import unittest

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_job_manager_" + "z" * 32)

import backend.job_manager as job_module


class TestHeartbeatLeaseFencing(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_jobs_dir = job_module.JOBS_DIR
        job_module.JOBS_DIR = self.temp.name
        self.manager = job_module.JobManager()
        self.manager.lease_seconds = 60

    def tearDown(self):
        job_module.JOBS_DIR = self.old_jobs_dir
        self.temp.cleanup()

    def _insert_processing_job(self, *, lease_expiry, cancel_requested=0):
        now = time.time()
        job_id = "heartbeat-test"
        with self.manager._connect() as conn:
            conn.execute("""
                INSERT INTO jobs (id, action, status, progress, created_at, updated_at,
                    lease_owner, lease_expires_at, cancel_requested)
                VALUES (?, 'mp3', 'processing', 5, ?, ?, ?, ?, ?)
            """, (job_id, now, now, self.manager.worker_id, lease_expiry, cancel_requested))
            conn.commit()
        return job_id

    async def test_heartbeat_does_not_revive_expired_lease(self):
        job_id = self._insert_processing_job(lease_expiry=time.time() - 1)
        self.assertTrue(hasattr(self.manager, "_heartbeat_once_for_test"))
        renewed = await self.manager._heartbeat_once_for_test(job_id)
        self.assertFalse(renewed)
        row = self.manager.get_job(job_id)
        self.assertLess(row["lease_expires_at"], time.time())

    async def test_heartbeat_stops_renewing_cancel_requested_job(self):
        job_id = self._insert_processing_job(lease_expiry=time.time() + 30, cancel_requested=1)
        renewed = await self.manager._heartbeat_once_for_test(job_id)
        self.assertFalse(renewed)
        row = self.manager.get_job(job_id)
        self.assertEqual(row["cancel_requested"], 1)
