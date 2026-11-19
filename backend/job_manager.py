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
                asyncio.get_running_loop().create_task(self._cleanup_loop())
                self._cleaner_started = True
            except RuntimeError:
                pass

    def start(self):
        self._ensure_cleaner()
        if self._worker_task is None or self._worker_task.done():
            try:
                self._worker_task = asyncio.get_running_loop().create_task(self._worker_loop())
            except RuntimeError:
                pass

    @staticmethod
    def _owner_hash(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_source_page(source_url: Optional[str]) -> Optional[str]:
        if not source_url:
            return None
        parsed = urllib.parse.urlsplit(str(source_url).strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        allowed = (
            "youtube.com", "youtu.be", "twitter.com", "x.com", "instagram.com",
            "tiktok.com", "facebook.com", "fb.watch", "pinterest.com", "pin.it",
            "reddit.com", "redd.it", "soundcloud.com", "vimeo.com",
        )
        if (
            parsed.scheme != "https" or not host or parsed.username or parsed.password
            or parsed.port not in (None, 443)
            or not any(host == domain or host.endswith("." + domain) for domain in allowed)
        ):
            raise ValueError("Unsupported or unsafe source URL.")
        return str(source_url).strip()

    async def create_job(
        self, tokens: List[str], action: str, source_url: Optional[str] = None,
        height: int = 1080, title: Optional[str] = None,
    ):
        if action not in {"merge", "mp3", "zip"}:
            raise ValueError("Unsupported job action.")
        if not isinstance(tokens, list):
            raise ValueError("Tokens must be an array.")
        max_tokens = 40 if action == "zip" else (2 if action == "merge" else 1)
        if not (1 <= len(tokens) <= max_tokens):
            raise ValueError(f"Action '{action}' requires between 1 and {max_tokens} media tokens.")
        if action == "mp3" and len(tokens) != 1:
            raise ValueError("MP3 extraction requires exactly one token.")
        if action == "merge" and len(tokens) not in (1, 2):
            raise ValueError("Merge requires one video token and an optional audio token.")
        if action == "merge" and (not isinstance(height, int) or height < 144 or height > 2160):
            raise ValueError("Video height must be between 144 and 2160.")
        safe_source_url = self._validate_source_page(source_url)
        for token in tokens:
            if not isinstance(token, str) or token.startswith(("http://", "https://", "/api/")):
                raise ValueError("Only signed download tokens are accepted.")
            payload = verify_download_token(token)
            if not payload or not payload.get("variant_url"):
                raise ValueError("A download token is invalid or expired.")

        job_id = str(uuid.uuid4())
        owner_token = secrets.token_urlsafe(32)
        ext = "mp4" if action == "merge" else ("mp3" if action == "mp3" else "zip")
        clean = re.sub(r'[\\/*?:"<>|]', "", str(title or "")).strip()
        clean = re.sub(r"\s+", "_", clean)[:60]
        filename = f"{clean}.{ext}" if clean else f"ovd_{action}_{job_id[:8]}.{ext}"
        now = time.time()
        payload = {"tokens": tokens, "source_url": safe_source_url, "height": height}
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO jobs (
                    id, action, status, progress, output_file, download_url, filename,
                    error, created_at, updated_at, payload_json, owner_token_hash,
                    attempts, max_attempts, next_run_at, cancel_requested
                ) VALUES (?, ?, 'queued', 0, NULL, NULL, ?, NULL, ?, ?, ?, ?, 0, ?, ?, 0)
            """, (
                job_id, action, filename, now, now, json.dumps(payload, separators=(",", ":")),
                self._owner_hash(owner_token), self.max_attempts, now,
            ))
            conn.commit()
        self.jobs[job_id] = {
            "id": job_id, "action": action, "status": "queued", "progress": 0,
            "output_file": None, "download_url": None, "filename": filename,
            "error": None, "created_at": now, "updated_at": now,
        }
        self.start()
        return job_id, owner_token

    def authorize_job(self, job_id: str, owner_token: str) -> bool:
        if not owner_token:
            return False
        with self._connect() as conn:
            row = conn.execute(
                "SELECT owner_token_hash FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        expected = row["owner_token_hash"] if row else None
        return bool(expected and hmac.compare_digest(expected, self._owner_hash(owner_token)))

    def cancel_job(self, job_id: str, owner_token: str) -> bool:
        if not self.authorize_job(job_id, owner_token):
            return False
        with self._connect() as conn:
            row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return False
            if row["status"] in ("done", "failed", "cancelled"):
                return True
            if row["status"] == "queued":
                conn.execute(
                    "UPDATE jobs SET status='cancelled', error='Cancelled by owner.', updated_at=? WHERE id=?",
                    (time.time(), job_id),
                )
            else:
                conn.execute(
                    "UPDATE jobs SET cancel_requested=1, updated_at=? WHERE id=?",
                    (time.time(), job_id),
                )
            conn.commit()
        return True

    def _claim_next_job(self):
        now = time.time()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("""
                SELECT id FROM jobs
                WHERE (status='queued' AND next_run_at <= ?)
                   OR (status='processing' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?)
                ORDER BY created_at ASC LIMIT 1
            """, (now, now)).fetchone()
            if not row:
                conn.commit()
                return None
            job_id = row["id"]
            updated = conn.execute("""
                UPDATE jobs SET status='processing', lease_owner=?, lease_expires_at=?,
                    attempts=attempts+1, progress=MAX(progress, 5), updated_at=?
                WHERE id=? AND (
                    (status='queued' AND next_run_at <= ?)
                    OR (status='processing' AND lease_expires_at < ?)
                )
            """, (self.worker_id, now + self.lease_seconds, now, job_id, now, now))
            if updated.rowcount != 1:
                conn.rollback()
                return None
            claimed = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            conn.commit()
        data = dict(claimed)
        data["payload"] = json.loads(data.get("payload_json") or "{}")
        return data

    async def _heartbeat(self, job_id: str):
        while True:
            await asyncio.sleep(max(10, self.lease_seconds // 3))
            with self._connect() as conn:
                updated = conn.execute("""
                    UPDATE jobs SET lease_expires_at=?, updated_at=?
                    WHERE id=? AND status='processing' AND lease_owner=?
                """, (time.time() + self.lease_seconds, time.time(), job_id, self.worker_id))
                conn.commit()
                if updated.rowcount != 1:
                    return

    async def _worker_loop(self):
        while True:
            try:
                claimed = await asyncio.to_thread(self._claim_next_job)
                if not claimed:
                    await asyncio.sleep(1.0)
                    continue
                job_id = claimed["id"]
                job = {k: claimed.get(k) for k in (
                    "id", "action", "status", "progress", "output_file",
                    "download_url", "filename", "error", "created_at",
                )}
                self.jobs[job_id] = job
                heartbeat = asyncio.create_task(self._heartbeat(job_id))
                try:
                    if claimed.get("cancel_requested"):
                        raise asyncio.CancelledError()
                    payload = claimed["payload"]
                    await self._process_job(
                        job_id, payload.get("tokens", []), claimed["action"],
                        source_url=payload.get("source_url"), height=int(payload.get("height") or 1080),
                    )
                    with self._connect() as conn:
                        current = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
                        if current and current["status"] == "processing":
                            conn.execute("""
                                UPDATE jobs SET status='done', progress=100, lease_owner=NULL,
                                    lease_expires_at=NULL, updated_at=? WHERE id=? AND lease_owner=?
                            """, (time.time(), job_id, self.worker_id))
                            conn.commit()
                except asyncio.CancelledError:
                    with self._connect() as conn:
                        conn.execute("""
                            UPDATE jobs SET status='cancelled', error='Cancelled by owner.',
                                lease_owner=NULL, lease_expires_at=NULL, updated_at=?
                            WHERE id=? AND lease_owner=?
                        """, (time.time(), job_id, self.worker_id))
                        conn.commit()
                except Exception as exc:
                    with self._connect() as conn:
                        row = conn.execute(
                            "SELECT attempts, max_attempts FROM jobs WHERE id=?", (job_id,)
                        ).fetchone()
                        attempts = int(row["attempts"]) if row else self.max_attempts
                        maximum = int(row["max_attempts"]) if row else self.max_attempts
                        retry = not isinstance(exc, (ValueError, FileNotFoundError)) and attempts < maximum
                        delay = min(60, 3 * (2 ** max(0, attempts - 1)))
                        conn.execute("""
                            UPDATE jobs SET status=?, error=?, next_run_at=?, lease_owner=NULL,
                                lease_expires_at=NULL, updated_at=?
                            WHERE id=? AND lease_owner=?
                        """, (
                            "queued" if retry else "failed", str(exc)[:500],
                            time.time() + delay if retry else 0, time.time(), job_id, self.worker_id,
                        ))
                        conn.commit()
                finally:
                    heartbeat.cancel()
                    try:
                        await heartbeat
                    except asyncio.CancelledError:
                        pass
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[job_manager] queue loop error: {type(exc).__name__}: {exc}", flush=True)
                await asyncio.sleep(2.0)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        job = dict(row)
        self.jobs[job_id] = job
        return job

    def _is_cancelled(self, job_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT cancel_requested FROM jobs WHERE id=?", (job_id,)).fetchone()
        return bool(row and row["cancel_requested"])

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
