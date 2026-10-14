# ADR-0007: Sprint merge of Phases 3, 4 and 5

- Status: accepted
- Date: 2026-10-13
- Phase: 3-4-5 (merged)

## Context

Sprint mode continues (ADR-0006). Video, concept graph and tutor chat merge into
one build. Demo scope stays Lectures 1–2 + OpenStax Ch 3.

## Decision (changes to PROJECT.md)

- Video: Lectures 1–2 only. ASR via faster-whisper small/int8/CPU with segment
  timestamps cached to JSONL. Keyframe/figure description from video capped at 8
  frames per lecture, background-only, never blocking; slide + textbook figures
  already cover the figure modality.
- Concept graph: 15–25 concepts, depth ≤ 3, prerequisite edges carry evidence
  unit IDs, cycles removed, units tagged, 2–4 misconceptions per concept with
  honest `origin` labelling, importance from tag counts.
- Tutor: three-way labels, server-resolved citations, ONE batched verifier call
  per answer (not per segment — latency control), refusal with related topics.
- Rate limits: probed once with ~10 parallel cheap calls; `LLM_RPM` and
  `LLM_CONCURRENCY` set from observation (recorded below).
- `LLM_RPM` / `LLM_CONCURRENCY` observed values: 10 parallel cheap chat calls on
  `nvidia/nemotron-3.5-lightning-30b-a3b` → 10/10 ok, zero 429s, latencies
  1157–1843 ms, wall 1.9 s (2026-10-13). Set `LLM_RPM=60`, `LLM_CONCURRENCY=4`
  (conservative sustained rate; bursts of 10 proven fine).
- Demo-course transcripts: OCW's own archive.org upload ships timestamped
  `.srt` subtitles for L01/L02 — these are used for the demo transcript units
  instead of local ASR (this sandbox cannot fetch faster-whisper's ~100 MB+
  dependency chain; `uv run --no-sync` is used locally so missing optional
  deps never block). `ASR_BACKEND=whisper` + lazy `faster-whisper` import stays
  as the path for user-uploaded videos and the VM (ffmpeg + deps install in
  Docker, where the network is fast). Never YouTube scraping.

## Consequences

Gate file is `docs/verification/phase-3-4-5.md`; it records the sprint recovery,
live-chat outcomes, citation checks, and remaining blockers. Video keyframes
must not gate any other step.

## Addendum — database recovery and retrieval calibration (2026-10-13)

- Docker was unavailable: both `docker version` and `docker ps` reported that
  `dockerDesktopLinuxEngine` could not be found. No Docker/WSL settings were
  changed and no retries were made.
- Used the direct Neon URL from `.env.local` for migration: its scheme was
  `postgresql+psycopg://`, it required SSL, and its host was not pooled. The
  URL and key are deliberately not recorded here.
- Alembic upgrade completed; the follow-up query reported `vector` present and
  19 public base tables.
- Cached-store run 1 and run 2 both reported: 1 course, 2 sources, 190 content
  units (178 transcript + 12 figure), 22 concepts, 15 edges, 555 unit-concept
  tags, and 68 misconceptions. Three units were untagged on each run.
- The cached graph has concept levels but no explicit parent IDs; the loader
  assigns a subtopic to the preceding topic and a concept to the latest
  subtopic (or topic). Cached edges have no evidence-unit IDs, so they are
  stored with the `weak` marker. Cached misconceptions lack evidence IDs and
  are stored as `llm_suggested`. The cached frame descriptions have no image
  files alongside them; figure citations therefore resolve to their source
  video timestamp, not a still image.
- Retrieval confidence from the 10-question probe: S1–S5 in-scope =
  `0.016385, 0.008218, 0.008218, 0.008218, 0.008218`; N1–N2 near-miss =
  `0.008218, 0.008218`; O1–O3 unrelated = `0.008218, 0.008218, 0.008218`.
  The score does not separate nine of the ten cases. Set
  `RETRIEVAL_MIN_CONFIDENCE=0.0082`, just below the observed minimum, to avoid
  suppressing retrieved context; the segment verifier remains responsible for
  rejecting unsupported material.
- The live chat route returned two expected `not_covered` refusals; the other
  eight requests errored (seven NIM timeouts and one Neon
  `IdleInTransactionSessionTimeout`). No citations were returned, so source
  citation opening could not be tested. The complete per-probe transcript is
  in the verification gate.
- To avoid keeping read transactions open over slow model calls, the route
  closes the course lookup transaction before retrieval and the tutor closes
  the retrieval transaction before generation/verification. The focused tutor
  tests pass after this change; live NIM was not rerun.
- The full repository gate reached 32 passing tests but had six PostgreSQL
  integration-test setup errors because the expected local database did not
  respond. Those tests clear library tables, so they were not redirected to
  Neon. The remaining Makefile checks did not run, and no sprint commit was
  made.
- To distinguish retrieved-but-unresponsive passages on near-miss prompts, the
  batched verifier prompt now includes the original question and judges both
  source support and answer relevance. This is a deliberate expansion of the
  verifier input described in PROJECT.md 8.5; a transcript test guards this.
- The chat prompt requests one concise grounded answer, and verifier failures
  now fail closed instead of preserving unverified claims as `partial`. This
  avoids mislabeling timed-out NIM checks as verified answers; a timeout
  regression test covers the refusal path.
