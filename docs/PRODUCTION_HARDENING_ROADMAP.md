# AnyDownloader Production Hardening — Consolidated Remaining Roadmap

This is the tracking checklist for the remaining work. Items are not marked complete until implementation and verification evidence are attached.

## P0 Security
- [ ] DNS-to-socket pinning for outbound media/subtitle fetches (preflight alone is not rebinding protection)
- [ ] Audit every route in v1/v2, editor, studio, autopilot, temp media and auth for authentication, ownership, mutation and signed URL boundaries
- [ ] Worker authentication, request signing/rotation, replay protection and network isolation
- [ ] Artifact path isolation: canonical paths, symlink defenses, tenant/job ownership and cleanup
- [ ] Secrets/startup audit: production fail-closed, safe diagnostics, no secret leakage
- [ ] OAuth callback/state/nonce/token lifecycle tests across providers

## P1 Reliability
- [ ] Lease/concurrency race tests with multiple managers/processes
- [ ] Cancellation race and cancellation-after-claim tests
- [ ] Retry/backoff and retry exhaustion tests
- [ ] Worker crash/restart recovery tests
- [ ] Stale-worker fencing verification for every write path
- [ ] Orphan artifact cleanup with safe ownership checks

## P2 Observability
- [ ] Structured logs and request/job correlation across worker/API
- [ ] Readiness checks for DB, shared token store and worker dependencies
- [ ] Queue metrics and bounded cardinality
- [ ] Consistent API error schema and status mapping
- [ ] OpenAPI route/schema audit
- [ ] Operational alert thresholds and runbook

## P3 Production Certification
- [ ] Security regression suite
- [ ] Worker integration tests
- [ ] Multi-worker concurrency tests
- [ ] Load and soak tests with recorded thresholds
- [ ] Rollback/recovery exercise and evidence

## Evidence required before release
- CI test report
- Static/security scan report
- Integration test report
- Concurrency/load report
- Deployment configuration review
- Rollback rehearsal record



## Consolidated hardening batch status (PR)
- [x] Heartbeat renewal is fenced by an unexpired lease and stops when cancellation is requested.
- [ ] DNS-to-socket pinning and outbound transport enforcement.
- [ ] Route authorization/ownership audit and fixes across all route groups.
- [ ] Worker request signing, replay protection, and network isolation.
- [ ] Artifact canonicalization/symlink and ownership cleanup audit.
- [ ] Production secrets/startup fail-closed audit.
- [ ] OAuth lifecycle/state/nonce coverage.
- [ ] Crash/restart, cancellation, retry and stale-worker integration suite.
- [ ] Observability/readiness/error schema/OpenAPI/operational thresholds.
- [ ] Load/soak/rollback evidence. These require deployment infrastructure and CI execution; not asserted complete in this PR.
