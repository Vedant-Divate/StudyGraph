# Phase 3-4-5 verification — Video, concept graph, tutor (short gate)

Sprint merge per ADR-0007. Docker Desktop died mid-phase, so live-DB steps are
recorded as blocked with recovery commands. Everything else is proven below.

## What was built (all committed + pushed)

- Video: SRT parse/merge (30–60 s windows), whisper path (lazy import, Docker/VM),
  keyframe figure units, range streaming route, thumb storyboard ingestion.
- KB: per-source concept extraction + merge (22 concepts, depth ≤ 3), 15
  prerequisite edges (acyclic, evidence-labelled), unit tagging, misconceptions
  with honest origins, importance, hybrid vector + full-text RRF retrieval with
  neighbour expansion + confidence.
- Tutor: 8.4 generation, ONE batched verifier call, hallucinated-ID rejection,
  downgrade/drop rules, not_covered + related topics, allow_outside path.
- API: chat, graph, units, source file (Range), page render, course/source lists.
- Web: courses, library with statuses, source viewer (?page/?slide/?t=), chat
  with 3 label styles + citation chips + general-knowledge button, Cytoscape map
  with click panel, disclaimers. `typecheck/lint/test/build` green.

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

## BLOCKED (Docker daemon down ~2 h, pipe missing)

- Storing video transcript/figure units, concepts/edges/tags/misconceptions.
  Artifacts ready: thumb_desc.json (12), graph_draft.json (22+15+misc).
- Retrieval threshold tuning + 5/5 live chat transcript.
- Recover: restart Docker Desktop, `docker compose up -d db`,
  `DATABASE_URL_SYNC=...:15432 alembic upgrade head` (already applied),
  run store script (graph_draft → DB), then 10-question tuning.
  Native PG18 on this host lacks the vector extension — use the pgvector
  container, not native PG.

## Deviations

- ADR-0007: SRT from OCW's own upload instead of local ASR (sandbox cannot
  fetch faster-whisper deps; `uv run --no-sync` locally); thumbs instead of
  ffmpeg keyframes (no ffmpeg here; Docker image has it); JUDGE_MODEL=glimmer
  (glm-5.3 silent 150 s); hook uses --no-sync; faster graph calls use gpt-oss.
- `.husky/pre-commit` uses --no-sync (CI unaffected — it syncs fresh).

## Commits

feat(ingest) video · feat(kb) concepts/edges/retrieval · feat(tutor)+routes ·
feat(web) · docs ADR-0007 · fix(kb) context · style(kb)
