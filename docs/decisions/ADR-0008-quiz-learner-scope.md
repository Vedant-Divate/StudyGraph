# ADR-0008: Quiz + learner sprint scope (Phases 6-7 merged)

- Status: accepted
- Date: 2026-10-13
- Phase: 6-7 (merged)

## Context

Build freeze ~14:30 IST; this phase must land by ~13:30. Database is Neon
(hosted Postgres + pgvector). Chat accepted as-is (3/5 in-scope with
citations — known limit, honesty over rework).

## Decision (changes to PROJECT.md)

- Question priority: MCQ with misconception-tagged distractors first, verified
  numericals second (restricted evaluator). No short-answer. No
  figure-dependent questions unless everything else finishes early.
- No separate diagnostic mode: adaptive mode opens with 8 questions chosen by
  concept importance, one per top-level topic first.
- No separate dashboard: the Knowledge Map IS the dashboard (coloured by
  effective mastery, icons/text, root-cause trace highlight) plus a short
  post-quiz summary.
- The question bank is generated OFFLINE by a background script with LLM
  response caching; the demo never generates questions live.

## Consequences

Gate file is `docs/verification/phase-6-7.md` (short). `docs/review/questions.md`
holds the 20-question human review sheet. Phase 8 untouched.
