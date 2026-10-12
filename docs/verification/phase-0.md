# Phase 0 verification — Foundations, material selection, assumption resolution

## What was built

- Monorepo skeleton per PROJECT.md Section 13: `apps/web` (Next.js landing with
  disclaimers), `services/api` (FastAPI `GET /api/health`, config, LLM provider
  interface stub + mock provider, idle worker loop), `db` (pgvector), compose
  wiring all four services.
- Tooling: ruff, mypy (strict), pytest, ESLint, Prettier, Vitest, husky
  (pre-commit runs ruff; commit-msg runs commitlint), commitlint with the
  PROJECT.md scope enum, `check_no_secrets.sh`, CI (`ci.yml`: lockfile installs,
  `make verify` on mock backends, image build).
- Docs: PROJECT.md, AGENTS.md, ADRs 0001–0005, `docs/questions.md` (Section 4
  resolutions), demo-course ATTRIBUTIONS.md + `scripts/fetch_demo_course.sh`.
- No feature code, no live API calls, no provisioned resources.

## Commands run and output (abbreviated, real)

$ (services/api) uv run --frozen ruff check .
All checks passed!
$ (services/api) uv run --frozen ruff format --check .
9 files already formatted
$ (services/api) uv run --frozen mypy app
Success: no issues found in 8 source files
$ (services/api) LLM_PROVIDER=mock ASR_BACKEND=mock EMBED_BACKEND=hash uv run --frozen pytest -q
3 passed, 1 warning in 0.45s
$ (apps/web) pnpm typecheck  # tsc --noEmit, clean
$ (apps/web) pnpm lint      # clean after adding .next/out ignores
$ (apps/web) pnpm test
Test Files 1 passed (1) / Tests 1 passed (1)
$ (apps/web) pnpm build
Route (app)  Size  First Load JS /  123 B  102 kB — prerendered, exit 0
$ bash scripts/check_no_secrets.sh; echo exit=$?
exit=0
$ docker compose up --build -d  # exit=0 after two fixes (below)
api Up / db Up (healthy) / web Up / worker Up
$ curl localhost:8000/api/health
{"status":"ok","app_env":"development","llm_provider":"mock","asr_backend":"mock","embed_backend":"hash"}
$ curl localhost:3000/  # contains:
<h1>StudyGraph</h1>  + "Check the cited source."
$ git clone . /tmp/clone-test  # all 13 key files present (lockfiles, compose,
  Dockerfiles, .env.example, Makefile, fetch script, attributions, CI workflow)

Bad-commit proof:
$ git commit --allow-empty -m "bad message without convention"
All checks passed! / 9 files already formatted
input: bad message without convention
subject may not be empty [subject-empty] / type may not be empty [type-empty]
(husky - commit-msg script failed; commit count stayed at 6 — nothing kept)

Fixes found by building/running (committed as fix(deploy)):
- api image missed the venv on PATH (`uvicorn: executable not found`) → set
  VIRTUAL_ENV/PATH in the Dockerfile.
- web image: `COPY . .` without a .dockerignore overlaid Windows node_modules
  (`styled-jsx` resolution failure) → added .dockerignore files; `next start`
  needs no pnpm (direct `node .../next/dist/bin/next start`); `next.config.ts`
  needs runtime TypeScript (pruned) → plain `next.config.mjs`.

## Manual check

API health JSON above (mock backends, no secrets). Landing page renders the
title plus the three mandatory disclaimers. Screenshots: n/a (headless shell).

## Links fetched

- https://devpost.com/submit-to/31481-multimodal-ai-hackathon-2026/manage/submissions
  → redirects logged-out to https://multimodal-ai-hackathon-2026-7.devpost.com/
  (+ /rules): deadline "Oct 15, 2026 @ 12:15am IST" (= 00:15 IST Thu 15 Oct 2026
  = 18:45 UTC Wed 14 Oct); teams 1–4 incl. solo, students only; build period
  30 Sep–14 Oct EOD; judging 15–20 Oct; showcase 21 Oct; AI assistants allowed
  with Built-With + README disclosure.
- OCW course page, Unit I page, Lecture 1–5 pages, lecture-1-video resource page:
  6.041SC Fall 2013, Prof. John Tsitsiklis, CC BY-NC-SA 4.0 footer on all pages;
  L1 00:51:11 §§1.1–1.2, L2 00:51:11 §§1.3–1.4, L3 00:46:30 §1.5, L4 00:51:35 §1.6
  (total ≈3h20m); PDFs are "Slides (PDF)"; videos have OCW "Download video" +
  transcript, hosted at archive.org/download/MIT6.041F10/MIT6_041F11_lec0N_300k.mp4
  (L01 HEAD: video/mp4, 118,062,027 bytes).
- OpenStax CMS API (apps/cms/api/v2/pages/750) + the 2e PDF itself (23,503,369
  bytes, 847 pp, bookmarks + p.3 copyright page extracted): licence
  **CC BY-NC-SA 4.0** (corrects PROJECT.md's "expected CC BY 4.0"); chapters:
  1 Sampling and Data, 2 Descriptive Statistics, **3 Probability Topics**,
  **4 Discrete Random Variables**, 5–13 + appendices. Ch 3 ↔ Lectures 1–4,
  Ch 4 ↔ Lectures 5+. Good match; no alternative proposed.
- Oracle Always Free docs: Ampere A1 Flex = 2 OCPU / 12 GB; 7-day idle
  (<20% CPU/net/mem) instances may be reclaimed; 200 GB storage.
- PyPI JSON API: ctranslate2 4.8.2 (cp312-manylinux_aarch64 ✓), PyMuPDF 1.28.2
  (manylinux_aarch64 ✓), onnxruntime 1.31.0 (aarch64 ✓); faster-whisper /
  scenedetect / imagehash are pure-Python. Debian bookworm/arm64 pages resolve
  for ffmpeg and libreoffice-writer. No dependency lacks arm64; no fallback needed.
- `docker buildx imagetools inspect pgvector/pgvector:0.8.7-pg17` → linux/amd64
  + linux/arm64. `python:3.12-slim` and `node:22-alpine` run as aarch64 under
  emulation (`uname -m` → aarch64).

## arm64 image build (attempted, partial — environment-limited)

- After installing qemu binfmt, the api arm64 build progressed through the
  arm64 base pull and ~290+ arm64 Debian package fetches (trixie/main arm64 in
  the log) before the 10-minute tool timeout killed the client. Emulated apt +
  LibreOffice needs longer than this shell allows; not a build failure.
- Web arm64 build got through pnpm install, then died on qemu-emulation I/O
  flakiness (EIO copyfile + EOF under heavy overlayfs load on this Windows host).
- Conclusion: Dockerfiles are arch-clean (no arch-specific steps); full arm64
  builds run in CI/native on the ARM VM. The amd64 `docker compose build` step
  added to CI covers per-commit image regressions.
- End-state note: after the emulated builds, this host's Docker Desktop Linux
  engine became unresponsive (API 500s; service restart did not recover it within
  the phase). The successful `up` + endpoint checks above were captured before
  that. If containers revive on daemon recovery, run `docker compose down`.

## Course verification results

See ADR-0004. Slides L01 verified downloadable (599,312 bytes,
sha256 d9538a403bd0390f54f3f1c6edec12a49777821facb459f1e6004744fe5498b0).
Full media fetch (4 videos ≈ 450 MB + PDFs) deferred to the human/VM — the script
`scripts/fetch_demo_course.sh` performs it with retries; checksums to be recorded
on first successful fetch. Media is gitignored, never committed.

## Resolution of every row in Section 4

- A-1 deadline/timezone: resolved (00:15 IST Thu 15 Oct 2026).
- A-2 team/registration: rules resolved (1–4 incl. solo); **our registration
  status unresolved — human to confirm.**
- A-3 video host/length: **unresolved, using default** (public YouTube, 3–10 min).
- A-4 originality/build/AI disclosure: build period + AI rules resolved;
  no separate originality clause found — honest history + README disclosure.
- Third-party/material rules: **unresolved, using default** (open-licensed only).
- Organizer resources: resolved (Drive problem statements — unopened, needs human;
  Discord https://discord.gg/UD8EVcdcq).
- A-5 course: fixed + verified (licence correction recorded, no swap).
- A-6/A-8 Oracle VM: limits confirmed; **VM provisioning + public URL pending (human).**
- A-7 NIM: **unresolved — human uploads model screenshots, then base URL + key.
  ADR-0005 holds placeholders; no live calls made.**
- A-9 Hindi: out of scope (P2), no action.

## Deviations from PROJECT.md

- `.dockerignore` files added (standard hygiene implied by the multi-arch image
  requirement; no new folders outside Section 13).
- `output: "standalone"` dropped: standalone tracing needs symlinks, which
  Windows dev machines without Developer Mode cannot create; runner uses
  `next start`. Revisit for image size on the VM.
- `python:3.12-slim` currently resolves to Debian trixie, not bookworm
  (recorded in ADR-0002; tag floats).
- `make` is unavailable on the Windows dev machine, so the verify steps were run
  directly with identical commands; `make verify` runs for real in CI (ubuntu).
- Full arm64 image builds exceed what this emulated host can finish; recorded
  above with the evidence that every layer is arm64-clean.

## Public URL

**Pending** — human provisions the Oracle VM in Phase 9.

## Commits in this phase

- 07dea90 chore(repo): scaffold monorepo with compose services
- 8fdbfe1 chore(repo): configure linting, hooks and commitlint
- 1d54ad4 docs(project): add PROJECT.md and AGENTS.md
- e33eec0 docs(decisions): add ADR-0001 to ADR-0005
- f9d6560 chore(scripts): add demo course fetch script
- df39f65 ci(ci): add verify workflow
- 00d2d0c fix(deploy): make compose stack build and run
- a09e95f docs(decisions): note trixie base in ADR-0002
