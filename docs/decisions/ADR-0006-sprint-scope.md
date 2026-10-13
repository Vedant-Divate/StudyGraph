# ADR-0006: Sprint scope (deadline 00:15 IST Thu 15 Oct 2026)

- Status: accepted
- Date: 2026-10-12
- Phase: 1-2 (merged)

## Context

About 25 hours remain to the submission deadline. Phases 1 and 2 merge into one
build; later phases may merge the same way. This ADR records the descoping; all
P0 differentiators stay in.

## Decision (changes to PROJECT.md)

- Phases 1 + 2 build together now; later merges allowed without a new ADR each
  time (recorded in the gate file instead).
- Verification gates are short: tail of `make verify` (or identical commands on
  machines without `make`) plus 3+ spot checks. Phase 0 stays the full-format gate.
- Skipped: all P1/P2 features (F-21–F-26) and the PPTX pipeline — the lecture PDFs
  are slides and go through the PDF page pipeline.
- Demo scope: videos + slides of Lectures 1–2 only; textbook OpenStax Ch 3 only.
- Eval test set: 30 items minimum (was 60). Simulator: ≥10 students per profile
  (was 30). Applies when Phase 8 builds.
- In scope, unchanged: server-resolved citations, three-way labels + verifier,
  verified questions with cross-model solving + dedup, BKT learner model with
  propagation/forgetting, Knowledge Map, RAGAS + adversarial refusal + ablation.

## Consequences

`docs/verification/phase-1-2.md` uses the short gate format. Phase 3+ prompts may
declare further merges; this ADR covers them.
