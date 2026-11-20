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
import base64
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
import static_ffmpeg
import httpx

try:
    from backend.utils.security import verify_download_token, is_safe_cdn_host, verify_safe_upstream_url, verify_public_dns_resolution
except (ModuleNotFoundError, ImportError):
    from utils.security import verify_download_token, is_safe_cdn_host, verify_safe_upstream_url, verify_public_dns_resolution

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
        owner_secret = (os.environ.get("JOB_OWNER_SECRET") or os.environ.get("WPB_VAULT_SECRET", "").split(",")[0]).strip()
        self.owner_secret = owner_secret.encode("utf-8") if owner_secret else secrets.token_bytes(32)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=15000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            yield conn
        finally:
            conn.close()

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
                "idempotency_key": "TEXT", "idempotency_owner": "TEXT", "request_fingerprint": "TEXT",
            }
            for name, definition in migrations.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, next_run_at, lease_expires_at)")
            conn.execute("""
                UPDATE jobs SET status='failed', error='Legacy job cannot be resumed; the previous version did not persist its input payload.'
                WHERE status IN ('queued', 'processing') AND payload_json IS NULL
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_owner ON jobs(owner_token_hash)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs(idempotency_owner, idempotency_key)")
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
                    filename=?, error=?, updated_at=? WHERE id=? AND lease_owner=?
                    AND lease_expires_at >= ?
            """, (
                job.get("status"), job.get("progress", 0), job.get("output_file"),
                job.get("download_url"), job.get("filename"), job.get("error"),
                time.time(), job.get("id"), job.get("lease_owner"), time.time(),
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

    def _owner_token_for_job(
        self, job_id: str, idempotency_key: Optional[str] = None,
        owner_context: str = "anonymous",
    ) -> str:
        # Bind recoverable idempotency capabilities to the high-entropy caller key
        # and requester context, not only to the job id.
        material = "\\0".join((
            "ovd-job-owner-v2", job_id, idempotency_key or "",
            str(owner_context or "anonymous"),
        ))
        raw = hmac.new(self.owner_secret, material.encode("utf-8"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    @staticmethod
    def _fingerprint(value: Dict[str, Any]) -> str:
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_source_page(source_url: Optional[str]) -> Optional[str]:
        if not source_url:
            return None
        if len(str(source_url)) > 4096:
            raise ValueError("Source URL is too long.")
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
        idempotency_key: Optional[str] = None, owner_context: str = "anonymous",
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
        if safe_source_url and (
            not verify_safe_upstream_url(safe_source_url)
            or not await asyncio.to_thread(verify_public_dns_resolution, safe_source_url)
        ):
            raise ValueError("Source page must resolve only to public IP addresses.")
        if title is not None and len(str(title)) > 120:
            raise ValueError("Job title must be 120 characters or fewer.")
        for token in tokens:
            if not isinstance(token, str) or len(token) > 4096 or token.startswith(("http://", "https://", "/api/")):
                raise ValueError("Only signed download tokens are accepted.")
            payload = verify_download_token(token)
            if not payload or not payload.get("variant_url"):
                raise ValueError("A download token is invalid or expired.")
            media_url = payload["variant_url"]
            parsed_media = urllib.parse.urlsplit(media_url)
            if parsed_media.path == "/api/stream":
                inner_url = urllib.parse.parse_qs(parsed_media.query).get("url", [None])[0]
                if not inner_url:
                    raise ValueError("Download token contains an invalid stream URL.")
                media_url = inner_url
                parsed_media = urllib.parse.urlsplit(media_url)
            if (
                parsed_media.scheme != "https" or not parsed_media.hostname
                or not is_safe_cdn_host(parsed_media.hostname)
                or not verify_safe_upstream_url(media_url)
                or not await asyncio.to_thread(verify_public_dns_resolution, media_url)
            ):
                raise ValueError("Download token does not reference an approved public media CDN.")

        if idempotency_key is not None:
            idempotency_key = str(idempotency_key).strip()
            if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idempotency_key):
                raise ValueError("Idempotency-Key must be 8-128 safe characters.")
        owner_fingerprint = hashlib.sha256(str(owner_context).encode("utf-8")).hexdigest()
        ext = "mp4" if action == "merge" else ("mp3" if action == "mp3" else "zip")
        job_id = str(uuid.uuid4())
        clean = re.sub(r'[\\/*?:"<>|]', "", str(title or "")).strip()
        clean = re.sub(r"\s+", "_", clean)[:60]
        filename = f"{clean}_{job_id[:16]}.{ext}" if clean else f"ovd_{action}_{job_id[:16]}.{ext}"
        now = time.time()
        payload = {"tokens": tokens, "source_url": safe_source_url, "height": height}
        fingerprint = self._fingerprint({
            "action": action, "tokens": tokens, "source_url": safe_source_url,
            "height": height, "title": title or "",
        })
        if idempotency_key:
            with self._connect() as conn:
                existing = conn.execute("""
                    SELECT id, request_fingerprint FROM jobs
                    WHERE idempotency_owner=? AND idempotency_key=?
                """, (owner_fingerprint, idempotency_key)).fetchone()
            if existing:
                if existing["request_fingerprint"] != fingerprint:
                    raise ValueError("Idempotency-Key was already used for a different request.")
                existing_id = existing["id"]
                return existing_id, self._owner_token_for_job(existing_id, idempotency_key, owner_context)

        owner_token = self._owner_token_for_job(job_id, idempotency_key, owner_context)
        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT INTO jobs (
                        id, action, status, progress, output_file, download_url, filename,
                        error, created_at, updated_at, payload_json, owner_token_hash,
                        attempts, max_attempts, next_run_at, cancel_requested,
                        idempotency_key, idempotency_owner, request_fingerprint
                    ) VALUES (?, ?, 'queued', 0, NULL, NULL, ?, NULL, ?, ?, ?, ?, 0, ?, ?, 0, ?, ?, ?)
                """, (
                    job_id, action, filename, now, now, json.dumps(payload, separators=(",", ":")),
                    self._owner_hash(owner_token), self.max_attempts, now,
                    idempotency_key, owner_fingerprint if idempotency_key else None,
                    fingerprint if idempotency_key else None,
                ))
                conn.commit()
        except sqlite3.IntegrityError:
            if not idempotency_key:
                raise
            with self._connect() as conn:
                existing = conn.execute("""
                    SELECT id, request_fingerprint FROM jobs
                    WHERE idempotency_owner=? AND idempotency_key=?
                """, (owner_fingerprint, idempotency_key)).fetchone()
            if not existing or existing["request_fingerprint"] != fingerprint:
                raise ValueError("Idempotency-Key conflicts with another job request.")
            existing_id = existing["id"]
            return existing_id, self._owner_token_for_job(existing_id, idempotency_key, owner_context)
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
            conn.execute("""
                UPDATE jobs SET status='failed', error='Worker lease expired after maximum attempts.',
                    lease_owner=NULL, lease_expires_at=NULL, updated_at=?
                WHERE status='processing' AND lease_expires_at IS NOT NULL
                    AND lease_expires_at < ? AND attempts >= max_attempts
            """, (now, now))
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

    @staticmethod
    def _approved_media_url(url: str) -> bool:
        try:
            parsed = urllib.parse.urlsplit(url)
            return bool(
                parsed.scheme == "https" and parsed.hostname
                and is_safe_cdn_host(parsed.hostname)
                and verify_safe_upstream_url(url)
                and verify_public_dns_resolution(url)
            )
        except Exception:
            return False

    async def _download_media_source(self, source_url: str, destination: str, job_id: str) -> str:
        """Download an approved CDN source to bounded local storage before FFmpeg."""
        max_mb = max(10, min(int(os.environ.get("JOB_MAX_SOURCE_MB", "1024")), 2048))
        max_bytes = max_mb * 1024 * 1024
        temporary = destination + ".part"
        current_url = source_url
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=15.0),
                follow_redirects=False,
            ) as client:
                response = None
                for _ in range(6):
                    if not await asyncio.to_thread(self._approved_media_url, current_url):
                        raise ValueError("Media URL or redirect is not an approved public CDN.")
                    request = client.build_request(
                        "GET", current_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                            "Referer": "https://www.youtube.com/",
                        },
                    )
                    response = await client.send(request, stream=True, follow_redirects=False)
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        await response.aclose()
                        response = None
                        if not location:
                            raise ValueError("Media source returned a redirect without a location.")
                        current_url = urllib.parse.urljoin(current_url, location)
                        continue
                    break
                if response is None:
                    raise ValueError("Media source exceeded the redirect limit.")
                try:
                    response.raise_for_status()
                    declared = int(response.headers.get("content-length", "0") or 0)
                    if declared > max_bytes:
                        raise ValueError(f"Source media exceeds the {max_mb} MB job limit.")
                    written = 0
                    with open(temporary, "wb") as output:
                        async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                            if await asyncio.to_thread(self._is_cancelled, job_id):
                                raise asyncio.CancelledError()
                            written += len(chunk)
                            if written > max_bytes:
                                raise ValueError(f"Source media exceeds the {max_mb} MB job limit.")
                            output.write(chunk)
                    if written == 0:
                        raise ValueError("Source media is empty.")
                finally:
                    await response.aclose()
            os.replace(temporary, destination)
            try:
                os.chmod(destination, 0o600)
            except OSError:
                pass
            return destination
        except BaseException:
            if os.path.exists(temporary):
                try:
                    os.remove(temporary)
                except OSError:
                    pass
            raise

    async def _wait_ffmpeg(self, process, job_id: str):
        communication = asyncio.create_task(process.communicate())
        for _ in range(900):
            if communication.done():
                return await communication
            if await asyncio.to_thread(self._is_cancelled, job_id):
                process.kill()
                await communication
                raise asyncio.CancelledError()
            await asyncio.sleep(1)
        process.kill()
        await communication
        raise RuntimeError("FFmpeg job exceeded the 15-minute execution limit.")

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
                    "download_url", "filename", "error", "created_at", "lease_owner",
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
                        if current and current["status"] in ("processing", "done"):
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

    def get_stats(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS total FROM jobs GROUP BY status"
            ).fetchall()
            totals = {row["status"]: int(row["total"]) for row in rows}
        return {
            "counts": totals,
            "worker_running": bool(self._worker_task and not self._worker_task.done()),
            "lease_seconds": self.lease_seconds,
            "max_attempts": self.max_attempts,
        }

    def _is_cancelled(self, job_id: str) -> bool:
        """Abort processing when cancellation is requested or this worker lost its lease."""
        now = time.time()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT cancel_requested, status, lease_owner, lease_expires_at FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
        return bool(
            not row
            or row["cancel_requested"]
            or row["status"] != "processing"
            or row["lease_owner"] != self.worker_id
            or row["lease_expires_at"] is None
            or row["lease_expires_at"] < now
        )

    async def _process_job(self, job_id: str, tokens: List[str], action: str, source_url: Optional[str] = None, height: int = 1080):
        source_files = []
        job = self.jobs.get(job_id)
        if not job:
            return

        job["status"] = "processing"
        job["progress"] = 15
        self._save_job_db(job)
        ffmpeg_bin = shutil.which("ffmpeg")

        try:
            if self._is_cancelled(job_id):
                raise asyncio.CancelledError()
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
                            if self._is_cancelled(job_id):
                                raise asyncio.CancelledError()
                            parsed_result = urllib.parse.urlsplit(worker_url)
                            if parsed_result.scheme != "https" or not parsed_result.hostname or parsed_result.username or parsed_result.password:
                                raise RuntimeError("Worker returned an invalid result URL.")
                            job["download_url"] = worker_url
                            job["status"] = "done"
                            job["progress"] = 100
                            self._save_job_db(job)
                            return
                    except Exception as we:
                        print(f"[job_manager] worker delegation failed, falling back to local task: {we}", flush=True)


            # Verify tokens only through the security module; do not decode unsigned payloads.
            sources = []
            for t in tokens:
                payload = verify_download_token(t)
                if not payload:
                    raise ValueError("Invalid or expired download token.")
                media_url = payload["variant_url"]
                parsed_media = urllib.parse.urlsplit(media_url)
                if parsed_media.path == "/api/stream":
                    media_url = urllib.parse.parse_qs(parsed_media.query).get("url", [None])[0] or ""
                parsed_media = urllib.parse.urlsplit(media_url)
                if (
                    parsed_media.scheme != "https" or not parsed_media.hostname
                    or not is_safe_cdn_host(parsed_media.hostname)
                    or not verify_safe_upstream_url(media_url)
                    or not await asyncio.to_thread(verify_public_dns_resolution, media_url)
                ):
                    raise ValueError("Media source URL is no longer an approved public CDN.")
                sources.append(media_url)

            if action in ("merge", "mp3"):
                local_sources = []
                for index, source in enumerate(sources):
                    if self._is_cancelled(job_id):
                        raise asyncio.CancelledError()
                    local_path = os.path.join(JOBS_DIR, f".{job_id}_input_{index + 1}.media")
                    local_sources.append(await self._download_media_source(source, local_path, job_id))
                    source_files.append(local_path)
                    job["progress"] = 75 + int(5 * (index + 1) / len(sources))
                    self._save_job_db(job)

                sources = local_sources

            if self._is_cancelled(job_id):
                raise asyncio.CancelledError()
            job["progress"] = 82
            self._save_job_db(job)
            output_path = os.path.join(JOBS_DIR, job["filename"])
            # FFmpeg processes only local bounded files; no remote protocol is enabled.
            ua_args = ["-protocol_whitelist", "file,pipe"]
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
                stdout, stderr = await self._wait_ffmpeg(proc, job_id)
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
                await self._wait_ffmpeg(proc, job_id)
                if proc.returncode != 0:
                    raise RuntimeError("ffmpeg mp3 conversion failed.")

            elif action == "zip":
                job["filename"] = f"ovd_gallery_{job_id[:16]}.zip"
                output_path = os.path.join(JOBS_DIR, job["filename"])
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
                        total_bytes = 0
                        for idx, src in enumerate(sources):
                            if self._is_cancelled(job_id):
                                raise asyncio.CancelledError()
                            current_url = src
                            response = None
                            for _redirect in range(6):
                                if not await asyncio.to_thread(
                                    lambda u=current_url: (
                                        urllib.parse.urlsplit(u).scheme == "https"
                                        and bool(urllib.parse.urlsplit(u).hostname)
                                        and is_safe_cdn_host(urllib.parse.urlsplit(u).hostname)
                                        and verify_safe_upstream_url(u)
                                        and verify_public_dns_resolution(u)
                                    )
                                ):
                                    raise ValueError("ZIP source or redirect is not an approved public CDN.")
                                request = client.build_request("GET", current_url, headers={"User-Agent": "Mozilla/5.0"})
                                response = await client.send(request, stream=True, follow_redirects=False)
                                if response.status_code in (301, 302, 303, 307, 308):
                                    location = response.headers.get("location")
                                    await response.aclose()
                                    if not location:
                                        raise ValueError("ZIP source returned an invalid redirect.")
                                    current_url = urllib.parse.urljoin(current_url, location)
                                    response = None
                                    continue
                                break
                            if response is None:
                                raise ValueError("ZIP source exceeded the redirect limit.")
                            try:
                                response.raise_for_status()
                                declared = int(response.headers.get("content-length", "0") or 0)
                                if declared > 50 * 1024 * 1024:
                                    raise ValueError("ZIP item exceeds the 50 MB limit.")
                                parts = []
                                item_bytes = 0
                                async for chunk in response.aiter_bytes():
                                    item_bytes += len(chunk)
                                    total_bytes += len(chunk)
                                    if item_bytes > 50 * 1024 * 1024 or total_bytes > 300 * 1024 * 1024:
                                        raise ValueError("ZIP archive exceeded its size limit.")
                                    parts.append(chunk)
                                ext = "png" if urllib.parse.urlsplit(current_url).path.lower().endswith(".png") else "jpg"
                                zf.writestr(f"media_{idx+1}.{ext}", b"".join(parts))
                            finally:
                                await response.aclose()
                            job["progress"] = int(25 + (70 * (idx + 1) / len(sources)))
                            self._save_job_db(job)

            if self._is_cancelled(job_id):
                raise asyncio.CancelledError()
            job["output_file"] = output_path
            job["status"] = "done"
            job["progress"] = 100
            job["download_url"] = f"/api/jobs/{job_id}/file"
            self._save_job_db(job)
            if job.get("output_file") and os.path.isfile(job["output_file"]):
                try:
                    os.chmod(job["output_file"], 0o600)
                except OSError:
                    pass

        except Exception as e:
            job["error"] = str(e)[:500]
            self._save_job_db(job)
            raise
        finally:
            for source_file in source_files:
                try:
                    if os.path.isfile(source_file):
                        os.remove(source_file)
                except OSError:
                    pass

    async def _cleanup_loop(self):
        """Delete expired terminal jobs; queued and leased work remains durable."""
        while True:
            await asyncio.sleep(600)
            cutoff = time.time() - 7200
            try:
                with self._connect() as conn:
                    rows = conn.execute("""
                        SELECT id, output_file, filename FROM jobs
                        WHERE created_at < ? AND status IN ('done', 'failed', 'cancelled')
                    """, (cutoff,)).fetchall()
                    for row in rows:
                        path = row["output_file"]
                        candidates = [path, os.path.join(JOBS_DIR, row["filename"] or "")]
                        for candidate in candidates:
                            if not candidate:
                                continue
                            try:
                                if os.path.basename(candidate) == os.path.basename(os.path.normpath(candidate)) and os.path.commonpath((os.path.realpath(JOBS_DIR), os.path.realpath(candidate))) == os.path.realpath(JOBS_DIR) and os.path.isfile(candidate):
                                    os.remove(candidate)
                            except (OSError, ValueError):
                                pass
                    conn.execute("""
                        DELETE FROM jobs WHERE created_at < ?
                        AND status IN ('done', 'failed', 'cancelled')
                    """, (cutoff,))
                    conn.commit()
                    # Remove abandoned partial inputs and output temp files left by a crashed process.
                    for name in os.listdir(JOBS_DIR):
                        path = os.path.join(JOBS_DIR, name)
                        if name.endswith(".part") or (name.startswith(".") and "_input_" in name and name.endswith(".media")):
                            try:
                                if os.path.isfile(path) and os.path.getmtime(path) < time.time() - 1800:
                                    os.remove(path)
                            except OSError:
                                pass
            except Exception as exc:
                print(f"[job_manager] cleanup error: {type(exc).__name__}", flush=True)


job_manager = JobManager()
