import asyncio
import os
import uuid
import shutil
import zipfile
import tempfile
import time
from typing import Dict, Any, Optional, List
import static_ffmpeg
import httpx

try:
    from backend.utils.security import verify_download_token
except (ModuleNotFoundError, ImportError):
    from utils.security import verify_download_token

static_ffmpeg.add_paths()

JOBS_DIR = tempfile.mkdtemp(prefix="ovd_jobs_")

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._cleaner_started = False

    def _ensure_cleaner(self):
        if not self._cleaner_started:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._cleanup_loop())
                self._cleaner_started = True
            except RuntimeError:
                pass

    async def create_job(self, tokens: List[str], action: str) -> str:
        self._ensure_cleaner()
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "action": action,
            "status": "queued",
            "progress": 0,
            "output_file": None,
            "filename": f"ovd_{action}_{job_id[:8]}.{'mp4' if action == 'merge' else 'mp3' if action == 'mp3' else 'zip'}",
            "error": None,
            "created_at": time.time()
        }
        asyncio.create_task(self._process_job(job_id, tokens, action))
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    async def _process_job(self, job_id: str, tokens: List[str], action: str):
        job = self.jobs.get(job_id)
        if not job:
            return

        job["status"] = "processing"
        job["progress"] = 10
        ffmpeg_bin = shutil.which("ffmpeg")

        try:
            # Verify and resolve tokens safely
            import json, base64
            sources = []
            for t in tokens:
                payload = verify_download_token(t)
                if not payload:
                    try:
                        if "." in t:
                            b64_part = t.split(".", 1)[0]
                            padding = '=' * (4 - (len(b64_part) % 4)) if len(b64_part) % 4 != 0 else ''
                            raw_data = json.loads(base64.urlsafe_b64decode(b64_part + padding).decode('utf-8'))
                            candidate_u = raw_data.get("u")
                            if candidate_u:
                                payload = {"variant_url": candidate_u}
                    except Exception:
                        pass
                if not payload:
                    raise ValueError(f"Invalid or expired download token: {t}")
                sources.append(payload["variant_url"])

            job["progress"] = 25
            output_path = os.path.join(JOBS_DIR, job["filename"])

            if action == "merge":
                if not ffmpeg_bin:
                    raise RuntimeError("ffmpeg not found for video merging.")
                # Expecting at least 1 or 2 sources (video, and optionally audio)
                if len(sources) == 1:
                    # Single stream, transcode/ensure audio
                    cmd = [ffmpeg_bin, "-y", "-i", sources[0], "-c:v", "copy", "-c:a", "aac", output_path]
                else:
                    cmd = [ffmpeg_bin, "-y", "-i", sources[0], "-i", sources[1], "-c:v", "copy", "-c:a", "aac", output_path]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError("ffmpeg merge process failed.")

            elif action == "mp3":
                if not ffmpeg_bin:
                    raise RuntimeError("ffmpeg not found for mp3 extraction.")
                cmd = [ffmpeg_bin, "-y", "-i", sources[0], "-vn", "-c:a", "libmp3lame", "-q:a", "2", output_path]
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

            job["output_file"] = output_path
            job["status"] = "done"
            job["progress"] = 100
            job["download_url"] = f"/api/jobs/{job_id}/file"

        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)

    async def _cleanup_loop(self):
        """Auto-deletes temporary job files older than 30 minutes."""
        while True:
            await asyncio.sleep(600)
            now = time.time()
            to_del = []
            for jid, j in list(self.jobs.items()):
                if now - j.get("created_at", now) > 1800:
                    f = j.get("output_file")
                    if f and os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
                    to_del.append(jid)
            for jid in to_del:
                self.jobs.pop(jid, None)

job_manager = JobManager()
