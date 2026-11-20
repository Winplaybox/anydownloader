"""AutoClip workers.

Inline (default, AUTOCLIP_WORKER_MODE=inline): started by the API on boot, renders inside the API process.

Remote (AUTOCLIP_WORKER_MODE=remote on the API): run this on workers.winplaybox.in / any PC / GPU box:

    AUTOCLIP_API_BASE=https://api.winplaybox.in AUTOCLIP_WORKER_KEY=... GEMINI_API_KEY=... \
        python -m backend.autoclip.worker

The remote worker claims jobs over HTTPS (/api/autoclip/workers/*), downloads links itself (its own IP,
which matters for YouTube), renders, and uploads the clips back. Lease + heartbeat fencing means
any number of workers can run; a crashed worker's job is requeued automatically.
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket
import tempfile
import time
import uuid
from typing import Any, Dict, List, Optional

from . import byo, config, pipeline, store

log = logging.getLogger("autoclip.worker")


def _worker_id(prefix: str) -> str:
    return f"{prefix}:{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"


# --------------------------------------------------------------------------- #
# Inline worker (inside the API)
# --------------------------------------------------------------------------- #

class InlineWorker:
    def __init__(self) -> None:
        self.tasks: List[asyncio.Task] = []
        self.ids = [_worker_id("inline") for _ in range(config.INLINE_CONCURRENCY)]
        self.last_cleanup = 0.0
        self.busy = 0

    def start(self) -> None:
        if self.tasks or not config.ENABLED:
            return
        loop = asyncio.get_running_loop()
        self.tasks.append(loop.create_task(self._housekeeping()))
        if config.WORKER_MODE == "inline":
            for wid in self.ids:
                self.tasks.append(loop.create_task(self._loop(wid)))
            log.info("autoclip inline worker x%d started", len(self.ids))

    async def _housekeeping(self) -> None:
        while True:
            try:
                n = await asyncio.to_thread(store.cleanup)
                if n:
                    log.info("autoclip cleanup removed %d jobs", n)
            except Exception:
                log.exception("autoclip cleanup failed")
            await asyncio.sleep(1800)

    async def _loop(self, wid: str) -> None:
        while True:
            try:
                job = await asyncio.to_thread(store.claim, wid)
            except Exception:
                log.exception("autoclip claim failed")
                job = None
            if not job:
                await asyncio.sleep(3)
                continue
            self.busy += 1
            try:
                await self._process(job, wid)
            finally:
                self.busy -= 1

    async def _process(self, job: Dict[str, Any], wid: str) -> None:
        job_id = job["id"]
        workdir = store.job_dir(job_id)

        async def report(stage: str, progress: int, meta: Dict[str, Any]) -> bool:
            r = await asyncio.to_thread(store.heartbeat, job_id, wid, stage=stage, progress=progress,
                                        title=meta.get("title"), duration=meta.get("duration"))
            return r["ok"] and not r["cancel"]

        try:
            result = await pipeline.run(job, workdir, report, source_path=store.source_path(job_id))
            await asyncio.to_thread(store.complete, job_id, wid, _strip(result))
        except pipeline.Cancelled:
            await asyncio.to_thread(store.fail, job_id, wid, "cancelled", cancelled=True)
        except Exception as e:  # noqa: BLE001
            log.exception("autoclip job %s failed", job_id)
            await asyncio.to_thread(store.fail, job_id, wid, pipeline.friendly(e), retry=pipeline.retryable(e))
        finally:
            j = await asyncio.to_thread(store.get, job_id)
            if not j or j.get("status") in ("done", "failed", "cancelled"):
                byo.drop(job_id)  # the user's key never outlives its job

    def status(self) -> Dict[str, Any]:
        return {"mode": config.WORKER_MODE, "inline_workers": len(self.ids) if config.WORKER_MODE == "inline" else 0,
                "busy": self.busy, "running": any(not t.done() for t in self.tasks)}


def _strip(result: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the DB row small: transcript text per clip is capped already, drop nothing else."""
    return result


inline_worker = InlineWorker()


# --------------------------------------------------------------------------- #
# Remote worker (CLI)
# --------------------------------------------------------------------------- #

class RemoteWorker:
    def __init__(self, base: str, key: str) -> None:
        import httpx

        self.base = base.rstrip("/") + "/api/autoclip/workers"
        self.wid = _worker_id("remote")
        self.http = httpx.AsyncClient(headers={"X-Worker-Key": key, "User-Agent": "autoclip-worker/1"},
                                      timeout=httpx.Timeout(60.0, connect=10.0))
        self.stop = False

    async def _post(self, path: str, **kw: Any):
        for attempt in range(4):
            try:
                r = await self.http.post(self.base + path, **kw)
                if r.status_code >= 500:
                    raise RuntimeError(f"HTTP {r.status_code}")
                return r
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    raise
                log.warning("worker POST %s failed (%s), retrying", path, e)
                await asyncio.sleep(2 ** attempt)

    async def run_forever(self) -> None:
        log.info("autoclip remote worker %s -> %s", self.wid, self.base)
        idle = 2.0
        while not self.stop:
            try:
                r = await self._post("/claim", json={"worker_id": self.wid})
                if r.status_code == 204:
                    await asyncio.sleep(idle)
                    idle = min(15.0, idle * 1.5)
                    continue
                r.raise_for_status()
                idle = 2.0
                await self.process(r.json()["job"])
            except Exception as e:  # noqa: BLE001
                log.warning("worker loop error: %s", e)
                await asyncio.sleep(10)

    async def process(self, job: Dict[str, Any]) -> None:
        job_id = job["id"]
        with tempfile.TemporaryDirectory(prefix=f"autoclip_{job_id[:8]}_") as work:
            src_path = None
            try:
                if job["source_kind"] == "upload":
                    src_path = os.path.join(work, "source" + (job.get("source_ext") or ".mp4"))
                    async with self.http.stream("GET", f"{self.base}/jobs/{job_id}/source",
                                                params={"worker_id": self.wid}, timeout=None) as resp:
                        resp.raise_for_status()
                        with open(src_path, "wb") as f:
                            async for chunk in resp.aiter_bytes(1 << 20):
                                f.write(chunk)

                async def report(stage: str, progress: int, meta: Dict[str, Any]) -> bool:
                    try:
                        r = await self._post(f"/jobs/{job_id}/heartbeat", json={
                            "worker_id": self.wid, "stage": stage, "progress": progress,
                            "title": meta.get("title"), "duration": meta.get("duration")})
                        d = r.json()
                        return bool(d.get("ok")) and not d.get("cancel")
                    except Exception:  # transient network blip: keep going, lease covers us
                        return True

                result = await pipeline.run(job, work, report, source_path=src_path)
                out_dir = os.path.join(work, "clips")
                for name in sorted(os.listdir(out_dir)):
                    if not store.valid_artifact(name):
                        continue
                    with open(os.path.join(out_dir, name), "rb") as f:
                        data = f.read()
                    r = await self._post(f"/jobs/{job_id}/artifact", params={"worker_id": self.wid, "name": name},
                                         content=data, headers={"Content-Type": "application/octet-stream"},
                                         timeout=600)
                    r.raise_for_status()
                r = await self._post(f"/jobs/{job_id}/complete", json={"worker_id": self.wid, "result": result})
                r.raise_for_status()
                log.info("job %s done: %d clips", job_id, len(result["clips"]))
            except pipeline.Cancelled:
                await self._post(f"/jobs/{job_id}/fail", json={"worker_id": self.wid, "error": "cancelled",
                                                                 "cancelled": True})
            except Exception as e:  # noqa: BLE001
                log.exception("job %s failed", job_id)
                try:
                    await self._post(f"/jobs/{job_id}/fail", json={
                        "worker_id": self.wid, "error": pipeline.friendly(e), "retry": pipeline.retryable(e)})
                except Exception:
                    pass


async def _main() -> None:
    base = os.environ.get("AUTOCLIP_API_BASE", "").strip()
    key = config.WORKER_KEY
    if not base or len(key) < 32:
        raise SystemExit("Set AUTOCLIP_API_BASE and AUTOCLIP_WORKER_KEY (32+ chars).")
    w = RemoteWorker(base, key)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: setattr(w, "stop", True))
        except NotImplementedError:  # Windows
            pass
    try:
        from . import speech
        if speech.available():
            await asyncio.to_thread(speech._model)  # warm the model before the first job
    except Exception:
        pass
    await w.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(_main())
