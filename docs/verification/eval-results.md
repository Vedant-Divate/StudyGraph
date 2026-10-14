# Eval results — RAG baseline (retrieval-only real; full run blocked)

Date: 2026-10-14. Scope: this sprint's eval lane (`eval/`,
`services/api/app/eval/`). Every number below is pasted from a script output
actually run in this sandbox; nothing is invented. Where a run was impossible,
that is stated and no number is given.

## Test set

`eval/testset/rag.jsonl` (sha16 `a16b8cd2d2b41651`): 30 items + header —
15 `in_scope`, 4 `multi_hop`, 5 `near_miss`, 3 `unrelated`, 3 `false_premise`;
`must_refuse=true` on the 11 off-material items. Status: **LLM-DRAFTED,
REQUIRES HUMAN REVIEW** (see `docs/review/testset-check.md`; 10 items listed
there). No test-set number below may be quoted externally until review is
recorded in the file header.

Gold locations were recomputed with the deterministic uuid5 scheme of
`scripts/store_cached_artifacts.py` (equal to the DB rows by construction);
the live DB was unreachable in this sandbox (no Docker daemon), so locations
were NOT read from a DB connection. Each location is guard-keyword verified
against the transcript window text at build time.

## Retrieval-only eval — REAL BASELINE (2026-10-14)

Command: `uv run --frozen python ../../eval/run_rag_eval.py --retrieval-only`
(from `services/api`). Output: `eval/results/rag_eval_retrieval.json`
(created 2026-10-14T11:57Z).

Method (LLM-free, no API/DB): 190-unit corpus rebuilt read-only from
`data/demo-course/lec0{1,2}.srt` + `thumb_desc.json`; deterministic hash
embeddings identical to `EMBED_BACKEND=hash`; RRF fusion of vector cosine and
IDF-weighted token overlap (local stand-in for Postgres full-text, which plus
neighbour expansion is NOT replicated). Scored with
`services/api/app/eval/metrics.py` (unit-tested in `eval/test_metrics.py`,
6 passed).

| Metric (k=5) | Value | n |
|---|---|---|
| recall@5 (RRF mirror, server-faithful) | 0.2402 | 22 gold-bearing |
| MRR (RRF mirror) | 0.2167 | 22 |
| recall@5 keyword-only diagnostic | 0.4008 | 22 |
| MRR keyword-only diagnostic | 0.5871 | 22 |
| excluded (no gold: 5 near-miss + 3 unrelated) | 8 | — |

Notes:

- Retrieval is scored on 22 items: 15 in-scope + 4 multi-hop + 3 false-premise
  (false-premise gold locations are the contradicting passages, so retrieving
  them is correct behaviour). The 8 refusal items with empty gold are excluded,
  not scored zero.
- The keyword-only diagnostic beats the RRF mirror because hash embeddings are
  semantically random: fusing a noise ranking drags the signal down. The same
  holds for the server under `EMBED_BACKEND=hash`; with `nim` embeddings the
  vector side should help. This is a finding, not a tuning excuse — the
  RRF-mirror numbers above are the recorded baseline.
- Model IDs in the results file are client-environment reported, not
  server-proven: generator `nvidia/nemotron-3.5-lightning-30b-a3b`, verifier
  `openai/gpt-oss-20b`, judge `meta/muse-glimmer-30b`, embed backend `hash`.
  No key was read, printed, or stored.

## Full eval (chat route) — NOT RUN (blocked, honestly recorded)

Command: `run_rag_eval.py --course-id cabcd146-… --timeout-s 8` (course UUID
recomputed with the store script's stable-ID scheme). Result
(`eval/results/rag_eval_full.json`): **30/30 `URLError`** — no API server or
database is reachable in this sandbox (Docker daemon down, no Postgres).
Its `refusal`/`citation` summaries are connection-failure artifacts
(tp=0, fp=0, fn=11, accuracy=0.0), NOT measurements; do not quote them.

To run for real (manual, needs DB + API + NIM key, ~30 items × up to 150 s
timeouts worst-case): start the stack, then

    uv run --frozen python ../../eval/run_rag_eval.py \
      --course-id <demo-course-uuid> --timeout-s 150

and re-run the judge below. No refusal, citation-accuracy, or judge numbers
exist yet — they were not invented.

## Framework metrics — RAGAS-style, custom implementation (NOT RAGAS results)

Time-boxed wiring attempt (≤40 min): the `ragas` package is not installed and
not in the API dependencies (adding it would touch files outside this lane's
scope); the judge also needs a live NIM key plus a running API/DB, and full-mode
answers do not exist yet. Per the sprint brief, the four PROJECT.md 11.2
metrics (faithfulness, answer relevancy, context precision, context recall)
are implemented as simple NIM-judge prompts in `eval/judge_ragas_style.py,
labelled "RAGAS-style, custom implementation" in every field, docstring and
log line. They are never called RAGAS results.

Judge-model choice: no new latency probe was run here; ADR-0005's measured
values stand (verifier `openai/gpt-oss-20b` ~5.4 s structured call vs judge
`meta/muse-glimmer-30b` ~20–30 s). The configured judge stays glimmer
(changing it is out of scope); the script accepts `--judge-model` for latency
experiments. Verified so far: `--dry-run` prompt construction only
(`eval/results/rag_judge_dryrun.json`, judged=0 — retrieval-only records have
no chat answers, as intended). Live judge run is deferred to the manual
full-eval environment above.

## Thresholds

`eval/thresholds.json` is set from the RRF-mirror baseline in this file
(recall@5 0.24015151515151514, MRR 0.21666666666666667, n=22, k=5), with the
PROJECT.md 11.5 rule: CI fails on regressions of more than 5 percentage points.

## Caveats (copy these wherever numbers travel)

1. Test set is LLM-drafted, unreviewed — nothing quotable yet.
2. Retrieval numbers are a local-corpus proxy, not server measurements.
3. No refusal / citation / judge numbers exist yet (full run blocked).
4. "RAGAS-style, custom implementation" ≠ RAGAS library results.
5. Model IDs are client-reported defaults, not server-proven.
