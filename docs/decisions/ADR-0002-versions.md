# ADR-0002: Exact installed versions and arm64 findings

- Status: accepted
- Date: 2026-10-12
- Phase: 0

## Context

PROJECT.md 5.1 requires recording exact versions at build time and verifying every
dependency installs on linux/arm64 (Oracle VM).

## Decision

Phase 0 pins (lockfiles are the source of truth):

- API runtime: `python:3.12-slim` base; `fastapi==0.121.1`, `uvicorn==0.38.0`,
  `pydantic==2.12.4`, `pydantic-settings==2.12.0`, `httpx==0.28.1`
  (see `services/api/uv.lock`).
- API dev: `pytest==8.4.2`, `pytest-asyncio==1.2.0`, `ruff==0.14.5`, `mypy==1.18.2`.
- Web: Next.js / React / TS / ESLint / Vitest versions as in `apps/web/pnpm-lock.yaml`.
- System deps in API image: Debian `ffmpeg`, `libreoffice-writer`, `libreoffice-impress`.
- DB: `pgvector/pgvector:0.8.7-pg17`.
- Toolchain: `uv` 0.13.0, `commitlint` 19.8.1, `husky` 9.1.7.

## arm64 findings (checked 2026-10-12 via the PyPI JSON API, Debian package pages)

- `ctranslate2==4.8.2` (faster-whisper backend): `cp312-manylinux_aarch64` wheel
  exists — ASR stack OK on arm64 with Python 3.12.
- `PyMuPDF==1.28.2`: `manylinux_aarch64` (abi3) wheel exists — OK.
- `onnxruntime==1.31.0`: `manylinux_aarch64` wheels exist — OK (fallback embedder path).
- `faster-whisper==1.2.1`, `scenedetect`, `imagehash`: pure-Python (sdist/any-wheel) — OK.
- Debian bookworm `ffmpeg` and `libreoffice-writer` have arm64 builds (package pages
  resolve for bookworm/arm64) — OK.
- `pgvector/pgvector` publishes multi-arch images incl. arm64 (per its release CI);
  confirmed at image-build time in `docs/verification/phase-0.md`.

No dependency lacks an arm64 build; no fallback needed. Heavier deps
(faster-whisper, sentence-transformers) are pinned in Phase 2/3 when first used.

## Consequences

API Dockerfile stays on `python:3.12-slim` (Debian bookworm) so system packages and
`manylinux_2_27+` wheels line up. Re-check wheels when bumping versions.
