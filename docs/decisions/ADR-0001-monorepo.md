# ADR-0001: Monorepo with Docker Compose services

- Status: accepted
- Date: 2026-10-12
- Phase: 0

## Context

PROJECT.md Section 6.4 and Section 13 require a monorepo (`apps/web` + `services/api` + `eval/`)
runnable as one Docker Compose stack (web, api, worker, db) on an Oracle ARM VM.

## Decision

Monorepo at the repo root per Section 13: `apps/web` (Next.js), `services/api`
(FastAPI; api + worker share one image, worker runs an idle loop until Phase 2),
`db` via `pgvector/pgvector`. Python deps managed with `uv` + lockfile per 14.1;
Next.js app hand-written instead of `create-next-app` output (same shape, no
generator churn). No folders outside Section 13 were created.

## Consequences

Phase 1+ builds routers/services inside `services/api/app/`; the worker image is
reused with a different command. `create-next-app` deviation is cosmetic only.
