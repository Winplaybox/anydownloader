"""OVD AI Video Editor render worker.

Runs as its own container (`python -m backend.editor_worker`), separate from the API, and pulls
job ids from Redis. Heavy work (FFmpeg, Whisper, Kokoro) therefore never blocks API requests.

Reliability:
- A job id moves atomically from the queue to a processing list (BLMOVE) and holds a lease key
  that the worker refreshes. If a worker dies, the lease expires and the reaper requeues the job
  (bounded attempts) or fails it.
- Failed jobs are refunded from the billing info stored on the job; refunds are idempotent in the
  ledger, so a retry or a second reaper can never refund twice.
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket
import time
import uuid
from typing import Any, Dict

try:
    from backend.services import auth_service
    from backend.services.video_editor import pipeline
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services import auth_service  # type: ignore
    from services.video_editor import pipeline  # type: ignore

log = logging.getLogger("wpb.editor_worker")

CONCURRENCY = max(1, int(os.environ.get("EDITOR_CONCURRENCY", "1")))
LEASE_SECONDS = max(30, int(os.environ.get("EDITOR_LEASE_SECONDS", "120")))
MAX_ATTEMPTS = max(1, int(os.environ.get("EDITOR_MAX_ATTEMPTS", "2")))
JOB_TIMEOUT_SECONDS = max(60, int(os.environ.get("EDITOR_JOB_TIMEOUT_SECONDS", "1800")))
WORKER_ID = os.environ.get("EDITOR_WORKER_ID") or f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"


def settle(job: Dict[str, Any]) -> None:
    """Refund the job's debit if it failed. Safe to call any number of times."""
    if job.get("status") != "failed":
        return
    billing = job.get("billing") or {}
    entity_type, entity_id, cost = billing.get("entity_type"), billing.get("entity_id"), int(billing.get("cost") or 0)
    if not entity_id or cost <= 0:
        return
    identity = {"authenticated": True, "user_id": entity_id} if entity_type == "user" else {"is_guest": True, "guest_id": entity_id}
    if auth_service.refund_credit_for_job(identity, amount=cost, job_id=job["id"], reason="Render failed"):
        log.info("refunded %s credits for failed job %s", cost, job["id"])


def fail_job(job: Dict[str, Any], message: str) -> None:
    pipeline._update(job, status="failed", error=message)
    settle(job)


async def _heartbeat(r, job_id: str) -> None:
    key = pipeline.LEASE_PREFIX + job_id
    while True:
        await asyncio.sleep(LEASE_SECONDS / 3)
        await asyncio.to_thread(r.set, key, WORKER_ID, ex=LEASE_SECONDS)


async def run_job(r, job_id: str) -> None:
    lease_key = pipeline.LEASE_PREFIX + job_id
    await asyncio.to_thread(r.set, lease_key, WORKER_ID, ex=LEASE_SECONDS)
    hb = asyncio.create_task(_heartbeat(r, job_id))
    try:
        job = pipeline.load_job(job_id)
        if not job or job.get("status") in ("done", "failed", "cancelled"):
            return
        src = job.get("source_path") or ""
        if not src or not os.path.exists(src):
            fail_job(job, "The uploaded video is no longer available. Your credits were refunded.")
            return
        job["attempts"] = int(job.get("attempts") or 0) + 1
        job["worker"] = WORKER_ID
        pipeline.save_job(job)

        async def on_finish(j: Dict[str, Any]) -> None:
            settle(j)

        try:
            await asyncio.wait_for(pipeline._run(job, src, on_finish), timeout=JOB_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            fail_job(job, "Rendering took too long and was stopped. Your credits were refunded.")
    except Exception:
        log.exception("worker crashed on job %s", job_id)
        job = pipeline.load_job(job_id)
        if job and job.get("status") not in ("done", "failed"):
            fail_job(job, "Unexpected server error. Your credits were refunded.")
    finally:
        hb.cancel()
        await asyncio.to_thread(r.lrem, pipeline.PROCESSING_KEY, 0, job_id)
        await asyncio.to_thread(r.delete, lease_key)


def reap_orphans(r) -> int:
    """Requeue (or fail) jobs whose worker died: in the processing list but without a live lease."""
    n = 0
    for job_id in r.lrange(pipeline.PROCESSING_KEY, 0, -1):
        if r.exists(pipeline.LEASE_PREFIX + job_id):
            continue
        # Claim the orphan: only one reaper wins the LREM.
        if not r.lrem(pipeline.PROCESSING_KEY, 1, job_id):
            continue
        job = pipeline.load_job(job_id)
        if not job or job.get("status") in ("done", "failed", "cancelled"):
            continue
        if int(job.get("attempts") or 0) < MAX_ATTEMPTS and os.path.exists(job.get("source_path") or ""):
            pipeline._update(job, status="queued", stage="queued", stage_label="Waiting in queue", progress=0)
            r.rpush(pipeline.QUEUE_KEY, job_id)  # back of the list = next to be taken
            log.warning("requeued orphaned job %s (attempt %s)", job_id, job.get("attempts"))
        else:
            fail_job(job, "Rendering was interrupted. Your credits were refunded.")
            log.warning("failed orphaned job %s after %s attempts", job_id, job.get("attempts"))
        n += 1
    return n


async def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if pipeline.queue_mode() != "redis":
        raise SystemExit("editor_worker requires EDITOR_QUEUE=redis")
    r = pipeline.redis_client()
    r.ping()
    pipeline._sem = asyncio.Semaphore(CONCURRENCY)
    pipeline._ensure_cleaner()
    slots = asyncio.Semaphore(CONCURRENCY)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # pragma: no cover
            pass

    async def reaper() -> None:
        while not stop.is_set():
            try:
                await asyncio.to_thread(reap_orphans, r)
            except Exception:
                log.exception("reaper error")
            await asyncio.sleep(max(15, LEASE_SECONDS // 2))

    reaper_task = asyncio.create_task(reaper())
    running: set = set()
    log.info("editor worker %s started (concurrency=%s)", WORKER_ID, CONCURRENCY)
    while not stop.is_set():
        await slots.acquire()
        try:
            job_id = await asyncio.to_thread(r.blmove, pipeline.QUEUE_KEY, pipeline.PROCESSING_KEY, 5, "RIGHT", "LEFT")
        except Exception:
            slots.release()
            log.exception("queue read failed")
            await asyncio.sleep(3)
            continue
        if not job_id:
            slots.release()
            continue

        async def _one(jid: str) -> None:
            try:
                await run_job(r, jid)
            finally:
                slots.release()

        t = asyncio.create_task(_one(job_id))
        running.add(t)
        t.add_done_callback(running.discard)

    log.info("stopping: waiting for %s running job(s)", len(running))
    reaper_task.cancel()
    if running:
        await asyncio.wait(running, timeout=60)


if __name__ == "__main__":
    asyncio.run(main())
