# Production Compose security configuration

## Required environment variables

Set these in the deployment environment; do not commit populated secrets or `.env` files:

- `WPB_ENV=production`: enables production startup and security policy.
- `ADMIN_API_KEY` or `WPB_ADMIN_KEY`: high-entropy admin key (at least 32 characters), unless Supabase admin JWT and allowlisted admin emails are configured.
- `TOKEN_HMAC_SECRET` or `DOWNLOAD_SIGNING_SECRET`: dedicated download-token signing key. The vault key remains a compatibility fallback.
- `EXTENSION_SECRET_KEY`: extension signing secret (at least 32 characters).
- `WPB_VAULT_SECRET`: token vault key(s); production keys must be at least 32 characters.
- `JOB_OWNER_SECRET`: stable job ownership capability key (at least 32 characters). Keep it stable across API restarts and vault key rotation; losing it invalidates access to existing job records.
- `PUBLIC_BASE_URL`: canonical HTTPS base URL used for temporary public-media links (for example, `https://api.example.com`). Never derive this from a request Host header.
- `JOBS_DIR`: writable persistent disk path for the SQLite job queue and outputs (Compose sets `/tmp/ovd_jobs` on a named volume).
- `REDIS_URL` or both `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`: shared single-use token replay and rate-limit store. Production refuses a process-local memory fallback.

Generate a secret locally with:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Generate distinct secrets for each purpose. Do not put secret values in logs, pull requests, or source control.

## Network and persistence

- Redis does not publish port 6379 to the host; it is reachable only from the Compose network.
- API binds to localhost by default behind a reverse proxy.
- Set `API_BIND_ADDRESS=0.0.0.0` only if direct host exposure is intentional; secure it with firewall and TLS configuration.
- The SQLite job queue is a single-host shared-filesystem design. All API worker processes on that host must share the same persistent `JOBS_DIR`. Do not scale across hosts with independent disks.
- Set `WPB_TRUST_PROXY=1` only when the public reverse proxy overwrites `X-Forwarded-For`, `X-Real-IP`, and related headers and direct API access is blocked.
- Configure `WORKER_SECRET` or `WORKER_KEY` only when remote worker delegation is intended; without a configured secret the API disables delegation.
- Optional `WORKER_RESULT_HOSTS`: comma-separated exact HTTPS hostnames allowed for worker result URLs when they differ from `WORKER_URL` host.
- Optional `JOB_MAX_SOURCE_MB`: maximum downloaded source size for merge/MP3 jobs (default 1024 MB, hard-capped at 2048 MB).
- `WPB_ENABLE_MOCK_CHECKOUT` is forced off in production; only non-production sandbox deployments may set it to `1`.

## Temporary media URL

Temporary-media uploads return links from `PUBLIC_BASE_URL`. Production requests fail with `503` when it is missing or invalid. The host must route `/api/temp-media` to this API service and be reachable by the social platform fetching the media.

## Rollout checklist

1. Back up the existing production environment and current job/temp-media data.
2. Confirm the required environment variables and their values in the secret manager.
3. Confirm the persistent disk is mounted at `JOBS_DIR` and writable by the API process.
4. Confirm Redis is reachable from the API and is not publicly exposed.
5. Confirm the reverse proxy terminates TLS, overwrites forwarding headers, and blocks direct upstream access before enabling `WPB_TRUST_PROXY=1`.
6. Validate Compose configuration and run the complete CI suite.
7. Set and persist `JOB_OWNER_SECRET` before the first production start; preserve it across releases and key rotations.
7. Verify readiness at `/health/ready`, admin queue metrics at `/api/v1/system/queue`, and job create/poll/cancel/download behavior in staging.
8. Keep rollback instructions and the previous environment configuration ready.

No production deployment or secret rotation is performed by this PR.
