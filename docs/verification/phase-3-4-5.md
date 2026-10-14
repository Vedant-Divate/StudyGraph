# Phase 3-4-5 verification — Video, concept graph, tutor

Sprint recovery per ADR-0007. Historical phase evidence is retained below;
the database, cache import, retrieval calibration, live chat, and current
verification outcomes are recorded after it.

## Phase 3-5 implementation baseline

- Video: SRT parse/merge (30–60 s windows), whisper path (lazy import, Docker/VM),
  keyframe figure units, range streaming route, thumb storyboard ingestion.
- KB: per-source concept extraction + merge (22 concepts, depth ≤ 3), 15
  prerequisite edges, unit tagging, misconceptions, importance, hybrid vector +
  full-text RRF retrieval with neighbour expansion + confidence. The imported
  cache evidence limitations are noted below.
- Tutor: 8.4 generation, ONE batched verifier call, hallucinated-ID rejection,
  downgrade/drop rules, not_covered + related topics, allow_outside path.
- API: chat, graph, units, source file (Range), page render, course/source lists.
- Web: courses, library with statuses, source viewer (?page/?slide/?t=), chat
  with 3 label styles + citation chips + general-knowledge button, Cytoscape map
  with click panel, disclaimers.

## Tails

$ ruff check → All checks passed! / format clean / mypy 44 files clean
$ pytest → 38 passed (incl. 7 tutor/graph: downgrade, hallucinated-ID,
  refusal, pdf+video citation resolution, 2-call batching, cycle removal)
$ pnpm typecheck/lint/test/build → clean, 1 passed, prerendered
$ NIM probe (10 parallel) → 10/10 ok, zero 429s, 1157–1843 ms → RPM=60, CONC=4
$ NIM smoke (re-run) → 6/6 pass, embeddings dim=2048
$ SRT: L01 987 cues → 90 windows (0–3070 s, 0 out-of-range); L02 953 → 88
$ thumbs: 12/12 described by glimmer (700–1500 chars each), cached
$ concepts: 22 (4 topics/4 subtopics/14 concepts); edges proposed 15, kept 15;
  misconceptions 22/22 concepts (2–4 each)

## 15 strongest edges (human review)

0.95 Events -> Complementary Events / 0.95 Probability Axioms -> Conditional
Probability / 0.95 Conditional Models -> Airplane Radar Example / 0.90 Sample
Space -> Events / 0.90 Probability Assignment -> Probability Axioms /
0.90 Conditional Probability -> Conditional Models /
0.90 Definition (Conditional Probability) -> Conditional Probability Formula /
0.85 Mutually Exclusive Outcomes -> Mutually Exclusive Events /
0.85 Collectively Exhaustive Events -> Complementary Events /
0.80 Finite Sample Space -> Mutually Exclusive Outcomes /
0.80 Collectively Exhaustive Outcomes -> Collectively Exhaustive Events /
0.80 Definition (Events) -> Events as Subsets /
0.70 Definition (Sample Space) -> Finite Sample Space /
0.70 Events as Subsets -> Mutually Exclusive Events /
0.70 Countably Infinite Sample Space -> Probability Assignment

## Spot checks (5 transcript-adjacent, audio check deferred)

Cue-level: L01/L02 spans match video durations (51:11); windows monotonic,
30–90 s; first cues are the CC licence header (expected). Phonetic
audio-vs-cue check needs playback — do it while reviewing the demo video.

## Sprint recovery — database and cached artifacts

- Docker checks failed because the Docker Desktop engine pipe was unavailable;
  no Docker/WSL settings were changed or retried. The direct Neon path from
  `.env.local` was used. The URL/key were not printed or written here.
- `alembic upgrade head` completed. Database check: `vector` extension present;
  19 public base tables.
- `scripts/store_cached_artifacts.py` ran twice successfully with identical
  table counts: courses 1, sources 2, content_units 190 (178 transcript + 12
  figure), concepts 22, concept_edges 15, unit_concepts 555, misconceptions 68.
  Three units were untagged on both runs.
- The cache has no concept parent IDs or edge/misconception evidence-unit IDs.
  Parents are inferred from ordered levels; edges are marked weak and
  misconceptions `llm_suggested` without evidence IDs. Frame descriptions
  exist, but cached still-image files do not; figure locations resolve to video
  timestamps.

## Retrieval calibration

RRF remains the ordering signal. Confidence is the top raw embedding cosine;
the mean of the top three is reported as a diagnostic. On the ten probe
questions below, the five in-scope maxima are all above the three unrelated
maxima. The two near-misses are above threshold and are left to the verifier.
The measured scores support `RETRIEVAL_MIN_CONFIDENCE=0.35`.

| Probe | Scope | Top cosine | Mean top 3 |
|---|---|---:|---:|
| S1 | in-scope | 0.658150 | 0.639081 |
| S2 | in-scope | 0.606261 | 0.597710 |
| S3 | in-scope | 0.587431 | 0.577880 |
| S4 | in-scope | 0.646299 | 0.622906 |
| S5 | in-scope | 0.667641 | 0.648470 |
| N1 | near-miss | 0.420355 | 0.416068 |
| N2 | near-miss | 0.393891 | 0.377589 |
| O1 | unrelated | 0.150911 | 0.142178 |
| O2 | unrelated | 0.074751 | 0.069564 |
| O3 | unrelated | 0.187377 | 0.175727 |

## Live chat transcript

The final probe used the configured real NIM models: generation
`nvidia/nemotron-3.5-lightning-30b-a3b` (thinking disabled) and verifier
`openai/gpt-oss-20b` (`Reasoning: low`). Generation calls took 1.166–4.634 s.
Verifier calls took 4.484–60.019 s; calls reaching the 60 s deadline failed
closed. Total route latency includes database and embedding work.

| Probe | Question | Final segment / verifier | Citation location and validation | Generation / verifier / total latency |
|---|---|---|---|---:|
| S1 | What are the axioms of probability? | `not_covered`: “This isn't covered in your uploaded material.”; verifier returned no supported segment | None | 2.637 / 16.992 / 38.043 s |
| S2 | How is conditional probability defined, and what is its formula? | `source_backed`: “Conditional probability is defined as the probability of both events A and B occurring divided by the probability of the conditioning event B. Its formula is P(A and B) / P(B), provided P(B) is not zero.” Verifier: supported | MIT 6.041SC Lecture 2 · 30:05 (`t=1805`, 1805.370–1835.540 s); 36:07 (`t=2167`, 2167.310–2201.980 s); 46:59 (`t=2819`, 2819.340–2853.550 s). All source files exist; timestamps are within 3070.94 s duration. | 3.253 / 4.484 / 28.566 s |
| S3 | What does it mean for outcomes in a sample space to be collectively exhaustive? | `source_backed`: “Outcomes in a sample space are collectively exhaustive if every possible result of the experiment is included as an element, ensuring no possibilities are omitted.” Verifier: supported | MIT 6.041SC Lecture 1 · 12:06 (`t=726`, 726.730–757.830 s); 12:37 (`t=757`, 757.830–790.660 s); Lecture 2 · 1:44 (`t=104`, 104.900–140.510 s); Lecture 1 · 25:08 (`t=1508`, 1508.110–1541.520 s). All source files exist; timestamps are within their video durations (3070.63/3070.94 s). | 2.062 / 14.273 / 31.444 s |
| S4 | What are mutually exclusive events, and how does their probability relate to the probability of their union? | `not_covered`: “This isn't covered in your uploaded material.”; verifier timed out at 60.019 s | None | 1.166 / 60.019 / 82.763 s |
| S5 | What does the airplane radar example illustrate about conditional probability? | `source_backed`: “Conditional probability updates beliefs based on new evidence, such as radar detecting an object, shifting the likelihood of a plane's presence from an initial 5% to 34% given the observation.” Verifier: supported | MIT 6.041SC Lecture 2 · 46:20 (`t=2780`, 2780.110–2819.340 s); 44:42 (`t=2682`, 2682.950–2718.610 s). All source files exist; timestamps are within 3070.94 s duration. | 1.797 / 7.722 / 26.452 s |
| N1 | Derive the binomial distribution from independent Bernoulli trials. | `not_covered`; verifier timed out at 60.008 s | None | 2.152 / 60.008 / 91.638 s |
| N2 | How can Bayes' theorem diagnose a disease from test sensitivity, specificity, and prior probability? | `not_covered`; verifier returned no supported segment | None | 4.634 / 15.960 / 38.502 s |
| O1 | How does a TLS handshake negotiate encryption keys? | `not_covered`; verifier not run (below retrieval threshold) | None | No LLM calls / 27.037 s |
| O2 | How does photosynthesis convert light into chemical energy? | `not_covered`; verifier not run (below retrieval threshold) | None | No LLM calls / 21.218 s |
| O3 | How does quicksort partition and sort an array? | `not_covered`; verifier not run (below retrieval threshold) | None | No LLM calls / 18.515 s |

Result: 3/5 in-scope questions returned a valid `source_backed` answer with
citations; the requested 4/5 target was not met. All 3/3 unrelated questions
were refused, and both near-misses were refused. Every returned citation passed
the recorded source-file and timestamp-bounds checks. The transcript records
the resolved viewer routes, but browser-opening each route was not verified.

Verifier timeout cases fail closed. The route/tutor release the read-only DB
transaction before model calls; focused tests cover that behavior.

## Verification run

The Makefile recipe uses Unix inline environment assignments, which `cmd.exe`
does not support. `mingw32-make verify` therefore fails at pytest setup on this
Windows shell. Ran each Makefile verification command directly in PowerShell
with the same mock providers, `DATABASE_URL_SYNC` unset, and `PGPORT=1` to
ensure integration tests use only unreachable local PostgreSQL (never Neon):

```text
ruff check .
All checks passed!
ruff format --check .
56 files already formatted
mypy app
Success: no issues found in 44 source files
pytest -q
sss........sss.............................                              [100%]
37 passed, 6 skipped, 1 warning in 5.44s
pnpm.cmd typecheck
tsc --noEmit (exit 0)
pnpm.cmd lint
0 errors, 2 warnings (unused useEffect and API_BASE)
pnpm.cmd test
Test Files  1 passed
Tests  1 passed
pnpm.cmd build
Compiled successfully; generated 5/5 static pages (exit 0)
./scripts/check_no_secrets.sh
exit 0; no output
```

The first direct secret-scan invocation lacked `grep` on the shell PATH; the
scan was rerun with the MSYS utilities available and exited 0. Full verification
passes, with six expected local-Postgres skips. Do not start Phase 6.

## Deviations

- ADR-0007: SRT from OCW's own upload instead of local ASR (sandbox cannot
  fetch faster-whisper deps; `uv run --no-sync` locally); thumbs instead of
  ffmpeg keyframes (no ffmpeg here; Docker image has it); JUDGE_MODEL=glimmer
  (glm-5.3 silent 150 s); hook uses --no-sync; faster graph calls use gpt-oss.
- `.husky/pre-commit` uses --no-sync (CI unaffected — it syncs fresh).

## Commits

Earlier phase commits remain in history. Sprint changes are pending separate
feature commits after this verification gate.
