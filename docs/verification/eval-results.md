# Eval results — full RAG eval, judge, and ablation (2026-10-14)

Scope: sprint eval lane (`eval/`, `services/api/app/eval/`, docs). Every
number below comes from a script output actually run here; nothing is
invented or rounded up. Raw JSON outputs live in `eval/results/` (gitignored
by repo design); this file is the committed record.

## Test set

`eval/testset/rag.jsonl` (sha16 `a16b8cd2d2b41651`): 30 items + header —
15 `in_scope`, 4 `multi_hop`, 5 `near_miss`, 3 `unrelated`, 3 `false_premise`;
`must_refuse=true` on the 11 off-material items. Status: **LLM-DRAFTED,
REQUIRES HUMAN REVIEW** (see `docs/review/testset-check.md`). Nothing below
may be quoted externally until review is recorded in the file header.

Gold locations use the deterministic uuid5 scheme of
`scripts/store_cached_artifacts.py`. Spot-check 2026-10-14: **54/54 gold
unit_ids present in Neon**. Course `cabcd146-86e6-5742-b51b-ad3ffd61ae27`
(MIT OCW 6.041SC): 2 sources, 190 units (all with 2048-dim stored embeddings),
22 concepts, 15 edges, 36/36 bank questions `verification.ok=true`.

## 1. Retrieval baseline — REAL (Neon + NIM embeddings)

Command: `run_rag_eval.py --db-retrieval` (server's own
`app.kb.retrieval.retrieve`: stored-vector cosine + Postgres full-text + RRF +
neighbour expansion; SELECT-only; `EMBED_BACKEND=nim` query-side).
Output: `eval/results/rag_eval_db.json`.

| Metric (k=5) | Value | n |
|---|---|---|
| recall@5 | 0.6053030303030303 | 22 gold-bearing |
| MRR | 0.7916666666666667 | 22 |
| excluded (no gold: 5 near-miss + 3 unrelated) | 8 | — |

The earlier hash-embedding proxy (recall@5 0.24015151515151514, MRR
0.21666666666666667) was non-representative — hash vectors carry no
semantics — and is superseded (kept, labelled, in `thresholds.json`).

Miss diagnosis (exact-unit matching is strict for multi-window answers;
gold labels and retrieval untouched per brief):

- rag-01 recall 0.00: retrieved 6 axiom-related windows (W20/W55/W56/W63/W43/
  W53), none the 4 gold windows (W44/W45/W48/W49). Topically right, unit-exact
  wrong.
- rag-02 0.50, rag-03 0.50, rag-04 0.67, rag-07 0.50: partial hits; misses are
  adjacent windows of the same passage (e.g. W23 missed when W22 hit).
- Keyword leg returns [] on full natural-language questions (tsquery ANDs all
  terms incl. `lectur`/`1`), so ranking is effectively vector-only there.
- `vector_ranked` has no ORDER BY: near-tied cosines can reorder between
  sessions (observed on the axioms probe). Reruns may vary slightly.

## 2. Full eval — real chat route, 30/30 ok, 0 errors, 0 timeouts

Server: `uvicorn app.main:app` on 127.0.0.1:8000 with Neon config,
`LLM_PROVIDER=nim`, `EMBED_BACKEND=nim`, `LLM_CONCURRENCY=2`, `LLM_RPM=30`;
stopped afterwards. Client: `run_rag_eval.py --course-id <demo> --timeout-s
300` in 3 chunks of 10 (merged to `eval/results/rag_eval_full.json`).
Per-item latency min 12.3 s, max 57.4 s, mean 33.0 s. Answered-item retrieval
confidence range 0.354–0.704. No key or DB URL printed anywhere.

Refusal (predicted = all segments `not_covered`):

| Slice | Value |
|---|---|
| precision | 0.6 (tp 6, fp 4) |
| recall | 0.5454545454545454 (tp 6, fn 5) |
| recall unrelated | 1.0 (3/3: rag-25,26,27) |
| recall near-miss | 0.2 (1/5: only rag-20) |
| recall false-premise | 0.6666666666666666 (2/3: rag-28,29) |

- False positives (in-scope refused at the confidence gate, conf 0.0, no LLM
  generation): rag-06 (darts infinite), rag-12 (P(min=2)=5/16), rag-16,
  rag-19 (both multi-hop).
- False negatives (off-material answered `source_backed`): rag-21 (disease
  Bayes computed by transferring the radar numbers), rag-22 (defines
  independence — a Lecture 3 topic), rag-23, rag-24, rag-30 (presents the
  1=0 fallacy as a valid lecture proof). The verifier passed all five.

Citation accuracy (page/slide equal, timestamp ±15 s; unit_id match first):

| Slice | Value |
|---|---|
| all gold-bearing (n=22) | 0.6818181818181818 (15/22) |
| answered gold-bearing (n=16) | 0.9375 (15/16; only rag-01 MISS) |

Label accuracy, hand-checked 10 answered in-scope items: **8/10**.

| Item | Verdict |
|---|---|
| rag-02,03,04,05,08,09,10,11 | CORRECT — claims match cited windows |
| rag-01 | INCORRECT — axiom 3 overstated as "any sequence of disjoint events" (lecture: two events; countable version is a separate axiom); cited W20/W43/W63 don't support "sequence" |
| rag-07 | INCORRECT — gives "grouping for real-world scenarios" as the reason for events-vs-outcomes; the lecture's reason is zero-probability points (W39, not cited) |

## 3. Framework metrics — RAGAS-style, custom implementation (NOT RAGAS results)

`eval/judge_ragas_style.py` on the 20 answered items (15 in-scope/multi-hop +
5 answered off-material). Judge: `openai/gpt-oss-20b` (fastest measured
non-generator that returns parseable JSON; glimmer pilot: ~90% unparseable,
discarded — see questions.md A-13). Mean judge latency 16.52345 s/call.
`ragas` library not installed/used; never present these as RAGAS results.

| Metric (RAGAS-style, custom) | Mean | Stdev | n scored (errors) |
|---|---|---|---|
| faithfulness | 0.7542611111111112 | 0.3715143232454749 | 18 (2) |
| answer relevancy | 0.925 | 0.17853571071357124 | 20 (0) |
| context precision | 0.3178947368421053 | 0.2961965731947268 | 19 (1) |
| context recall | 0.5252631578947369 | 0.4116253843772416 | 19 (1) |

By type: faithfulness in_scope 0.7425 / multi_hop 1.0 / near_miss 0.8889 /
false_premise 0.0; relevancy 0.9615 / 1.0 / 0.75 / 1.0; ctx-precision 0.4033 /
0.4 / 0.1 / 0.0; ctx-recall 0.5692 / 0.975 / 0.275 / 0.1. Low context
precision reflects top-6 retrieval pulling neighbouring windows.

## 4. Ablation — simulated students, not real learners

`eval/ablation.py` + `eval/simulator.py` (LLM-free, deterministic rerun
verified True). Snapshot: `eval/simulation/bank_snapshot.json` (22 concepts,
15 edges, 36 verified MCQ; held-out rule fixed: 4 lowest-importance
question-bearing concepts). Protocol: 30 students × 5 profiles × 3 policies
(random / sequential lecture-flow order / adaptive via production
`app/learner/policy.choose` over estimator beliefs), 5 sessions × 10
questions, master seed 20261014, estimator = production BKT
`update_mastery` + `propagate_incorrect`. CIs: 95% bootstrap, 2000 resamples
over students. Simulator params fixed a priori in `simulator.py` (only change
post-smoke: eval-pool masking bugfix in `ablation.py`, documented in code).

Mean true-mastery gain is NEGATIVE in all cells: with 7-day gaps, forgetting
(S 3–30) dominates ~2–3 learning updates per concept. Relative comparison
remains valid; absolute values are regime artefacts, not learner quality.

| Profile | Random gain | Sequential gain | Adaptive gain |
|---|---|---|---|
| strong | -0.4290 [-0.4346,-0.4232] | -0.4239 [-0.4293,-0.4184] | -0.4378 [-0.4434,-0.4322] |
| average | -0.3497 [-0.3554,-0.3440] | -0.3468 [-0.3525,-0.3413] | -0.3575 [-0.3634,-0.3518] |
| weak-foundations | -0.1833 [-0.1873,-0.1796] | -0.1802 [-0.1841,-0.1764] | -0.1898 [-0.1937,-0.1860] |
| forgetful | -0.4471 [-0.4530,-0.4408] | -0.4469 [-0.4528,-0.4406] | -0.4478 [-0.4536,-0.4414] |
| guesser | -0.2756 [-0.2814,-0.2698] | -0.2742 [-0.2800,-0.2684] | -0.2791 [-0.2850,-0.2735] |

Held-out gain is identical across policies per profile (held-out concepts are
never asked; decay only): strong -0.5107, average -0.4053, weak-foundations
-0.2750, forgetful -0.4509, guesser -0.3219.

- Estimator MAE by session (random shown; full table in `ablation.json`):
  strong 0.3895→0.2015, average 0.1930→0.1522, weak-foundations 0.1428→0.1510,
  forgetful 0.2001→0.1919, guesser 0.1361→0.2398. Adaptive MAE starts best
  then degrades (estimator has no forgetting while truth decays; guesser
  noise misleads it most: 0.1398→0.3266).
- Weak-targeting precision (asks on true z<0.6): saturated near 1.0 for
  random/sequential (everything decays below 0.6); adaptive 0.5267–0.9993.
- Repetition rate: sequential 0.42 (optimal rotation), random ~0.48, adaptive
  0.55–0.57 (concentration).
- Failure cases (adaptive gain ≤ best baseline, all 5 profiles): under
  forgetting dominance, spreading practice (sequential/random) preserves more
  total mastery than concentrating on weak concepts, and concentration repeats
  more. Guesser is the sharpest case: high guess/slip noise corrupts the
  estimator (MAE 0.33 by session 5), so adaptive targets badly.

## 5. Thresholds

`eval/thresholds.json` = real baseline (recall@5 0.6053030303030303, MRR
0.7916666666666667, n=22, k=5; hash proxy kept, labelled superseded).
Regression rule: >5 percentage points.

## Model IDs, seeds, versions

Generator `nvidia/nemotron-3.5-lightning-30b-a3b`, verifier
`openai/gpt-oss-20b`, eval judge `openai/gpt-oss-20b` (A-13), embeddings
`nvidia/nemotron-3-embed-1b` (query `input_type=query`), testset sha16
`a16b8cd2d2b41651`, ablation master seed 20261014, API local uvicorn
(concurrency 2, RPM 30). No keys/URLs recorded.

## Caveats (copy these wherever numbers travel)

1. Test set LLM-drafted, unreviewed — nothing quotable yet.
2. Retrieval miss analysis: exact-unit matching understates topical hits.
3. Reruns may vary slightly (no ORDER BY in vector_ranked).
4. "RAGAS-style, custom implementation" ≠ RAGAS library results.
5. Ablation: simulated, not real learners; negative gains are a forgetting-regime artefact.
6. Label subset is 10, not the PROJECT.md ≥ 20 (A-12).
