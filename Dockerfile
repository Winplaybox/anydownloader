# OVD Downloader Production Dockerfile (v3)
FROM python:3.12-slim-bookworm

# Install system dependencies: ffmpeg, nodejs, curl, ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    nodejs \
    npm \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Deno for yt-dlp-ejs challenge solver
RUN curl -fsSL https://deno.land/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:$PATH"

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and platforms registry
COPY backend/ ./backend/
COPY platforms.yaml ./platforms.yaml
COPY scripts/ ./scripts/

# Set environment
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

# Start FastAPI application via uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
