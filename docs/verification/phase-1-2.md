# Phase 1-2 verification — Domain, DB, LLM provider, PDF ingestion (short gate)

Sprint scope per ADR-0006. Full output in shell history; key tails pasted.

## What was built

- Domain: types, server-side citation resolution, BKT (+propagation/forgetting),
  restricted expression evaluator, scoring — with unit + property tests.
- DB: 18 tables + pgvector extension, Alembic migration applied to real Postgres,
  CRUD repositories; round-trip + idempotent re-ingest tests.
- LLM: NIM provider (OpenAI-compatible, rate limit, backoff, disk cache,
  schema-prompt + validate + one retry, reasoning deltas ignored), mock updated,
  hash/NIM embeddings. Live smoke 6/6 (chat, structured JSON, vision, verifier,
  judge, embeddings dim=2048).
- API: courses, PDF upload (size/type limits), job status routes.
- Ingestion: per-page text units, page renders, raster/vector figure detection,
  VLM descriptions (capped, cached), NIM/hash embeddings.
- Worker: DB-backed job runner dispatching ingest_pdf.
- Real ingest: L01 slides, L02 slides, OpenStax Ch3 (PDF pp. 179–238, 60 pp).

## Commands run and output (tails)

$ uv run --frozen ruff check . → All checks passed!
$ uv run --frozen ruff format --check . → 45 files already formatted
$ uv run --frozen mypy app → Success: no issues found in 37 source files
$ pytest -q → 30 passed, 1 warning
$ (web) typecheck/lint/test/build → clean, 1 passed, prerendered exit 0
$ alembic upgrade head → clean; 19 tables (18 + alembic_version), vector ext present
$ python scripts/nim_smoke.py --pdf data/demo-course/MIT6_041SCF13_L01.pdf
[PASS] chat 6922ms / structured 2609ms / vision 6641ms chars=1447 /
verifier 1436ms / judge 7672ms / embeddings 266ms dim=2048 → smoke: 6/6 passed
(no key printed; script refuses under CI)

## Ingestion results

- L01 slides: 4 pages → 4 text, 0 figures (vector-light pages).
- L02 slides: text units + 1 figure with live VLM description.
- OpenStax Ch3: 60 pages → 60 text + 5 figures (cap 5 for sprint speed).
- Totals: 67 text + 6 figure = 73 units, all embedded (NIM, 2048-dim), all `ready`.
- Timing: L01+L02 a few minutes (VLM 7–90 s/image); Ch3 text+embed ~11 s with
  warm figure cache. Earlier full-cap Ch3 attempt was aborted as too slow —
  hence the cap (figure path already proven on L02).

## Spot checks (5/5 pass)

1. L01 p.1 text starts "LECTURE 1 Sample space Ω…" — found on page. True
2. L02 p.1 text starts "LECTURE 2 Review of probability models…" — found. True
3. L02 p.2 figure: VLM JSON describes conditional-probability panels; PNG exists. True
4. Ch3 p.1 text starts "Figure 3.1 Meteor showers are rare…" — found. True
5. Ch3 p.1 figure: VLM JSON describes meteor/night-sky chapter opener; PNG exists. True

## Deviations from PROJECT.md

- ADR-0006 (sprint): phases merged, short gates, no P1/P2, no PPTX, L1–2 + Ch3
  scope, 30-item test set / 10-student simulator minimums for Phase 8.
- ADR-0005: JUDGE_MODEL = muse-glimmer-30b (glm-5.3 gave zero bytes in 150 s
  even streaming); vision falls back to reasoning_content (content is null).
- Upload route bug found by tests (dest file opened but never written) — fixed.
- Test-only: loopback DB port 15432 (port 5432 blocked on this host), dev DB
  password aligned to `studygraph`, figure cap 5 for the Ch3 sprint run.

## Commits in this phase

- 02c12a7 feat(domain) / 76259a5+5a1dad6 feat(db) / 3e1ce76 feat(llm) /
  52ae2a8 feat(api) / f107659 feat(ingest) / ee97eeb feat(workers)
- (gate file commit below)
