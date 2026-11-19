import asyncio
import os
import re
import uuid
import shutil
import sqlite3
import zipfile
import tempfile
import time
import json
import hashlib
import secrets
import socket
import urllib.parse
import hmac
from typing import Dict, Any, Optional, List
import static_ffmpeg
import httpx

try:
    from backend.utils.security import verify_download_token
except (ModuleNotFoundError, ImportError):
    from utils.security import verify_download_token

static_ffmpeg.add_paths()

JOBS_DIR = os.environ.get("JOBS_DIR") or os.path.join(tempfile.gettempdir(), "ovd_jobs")
os.makedirs(JOBS_DIR, exist_ok=True)


class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.db_path = os.path.join(JOBS_DIR, "jobs.db")
        self._init_db()
        self._cleaner_started = False
        self._worker_task = None
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
        self.lease_seconds = max(60, int(os.environ.get("JOB_LEASE_SECONDS", "300")))
        self.max_attempts = max(1, min(5, int(os.environ.get("JOB_MAX_ATTEMPTS", "3"))))

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=15000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, action TEXT, status TEXT, progress INTEGER,
                    output_file TEXT, download_url TEXT, filename TEXT, error TEXT,
                    created_at REAL, updated_at REAL, payload_json TEXT,
                    owner_token_hash TEXT, attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3, next_run_at REAL NOT NULL DEFAULT 0,
                    lease_owner TEXT, lease_expires_at REAL,
                    cancel_requested INTEGER NOT NULL DEFAULT 0
                )
            """)
            existing = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
            migrations = {
                "payload_json": "TEXT", "owner_token_hash": "TEXT",
                "attempts": "INTEGER NOT NULL DEFAULT 0",
                "max_attempts": "INTEGER NOT NULL DEFAULT 3",
                "next_run_at": "REAL NOT NULL DEFAULT 0", "lease_owner": "TEXT",
                "lease_expires_at": "REAL", "cancel_requested": "INTEGER NOT NULL DEFAULT 0",
            }
            for name, definition in migrations.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, next_run_at, lease_expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_owner ON jobs(owner_token_hash)")
            conn.commit()
        try:
            os.chmod(self.db_path, 0o600)
            os.chmod(JOBS_DIR, 0o700)
        except OSError:
            pass

    def _save_job_db(self, job: Dict[str, Any]):
        with self._connect() as conn:
            conn.execute("""
                UPDATE jobs SET status=?, progress=?, output_file=?, download_url=?,
                    filename=?, error=?, updated_at=? WHERE id=?
            """, (
                job.get("status"), job.get("progress", 0), job.get("output_file"),
                job.get("download_url"), job.get("filename"), job.get("error"),
                time.time(), job.get("id"),
            ))
            conn.commit()

    def _ensure_cleaner(self):
        if not self._cleaner_started:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._cleanup_loop())
                self._cleaner_started = True
            except RuntimeError:
                pass

    async def create_job(self, tokens: List[str], action: str, source_url: Optional[str] = None, height: int = 1080, title: Optional[str] = None) -> str:
        self._ensure_cleaner()
        job_id = str(uuid.uuid4())
        ext = 'mp4' if action == 'merge' else ('mp3' if action == 'mp3' else 'zip')
        if title:
            clean = re.sub(r'[\\/*?:"<>|]', "", str(title)).strip()
            clean = re.sub(r'\s+', "_", clean)[:60]
            filename = f"{clean}.{ext}" if clean else f"ovd_{action}_{job_id[:8]}.{ext}"
        else:
            filename = f"ovd_{action}_{job_id[:8]}.{ext}"

        job_data = {
            "id": job_id,
            "action": action,
            "status": "queued",
            "progress": 0,
            "output_file": None,
            "download_url": None,
            "filename": filename,
            "error": None,
            "created_at": time.time()
        }
        self.jobs[job_id] = job_data
        self._save_job_db(job_data)
        asyncio.create_task(self._process_job(job_id, tokens, action, source_url=source_url, height=height))
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        if job_id in self.jobs:
            return self.jobs[job_id]
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                if row:
                    job = dict(row)
                    self.jobs[job_id] = job
                    return job
        except Exception as e:
            print(f"[job_manager] DB read error: {e}", flush=True)
        return None

    async def _process_job(self, job_id: str, tokens: List[str], action: str, source_url: Optional[str] = None, height: int = 1080):
        job = self.jobs.get(job_id)
        if not job:
            return

        job["status"] = "processing"
        job["progress"] = 15
        self._save_job_db(job)
        ffmpeg_bin = shutil.which("ffmpeg")

        try:
            # 1. High-speed worker delegation (runs on Hostinger VPS: fast network, hardware ffmpeg, residential IP)
            if action == "merge" and source_url:
                job["progress"] = 35
                self._save_job_db(job)
                try:
                    from backend.main import _download_via_worker
                except Exception:
                    try:
                        from main import _download_via_worker
                    except Exception:
                        _download_via_worker = None

                if _download_via_worker:
                    job["progress"] = 55
                    self._save_job_db(job)
                    try:
                        worker_url = await _download_via_worker(source_url, "video", height=height)
                        if worker_url:
                            job["download_url"] = worker_url
                            job["status"] = "done"
                            job["progress"] = 100
                            self._save_job_db(job)
                            return
                    except Exception as we:
                        print(f"[job_manager] worker delegation failed, falling back to local task: {we}", flush=True)

                # Fallback to local yt-dlp download task if source_url is available
                try:
                    from backend.main import _run_download_limited, run_download_video_task
                except Exception:
                    try:
                        from main import _run_download_limited, run_download_video_task
                    except Exception:
                        run_download_video_task = None
                        _run_download_limited = None

                if run_download_video_task:
                    job["progress"] = 65
                    self._save_job_db(job)
                    output_path = os.path.join(JOBS_DIR, job["filename"])
                    try:
                        if _run_download_limited:
                            await _run_download_limited(run_download_video_task, source_url, height, output_path)
                        else:
                            await asyncio.to_thread(run_download_video_task, source_url, height, output_path)
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                            job["output_file"] = output_path
                            job["status"] = "done"
                            job["progress"] = 100
                            job["download_url"] = f"/api/jobs/{job_id}/file"
                            self._save_job_db(job)
                            return
                    except Exception as lde:
                        print(f"[job_manager] local yt-dlp task failed, trying ffmpeg stream merge: {lde}", flush=True)

            # Verify tokens only through the security module; do not decode unsigned payloads.
            sources = []
            for t in tokens:
                payload = verify_download_token(t)
                if not payload:
                    raise ValueError("Invalid or expired download token.")
                sources.append(payload["variant_url"])

            job["progress"] = 75
            self._save_job_db(job)
            output_path = os.path.join(JOBS_DIR, job["filename"])

            ua_args = [
                "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                "-headers", "Referer: https://www.youtube.com/\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0\r\n"
            ]
            if action == "merge":
                if not ffmpeg_bin:
                    raise RuntimeError("ffmpeg not found for video merging.")
                # Expecting at least 1 or 2 sources (video, and optionally audio)
                if len(sources) == 1:
                    cmd = [ffmpeg_bin, "-y"] + ua_args + ["-i", sources[0], "-c:v", "copy", "-c:a", "aac", output_path]
                else:
                    cmd = [ffmpeg_bin, "-y"] + ua_args + ["-i", sources[0]] + ua_args + ["-i", sources[1], "-c:v", "copy", "-c:a", "aac", output_path]

                job["progress"] = 85
                self._save_job_db(job)
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    err_msg = (stderr or b"").decode("utf-8", errors="ignore")[-200:]
                    print(f"[job_manager] ffmpeg failed (code {proc.returncode}): {err_msg}", flush=True)
                    raise RuntimeError(f"ffmpeg merge process failed: {err_msg.strip()[:80]}")

            elif action == "mp3":
                if not ffmpeg_bin:
                    raise RuntimeError("ffmpeg not found for mp3 extraction.")
                cmd = [ffmpeg_bin, "-y"] + ua_args + ["-i", sources[0], "-vn", "-c:a", "libmp3lame", "-q:a", "2", output_path]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError("ffmpeg mp3 conversion failed.")

            elif action == "zip":
                job["filename"] = f"ovd_gallery_{job_id[:8]}.zip"
                output_path = os.path.join(JOBS_DIR, job["filename"])
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                        for idx, src in enumerate(sources):
                            resp = await client.get(src, headers={"User-Agent": "Mozilla/5.0"})
                            if resp.status_code == 200:
                                ext = "jpg" if ".png" not in src else "png"
                                zf.writestr(f"media_{idx+1}.{ext}", resp.content)
                            job["progress"] = int(25 + (70 * (idx + 1) / len(sources)))
                            self._save_job_db(job)

            job["output_file"] = output_path
            job["status"] = "done"
            job["progress"] = 100
            job["download_url"] = f"/api/jobs/{job_id}/file"
            self._save_job_db(job)

        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            self._save_job_db(job)

    async def _cleanup_loop(self):
        """Auto-deletes temporary job files older than 2 hours."""
        while True:
            await asyncio.sleep(600)
            now = time.time()
            to_del = []
            for jid, j in list(self.jobs.items()):
                if now - j.get("created_at", now) > 7200:
                    f = j.get("output_file")
                    if f and os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
                    to_del.append(jid)
            for jid in to_del:
                self.jobs.pop(jid, None)

            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM jobs WHERE created_at < ?", (now - 7200,))
                    conn.commit()
            except Exception:
                pass


job_manager = JobManager()
