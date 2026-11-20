# AnyDownloader / OVD Hardening Program

Status: Consolidated implementation in review. This is not a security certification.
Branch: hardening/full-production-readiness
Scope: API, workers, jobs, authentication/authorization, Swagger/OpenAPI, observability and regression safety.

## Guardrails
- Preserve existing downloader, editor, studio, social publishing and API behavior unless a change is explicitly versioned and approved.
- No deployment, secret rotation, data migration or production configuration change without explicit approval.
- Add tests and evidence for every security/reliability fix.
- Treat code inspection findings as confirmed only where source evidence is available. Runtime/deployment findings require environment verification.

## Initial confirmed source observations and current disposition
1. Insecure temp-media credentials, compose secret defaults, Redis host exposure, unsigned download payload fallback, extension secret fallback, and default forwarded-IP trust have been addressed by the merged PRs #16–#24.
2. Remote worker clients no longer contain a hard-coded shared secret; remote delegation is disabled when a secret is absent.
3. Temporary-media public URL generation uses configured production HTTPS host only.
4. CDN proxying validates approved media hosts, public DNS answers, and every redirect target. Socket-level DNS pinning remains an open gate.
5. Process-local token replay storage is rejected in production; shared Redis/Upstash is mandatory.
6. Job execution is persisted in SQLite with atomic claims, leases, heartbeats, bounded retries, owner capabilities, cancellation, and cleanup. A persistent shared filesystem on a single host is required.
7. Job result APIs enforce per-job ownership; generated-media download paths are constrained to known names and a retention window.
8. Production startup validates admin/extension/public URL/job disk configuration; readiness reports dependency checks.
9. Imported route modules, external worker deployment, full OpenAPI, end-to-end platform regressions, load/soak, and production rollback remain to be certified.

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
