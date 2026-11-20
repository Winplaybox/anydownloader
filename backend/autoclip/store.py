"""SQLite job store with leases + fencing. One DB file, owned only by AutoClip.

States: queued -> running -> done | failed | cancelled
A running job holds a lease (owner, until). Heartbeats extend it. An expired lease is requeued
(up to MAX_ATTEMPTS) so a crashed worker never strands a job. Every write from a worker is fenced
by lease_owner so a stale worker cannot overwrite a newer attempt.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from . import config

_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_ART_RE = re.compile(r"^clip_\d{2}\.(mp4|jpg|srt)$|^clips\.json$")
_lock = threading.Lock()
_ready = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  created REAL NOT NULL,
  updated REAL NOT NULL,
  status TEXT NOT NULL,
  stage TEXT NOT NULL DEFAULT 'queued',
  progress INTEGER NOT NULL DEFAULT 0,
  source_kind TEXT NOT NULL,
  source_url TEXT,
  source_name TEXT,
  settings TEXT NOT NULL,
  client TEXT NOT NULL,
  title TEXT,
  duration REAL,
  error TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  lease_owner TEXT,
  lease_until REAL NOT NULL DEFAULT 0,
  cancel INTEGER NOT NULL DEFAULT 0,
  result TEXT
);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status, created);
CREATE INDEX IF NOT EXISTS jobs_client ON jobs(client, created);
"""


def valid_id(job_id: str) -> bool:
    return bool(_ID_RE.match(job_id or ""))


def valid_artifact(name: str) -> bool:
    return bool(_ART_RE.match(name or ""))


def job_dir(job_id: str) -> str:
    if not valid_id(job_id):
        raise ValueError("bad job id")
    return os.path.join(config.DATA_DIR, "jobs", job_id)


def clips_dir(job_id: str) -> str:
    return os.path.join(job_dir(job_id), "clips")


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    global _ready
    if not _ready:
        with _lock:
            if not _ready:
                os.makedirs(os.path.join(config.DATA_DIR, "jobs"), exist_ok=True)
                c = sqlite3.connect(config.DB_PATH, timeout=30)
                c.execute("PRAGMA journal_mode=WAL")
                c.executescript(SCHEMA)
                c.close()
                _ready = True
    c = sqlite3.connect(config.DB_PATH, timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    try:
        yield c
    finally:
        c.close()


def _row(r: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if r is None:
        return None
    d = dict(r)
    d["settings"] = json.loads(d.get("settings") or "{}")
    d["result"] = json.loads(d["result"]) if d.get("result") else None
    return d


# --------------------------------------------------------------------------- #
# Access tokens
# --------------------------------------------------------------------------- #

def _secret() -> bytes:
    s = config.SECRET
    if not s:
        # Dev only: a per-process random secret (tokens die on restart). Production sets JOB_OWNER_SECRET.
        s = os.environ.setdefault("_AUTOCLIP_EPHEMERAL_SECRET", uuid.uuid4().hex + uuid.uuid4().hex)
    return s.encode()


def job_token(job_id: str) -> str:
    return hmac.new(_secret(), f"autoclip:{job_id}".encode(), hashlib.sha256).hexdigest()[:40]


def token_ok(job_id: str, token: str) -> bool:
    return bool(token) and valid_id(job_id) and hmac.compare_digest(job_token(job_id), token.strip())


# --------------------------------------------------------------------------- #
# Client side
# --------------------------------------------------------------------------- #

def create(*, source_kind: str, source_url: Optional[str], source_name: Optional[str],
           settings: Dict[str, Any], client: str, status: str = "queued") -> Dict[str, Any]:
    """status='uploading' keeps workers off the job until mark_queued() (file fully written)."""
    job_id = uuid.uuid4().hex
    now = time.time()
    os.makedirs(clips_dir(job_id), exist_ok=True)
    with _conn() as c:
        c.execute("INSERT INTO jobs(id,created,updated,status,stage,source_kind,source_url,source_name,settings,client)"
                  " VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (job_id, now, now, status, status, source_kind, source_url, source_name,
                   json.dumps(settings), client))
    return get(job_id)  # type: ignore[return-value]


def get(job_id: str) -> Optional[Dict[str, Any]]:
    if not valid_id(job_id):
        return None
    with _conn() as c:
        return _row(c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())


def mark_queued(job_id: str) -> None:
    with _conn() as c:
        c.execute("UPDATE jobs SET status='queued', stage='queued', updated=? WHERE id=? AND status='uploading'",
                  (time.time(), job_id))


def queue_position(job: Dict[str, Any]) -> int:
    if job["status"] != "queued":
        return 0
    with _conn() as c:
        n = c.execute("SELECT COUNT(*) FROM jobs WHERE status='queued' AND created<?", (job["created"],)).fetchone()[0]
    return int(n) + 1


def queued_count() -> int:
    with _conn() as c:
        return int(c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0])


def request_cancel(job_id: str) -> Optional[Dict[str, Any]]:
    now = time.time()
    with _conn() as c:
        c.execute("UPDATE jobs SET status='cancelled', stage='cancelled', updated=?, lease_owner=NULL, lease_until=0"
                   " WHERE id=? AND status IN ('queued','uploading')", (now, job_id))
        c.execute("UPDATE jobs SET cancel=1, updated=? WHERE id=? AND status='running'", (now, job_id))
    return get(job_id)


def public(job: Dict[str, Any]) -> Dict[str, Any]:
    res = job.get("result") or {}
    return {
        "id": job["id"], "status": job["status"], "stage": job["stage"], "progress": job["progress"],
        "created": job["created"], "updated": job["updated"], "title": job.get("title"),
        "duration": job.get("duration"), "error": job.get("error"), "settings": job["settings"],
        "source": {"kind": job["source_kind"], "url": job.get("source_url"), "name": job.get("source_name")},
        "queue_position": queue_position(job), "clips": res.get("clips", []), "engine": res.get("engine"),
        "expires_at": job["created"] + config.RETENTION_HOURS * 3600,
    }


# --------------------------------------------------------------------------- #
# Worker side (lease + fencing)
# --------------------------------------------------------------------------- #

def claim(worker_id: str) -> Optional[Dict[str, Any]]:
    """Atomically take the oldest queued job (or an expired lease)."""
    now = time.time()
    with _conn() as c:
        c.execute("BEGIN IMMEDIATE")
        try:
            # recover expired leases first
            for r in c.execute("SELECT id, attempts FROM jobs WHERE status='running' AND lease_until<?", (now,)).fetchall():
                if r["attempts"] >= config.MAX_ATTEMPTS:
                    c.execute("UPDATE jobs SET status='failed', stage='failed', error=?, updated=?, lease_owner=NULL"
                              " WHERE id=?", ("Worker stopped responding. Please try again.", now, r["id"]))
                else:
                    c.execute("UPDATE jobs SET status='queued', stage='queued', updated=?, lease_owner=NULL, lease_until=0"
                              " WHERE id=?", (now, r["id"]))
            r = c.execute("SELECT id FROM jobs WHERE status='queued' AND cancel=0 ORDER BY created LIMIT 1").fetchone()
            if not r:
                c.execute("COMMIT")
                return None
            c.execute("UPDATE jobs SET status='running', stage='starting', progress=1, attempts=attempts+1,"
                      " lease_owner=?, lease_until=?, updated=?, error=NULL WHERE id=?",
                      (worker_id, now + config.LEASE_SECONDS, now, r["id"]))
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise
    return get(r["id"])


def heartbeat(job_id: str, worker_id: str, *, stage: Optional[str] = None, progress: Optional[int] = None,
              title: Optional[str] = None, duration: Optional[float] = None) -> Dict[str, Any]:
    """Extend the lease. Returns {ok, cancel}. ok=False means this worker lost the job: stop now."""
    now = time.time()
    sets, args = ["lease_until=?", "updated=?"], [now + config.LEASE_SECONDS, now]
    if stage:
        sets.append("stage=?"); args.append(stage[:40])
    if progress is not None:
        sets.append("progress=?"); args.append(max(0, min(99, int(progress))))
    if title:
        sets.append("title=?"); args.append(title[:300])
    if duration:
        sets.append("duration=?"); args.append(float(duration))
    with _conn() as c:
        cur = c.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id=? AND status='running' AND lease_owner=?",
                        (*args, job_id, worker_id))
        if cur.rowcount != 1:
            return {"ok": False, "cancel": True}
        cancel = c.execute("SELECT cancel FROM jobs WHERE id=?", (job_id,)).fetchone()[0]
    return {"ok": True, "cancel": bool(cancel)}


def complete(job_id: str, worker_id: str, result: Dict[str, Any]) -> bool:
    now = time.time()
    with _conn() as c:
        cur = c.execute("UPDATE jobs SET status='done', stage='done', progress=100, result=?, updated=?,"
                        " lease_owner=NULL, lease_until=0 WHERE id=? AND status='running' AND lease_owner=?",
                        (json.dumps(result), now, job_id, worker_id))
        return cur.rowcount == 1


def fail(job_id: str, worker_id: str, error: str, *, retry: bool = False, cancelled: bool = False) -> bool:
    now = time.time()
    with _conn() as c:
        row = c.execute("SELECT attempts, cancel FROM jobs WHERE id=? AND status='running' AND lease_owner=?",
                        (job_id, worker_id)).fetchone()
        if not row:
            return False
        if cancelled or row["cancel"]:
            st, err = "cancelled", None
        elif retry and row["attempts"] < config.MAX_ATTEMPTS:
            st, err = "queued", None
        else:
            st, err = "failed", (error or "Processing failed.")[:500]
        c.execute("UPDATE jobs SET status=?, stage=?, error=?, updated=?, lease_owner=NULL, lease_until=0 WHERE id=?",
                  (st, st, err, now, job_id))
    return True


# --------------------------------------------------------------------------- #
# Housekeeping
# --------------------------------------------------------------------------- #

def cleanup() -> int:
    """Delete jobs + files past retention. Returns rows removed."""
    cutoff = time.time() - config.RETENTION_HOURS * 3600
    with _conn() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM jobs WHERE (created<? AND status!='running') OR (status='uploading' AND created<?)", (cutoff, time.time() - 3 * 3600)).fetchall()]
        for job_id in ids:
            shutil.rmtree(job_dir(job_id), ignore_errors=True)
            c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    # Source files are only needed while processing; drop them from finished jobs early.
    with _conn() as c:
        for r in c.execute("SELECT id FROM jobs WHERE status IN ('done','failed','cancelled')").fetchall():
            d = job_dir(r["id"])
            for name in os.listdir(d) if os.path.isdir(d) else []:
                if name.startswith("source") or name in ("audio16k.wav",) or name.startswith("work"):
                    p = os.path.join(d, name)
                    shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else _unlink(p)
    return len(ids)


def _unlink(p: str) -> None:
    try:
        os.unlink(p)
    except OSError:
        pass


def source_path(job_id: str) -> Optional[str]:
    d = job_dir(job_id)
    if not os.path.isdir(d):
        return None
    for name in sorted(os.listdir(d)):
        if name.startswith("source.") and os.path.isfile(os.path.join(d, name)):
            return os.path.join(d, name)
    return None


def stats() -> Dict[str, int]:
    with _conn() as c:
        rows = c.execute("SELECT status, COUNT(*) n FROM jobs GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


def list_artifacts(job_id: str) -> List[str]:
    d = clips_dir(job_id)
    return sorted(n for n in os.listdir(d) if valid_artifact(n)) if os.path.isdir(d) else []
