# AnyDownloader / OVD Hardening Program

Status: Initial code inspection. This document is a working plan, not a security certification.
Branch: hardening/p0-security-reliability
Scope: API, workers, jobs, authentication/authorization, Swagger/OpenAPI, observability and regression safety.

## Guardrails
- Preserve existing downloader, editor, studio, social publishing and API behavior unless a change is explicitly versioned and approved.
- No deployment, secret rotation, data migration or production configuration change without explicit approval.
- Add tests and evidence for every security/reliability fix.
- Treat code inspection findings as confirmed only where source evidence is available. Runtime/deployment findings require environment verification.

## Initial confirmed source observations
1. backend/security/zero_trust.py: rate_limit() returns allowed on storage exceptions (fail-open).
2. backend/main.py: EXTENSION_SECRET_KEY has a hard-coded fallback.
3. docker-compose.yml: ADMIN_API_KEY and TOKEN_HMAC_SECRET have insecure fallback values.
4. docker-compose.yml: Redis maps 6379 to the host; exposure depends on host/firewall configuration.
5. backend/job_manager.py: jobs are launched with asyncio.create_task() in the API process.
6. backend/job_manager.py: startup marks queued/processing jobs failed after restart rather than recovering them.
7. docker-compose.yml: worker service block is commented out; actual deployment topology must be verified.

## Priority sequence

### P0 — Security baseline
- Inventory every registered route, method, middleware and auth dependency.
- Verify public vs protected routes intentionally; identify missing auth and privilege boundaries.
- Remove insecure secret fallbacks; fail startup in production if required secrets are absent/weak.
- Confirm worker-to-API authentication and prevent direct unauthenticated worker operations.
- Audit SSRF, URL validation, redirects, DNS/IP resolution, file paths, temp-media access and FFmpeg invocation.
- Confirm Redis is private, authenticated as appropriate, and not publicly reachable.
- Evaluate rate-limit storage outage behavior; auth must remain fail-closed and rate limiting should degrade safely for sensitive operations.
- Add endpoint-specific limits and abuse controls.

### P1 — Job/worker reliability
- Define queue ownership and execution topology before replacing the current job model.
- Add durable execution, leases/heartbeats, idempotency, bounded retries/backoff, cancellation and stuck-job recovery.
- Enforce job ownership and result access controls.
- Validate worker payloads and job state transitions.
- Ensure crash recovery and duplicate execution safety.
- Resource limits for CPU, memory, disk, runtime, concurrency and uploads.

### P2 — API contract and observability
- Complete OpenAPI coverage and auth descriptions; Swagger docs must not be treated as access control.
- Standardize errors without breaking existing clients.
- Request/job correlation IDs, structured logs, health/readiness checks, queue and worker metrics.
- Dependency health checks with sensitive diagnostics restricted.

### P3 — Certification and optimization
- Regression suite for downloader/editor/studio/publishing.
- Security tests (auth bypass, IDOR, SSRF, traversal, abuse/rate limit).
- Load/soak tests, resource tuning and deployment/rollback verification.
- Production readiness checklist and evidence.

## Acceptance criteria
- All routes classified and tested for intended access.
- No insecure production secret defaults.
- Worker endpoints require authenticated, scoped service access.
- Users cannot access other users' jobs or files.
- Job recovery/retry/cancel/idempotency behavior is tested.
- Redis and internal services are not unintentionally exposed.
- Swagger accurately documents request/response/auth/error contracts.
- Existing downloader and editor flows pass regression tests.
- No production rollout until tests, configuration review and rollback plan are approved.

## Implementation order
1. Route/security inventory and environment/config audit.
2. P0 security fixes with tests.
3. Worker trust boundary and job ownership.
4. Durable job execution/recovery.
5. OpenAPI completion and observability.
6. Regression/load/security certification.
