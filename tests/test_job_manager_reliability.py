import asyncio
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_job_manager_" + "z" * 32)

from backend.utils.security import sign_download_token
import backend.job_manager as job_module


class TestDurableJobManager(unittest.IsolatedAsyncioTestCase):
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

    async def test_job_is_persisted_and_owner_token_is_not_stored(self):
        job_id, owner_token = await self._create()
        job = self.manager.get_job(job_id)
        self.assertEqual(job["status"], "queued")
        self.assertTrue(self.manager.authorize_job(job_id, owner_token))
        self.assertFalse(self.manager.authorize_job(job_id, "wrong-token"))
        with self.manager._connect() as conn:
            row = conn.execute("SELECT owner_token_hash, payload_json FROM jobs WHERE id=?", (job_id,)).fetchone()
        self.assertNotEqual(row["owner_token_hash"], owner_token)
        self.assertNotIn(owner_token, row["payload_json"])

    async def test_atomic_claim_prevents_two_workers_claiming_same_job(self):
        job_id, owner_token = await self._create()
        second = job_module.JobManager()
        second.db_path = self.manager.db_path
        claim1 = self.manager._claim_next_job()
        claim2 = second._claim_next_job()
        self.assertEqual(claim1["id"], job_id)
        self.assertIsNone(claim2)

    async def test_owner_can_cancel_queued_job(self):
        job_id, owner_token = await self._create()
        self.assertTrue(self.manager.cancel_job(job_id, owner_token))
        self.assertEqual(self.manager.get_job(job_id)["status"], "cancelled")
        self.assertFalse(self.manager.cancel_job(job_id, "not-the-owner"))

    async def test_unsigned_direct_urls_are_rejected(self):
        with self.assertRaises(ValueError):
            await self.manager.create_job(["https://video.twimg.com/media/test.mp4"], "merge")

    async def test_source_page_must_be_https_and_supported(self):
        with self.assertRaises(ValueError):
            await self.manager.create_job([self.token], "merge", source_url="http://youtube.com/watch?v=x")
        with self.assertRaises(ValueError):
            await self.manager.create_job([self.token], "merge", source_url="https://attacker.example/")

    async def test_idempotency_returns_same_job_and_owner_token(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            first_id, first_token = await self.manager.create_job(
                [self.token], "merge", height=720,
                idempotency_key="merge-request-123", owner_context="203.0.113.10",
            )
            second_id, second_token = await self.manager.create_job(
                [self.token], "merge", height=720,
                idempotency_key="merge-request-123", owner_context="203.0.113.10",
            )
        self.assertEqual(first_id, second_id)
        self.assertEqual(first_token, second_token)
        self.assertTrue(self.manager.authorize_job(first_id, second_token))

    async def test_idempotency_key_rejects_different_payload(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            await self.manager.create_job(
                [self.token], "merge", height=720,
                idempotency_key="merge-request-456", owner_context="203.0.113.10",
            )
            with self.assertRaises(ValueError):
                await self.manager.create_job(
                    [self.token], "merge", height=1080,
                    idempotency_key="merge-request-456", owner_context="203.0.113.10",
                )

    async def test_idempotency_is_scoped_to_requester_context(self):
        with patch("backend.job_manager.verify_public_dns_resolution", return_value=True):
            first_id, _ = await self.manager.create_job(
                [self.token], "merge", height=720,
                idempotency_key="merge-request-789", owner_context="203.0.113.10",
            )
            second_id, _ = await self.manager.create_job(
                [self.token], "merge", height=720,
                idempotency_key="merge-request-789", owner_context="203.0.113.11",
            )
        self.assertNotEqual(first_id, second_id)


    async def test_stale_worker_cannot_write_after_lease_expiry(self):
        job_id, owner_token = await self._create()
        claimed = self.manager._claim_next_job()
        self.assertEqual(claimed["id"], job_id)
        job = {k: claimed.get(k) for k in (
            "id", "action", "status", "progress", "output_file",
            "download_url", "filename", "error", "created_at", "lease_owner",
        )}
        job["progress"] = 88
        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET lease_expires_at=? WHERE id=?", (0, job_id))
            conn.commit()
        self.manager._save_job_db(job)
        persisted = self.manager.get_job(job_id)
        self.assertNotEqual(persisted["progress"], 88)

    async def test_worker_detects_lost_lease_and_stops_processing(self):
        job_id, _ = await self._create()
        claimed = self.manager._claim_next_job()
        self.assertEqual(claimed["id"], job_id)
        self.assertFalse(self.manager._is_cancelled(job_id))
        with self.manager._connect() as conn:
            conn.execute("UPDATE jobs SET lease_expires_at=? WHERE id=?", (0, job_id))
            conn.commit()
        self.assertTrue(self.manager._is_cancelled(job_id))

    async def test_artifact_paths_are_fenced_by_attempt_and_worker(self):
        job_id = "job-unique-id"
        path_a = self.manager._artifact_path(job_id, 1, "worker-a", "output.mp4")
        path_b = self.manager._artifact_path(job_id, 2, "worker-b", "output.mp4")
        path_c = self.manager._artifact_path(job_id, 1, "worker-c", "output.mp4")
        self.assertNotEqual(path_a, path_b)
        self.assertNotEqual(path_a, path_c)
        self.assertNotEqual(path_b, path_c)
        self.assertTrue(os.path.basename(path_a).startswith(f".{job_id}.1."))

    async def test_queue_metrics_include_lease_and_age_fields(self):
        stats = self.manager.get_stats()
        self.assertEqual(stats["queued"], 0)
        self.assertEqual(stats["active_leases"], 0)
        self.assertEqual(stats["expired_leases"], 0)
        self.assertEqual(stats["total_attempts"], 0)
        self.assertIn("oldest_queued_age_seconds", stats)

    async def test_queue_schema_migrates_legacy_table(self):
        path = os.path.join(self.temp.name, "legacy.db")
        with sqlite3.connect(path) as conn:
            conn.execute("""CREATE TABLE jobs (
                id TEXT PRIMARY KEY, action TEXT, status TEXT, progress INTEGER,
                output_file TEXT, download_url TEXT, filename TEXT, error TEXT,
                created_at REAL, updated_at REAL
            )""")
        manager = job_module.JobManager()
        manager.db_path = path
        manager._init_db()
        with manager._connect() as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
        self.assertIn("payload_json", columns)
        self.assertIn("lease_expires_at", columns)


if __name__ == "__main__":
    unittest.main()
