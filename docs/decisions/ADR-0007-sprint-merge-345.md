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

Gate file is `docs/verification/phase-3-4-5.md` (short format + 5/5 transcript
and 5 timestamp spot-checks). Video keyframes must not gate any other step.
