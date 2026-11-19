# Consolidated production-readiness implementation

This document distinguishes code-level controls from deployment validation. This branch is a consolidated hardening implementation; it is not a production certification or a deployment authorization.

## Implemented in this branch

### Security and configuration
- No hard-coded remote-worker shared secret remains in the API worker clients. Worker delegation is disabled when its shared secret is absent.
- Worker URLs must be HTTPS, without credentials, query strings, or fragments. Worker clients do not follow redirects.
- Download proxy token verification fails closed. Unsigned base64 payload decoding is not accepted as a signature fallback.
- Media CDN URLs are checked against the CDN hostname allowlist and public DNS answers. Outbound proxy redirects are followed manually only after validating each destination.
- Production token replay protection requires shared Redis or Upstash storage. Process-local memory is development-only.
- Rate-limit and admin lockout storage failures fail closed in production by default.
- Forwarded client IP headers remain opt-in through `WPB_TRUST_PROXY=1`.
- Temporary media links require a canonical production HTTPS `PUBLIC_BASE_URL`; caller-supplied Host and forwarded-host headers are not used.
- Generated video/audio endpoints accept only known generated filename patterns, reject path traversal/symlinks, and enforce a two-hour access lifetime.
- SQLite job files are permission-restricted where supported; database operations use WAL, full synchronous mode, busy timeout, and close connections after use.

### Durable job execution
- Jobs and their signed input payloads are persisted in SQLite.
- Job creation validates action, token count, signed token format, source-page host, media CDN hostname, and public DNS answers.
- Each job has a private owner capability. Only a SHA-256 hash of the capability is stored.
- Status polling, cancellation, and file access require the job owner capability.
- Job creation accepts a requester-scoped `Idempotency-Key`; a retry with the same key and same request returns the existing job, while a different payload conflicts.
- Queue claims are atomic across API worker processes sharing the same SQLite database.
- Worker leases and heartbeats support restart/stale-worker recovery.
- Transient processing failures use bounded retry/backoff; exhausted leases are failed safely.
- Jobs can be cancelled while queued, during FFmpeg execution, or between ZIP items.
- FFmpeg execution is time-bounded. ZIP jobs are limited to 40 items, 50 MB per item, and 300 MB total.
- Queue metadata exposes only aggregate counters through the admin-protected `/api/v1/system/queue` route.

### API and CI
- Job and ZIP APIs return asynchronous job capabilities; the frontend polls with `X-Job-Token` and retrieves the resulting file with the same capability.
- Readiness is available at `/health/ready`; queue metrics are admin-protected.
- Security CI compiles the backend/tests and runs focused tests for token handling, worker configuration, generated media paths, durable queue behavior, and security store failure policies.

## Production deployment prerequisites

Set these before starting the API with `WPB_ENV=production`:

- `WPB_VAULT_SECRET`: at least 32 characters per key; already enforced by token-vault startup validation.
- `REDIS_URL` or both `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`: shared single-use token/replay and rate-limit store. A process-local store is rejected in production.
- `ADMIN_API_KEY` or `WPB_ADMIN_KEY`: at least 32 characters, unless the Supabase admin JWT + allowlisted admin email configuration is fully provided.
- `EXTENSION_SECRET_KEY`: at least 32 characters.
- `PUBLIC_BASE_URL`: canonical HTTPS host that serves `/api/temp-media`.
- `JOBS_DIR`: writable persistent storage. All ASGI workers on the same host must see the same directory.
- `TOKEN_HMAC_SECRET` or `DOWNLOAD_SIGNING_SECRET` is recommended as a distinct download signing secret. The existing vault secret fallback remains for compatibility.
- Configure `WORKER_SECRET` or `WORKER_KEY` only when the remote worker is intended to be used. Without one, worker delegation is disabled.
- Set `WPB_TRUST_PROXY=1` only when the trusted reverse proxy overwrites forwarding headers and direct API access is blocked.

The Compose file sets `WPB_ENV=production`, `JOBS_DIR=/tmp/ovd_jobs`, requires `PUBLIC_BASE_URL`, keeps Redis on the private Compose network, and mounts the job directory as a named volume. For other hosting platforms, mount a persistent writable disk and point `JOBS_DIR` at that mount before enabling production mode.

The current SQLite queue is a **single-host, shared-filesystem design**. Do not scale the API across multiple hosts/replicas with independent disks or an unsupported network filesystem. Multi-host execution requires a different shared queue/database and shared result storage.

## Known remaining certification gates

These are intentionally not represented as completed:

1. **DNS rebinding / socket pinning:** the implementation checks DNS answers immediately before outbound requests and re-checks every redirect, but HTTPX still performs its own hostname resolution at connection time. A custom pinned-IP transport or egress proxy is required to eliminate the remaining DNS time-of-check/time-of-use window.
2. **Remote worker service:** this repository contains API-side worker clients, not the full deployed worker service implementation. Its routes, authorization, file access, runtime limits, and egress policy must be audited in the worker repository/deployment.
3. **Full route inventory:** the top-level API and job paths were reviewed, but every route imported from the Studio, Editor, Autopilot, Auth, Payments, v1/v2, and platform extractor modules still needs a route-by-route privilege review and explicit tests.
4. **OpenAPI:** a complete machine-readable OpenAPI contract for every route, request schema, scope, response, and error is not yet implemented.
5. **Full regression:** the CI additions are focused security/reliability tests. Downloader platform regression, Editor, Studio, publishing, auth integration, and browser end-to-end suites still need to run.
6. **Load and resource certification:** no production-equivalent load/soak test or CPU/RAM/disk stress test has been executed. FFmpeg timeout and ZIP/upload bounds exist, but host/container resource budgets still require deployment-specific sizing.
7. **Operational verification:** persistent-volume behavior, Redis connectivity/failover, reverse-proxy headers/TLS, backups, restore, and rollback have not been tested against the actual production environment.

## Validation commands

From the repository root:

```sh
python -m compileall -q backend tests
python tests/test_temp_media_auth.py
python tests/test_core.py
python tests/test_rate_limit_failure_policy.py
python tests/test_worker_config.py
python tests/test_generated_asset.py
python tests/test_job_manager_reliability.py
python tests/test_production_security_policy.py
docker compose config --quiet
```

A successful CI run is required before merge. A successful CI run alone does not close the external deployment and certification gates above.
