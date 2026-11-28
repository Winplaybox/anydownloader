# OVD API + render worker image (same image, different command).
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates nodejs unzip tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt requirements.txt
# The pip "deno" package ships the Deno binary used by yt-dlp's EJS challenge solver.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && python -c "import shutil,sys; sys.exit(0 if shutil.which('deno') else 'deno missing')"

COPY backend/ ./backend/
COPY platforms.yaml ./platforms.yaml
COPY scripts/ ./scripts/

# Non-root runtime user. Persistent paths are created here so named volumes inherit the ownership.
RUN useradd --system --uid 10001 --home /app --shell /usr/sbin/nologin ovd \
    && mkdir -p /data/db /data/jobs /data/editor /data/cache /app/cookies \
    && chown -R ovd:ovd /data /app

ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    WPB_DATA_DIR=/data/db \
    JOBS_DIR=/data/jobs \
    EDITOR_WORK_DIR=/data/editor \
    EDITOR_CACHE_DIR=/data/cache \
    HF_HOME=/data/cache/hf \
    XDG_CACHE_HOME=/data/cache

USER ovd
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers ${API_WORKERS:-2} --limit-concurrency 200 --timeout-keep-alive 5 --proxy-headers --forwarded-allow-ips='*'"]
