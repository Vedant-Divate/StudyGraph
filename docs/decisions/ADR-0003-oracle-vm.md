# ADR-0003: Hosting on an Oracle Cloud Always Free arm64 VM (addendum)

- Status: accepted
- Date: 2026-10-12
- Phase: 0

## Context

Amendment 2 to PROJECT.md: hosting is a $0 Oracle Cloud Always Free VM
(linux/arm64) running the full compose stack including live ingestion — not
Vercel/Render. PROJECT.md A-8 and Section 18.3 change accordingly.

## Decision

- Target shape: Ampere A1 Flex, up to 2 OCPU / 12 GB (confirmed in Oracle's
  Always Free docs, fetched 2026-10-12; the docs also note 6 GB memory per OCPU
  and 200 GB block storage). The stack (`web`, `api`, `worker`, `db`) is sized
  to fit: small ASR model, pre-ingested demo course, memory limits on services.
- All images build for `linux/amd64` + `linux/arm64` via buildx from day one.
- Oracle may reclaim instances idle for 7 days (<20% CPU/network/memory) — the
  demo must tolerate a reboot (compose `restart: unless-stopped`, data on a
  persistent volume).
- Fallback: same compose stack locally + Cloudflare Tunnel for the video/judging.
- The human provisions the VM and shares access; the agent never creates cloud
  resources. TLS/reverse-proxy choice is deferred to Phase 9.

## Consequences

Public URL: **pending** (recorded in `docs/verification/phase-0.md`). Phase 9
deploys with `docker compose up -d` + `make ingest-demo` on the VM.
