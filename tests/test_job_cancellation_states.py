"""Cancellation-state regression tests for durable jobs."""
import asyncio
import os
import tempfile
import unittest
import time
from unittest.mock import patch

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_job_manager_" + "z" * 32)

import backend.job_manager as job_module
from backend.utils.security import sign_download_token


class TestJobCancellationState(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_jobs_dir = job_module.JOBS_DIR
        job_module.JOBS_DIR = self.temp.name
        self.manager = job_module.JobManager()
        self.manager.start = lambda: None
        self.token = sign_download_token("https://video.twimg.com/media/test.mp4", "test.mp4", ttl_seconds=3600)

    def tearDown(self):
        job_module.JOBS_DIR = self.old_jobs_dir
        self.temp.cleanup()

    async def _create(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            return await self.manager.create_job([self.token], "merge", height=720)

    async def test_cancel_processing_sets_flag_without_premature_terminal_state(self):
        job_id, owner_token = await self._create()
        with self.manager._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status='processing', lease_owner=?, lease_expires_at=? WHERE id=?",
                (self.manager.worker_id, time.time() + 300, job_id),
            )
            conn.commit()

        self.assertTrue(self.manager.cancel_job(job_id, owner_token))
        persisted = self.manager.get_job(job_id)
        self.assertEqual(persisted["status"], "processing")
        self.assertEqual(persisted["cancel_requested"], 1)

    async def test_cancel_unknown_job_returns_false(self):
        self.assertFalse(self.manager.cancel_job("missing-job", "owner-token"))
