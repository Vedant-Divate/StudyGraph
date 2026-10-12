# ADR-0005: LLM provider is NVIDIA NIM (models pending human input)

- Status: proposed (models TBD — human uploads screenshots next)
- Date: 2026-10-12
- Phase: 0

## Context

Amendment 1 to PROJECT.md: AI provider is NVIDIA NIM behind the provider interface
(Sections 6/8), not Anthropic. Model IDs are configuration, never guessed. Phase 0
adds config, the provider-interface stub, the mock provider and this ADR — no live
API calls.

## Decision (structure; values pending)

- `LLM_PROVIDER=nim|mock`; `NIM_BASE_URL`, `NIM_API_KEY` (`.env.local` / deploy env
  only), `LLM_MODEL` (chat), `VISION_MODEL` (vision-capable, for figures/frames),
  `VERIFIER_MODEL` (≠ `LLM_MODEL`), `JUDGE_MODEL` (≠ `LLM_MODEL`), `EMBED_BACKEND`
  (`nim|local|hash`), `EMBED_MODEL`, `LLM_RPM` + `LLM_CONCURRENCY` caps. All are in
  `.env.example` as placeholders.
- Structured output: schema-prompt + Pydantic validate + one retry fallback, unless
  a chosen model documents guided/forced JSON — recorded per model below once known.
- Rate limiting/backoff configurable; LLM responses cached by input hash during
  ingestion/eval; tests/CI use the mock provider only.
- Key handling: never printed, echoed, or written into any committed file, doc, ADR,
  log or verification output; rotate after the hackathon.

## Chosen models (TO BE FILLED after human screenshots + NIM docs check)

| Role | Model ID | Vision? | Structured-output mode | Notes |
|------|----------|---------|------------------------|-------|
| `LLM_MODEL` (chat) | TBD | TBD | TBD | — |
| `VISION_MODEL` | TBD | must be yes | TBD | figure/frame descriptions |
| `VERIFIER_MODEL` | TBD (≠ chat) | n/a | TBD | cross-model verification |
| `JUDGE_MODEL` | TBD (≠ chat) | n/a | TBD | RAGAS/custom-metric judge |
| embeddings | TBD (`nim`/`local` + model, else `hash`) | n/a | n/a | tests always `hash` |

## Consequences

Phase 1 implements `nim_provider.py` against the models recorded here. If any
required capability (vision, structured output, a second distinct model) is missing
from the human's list, work stops and asks before building around it.
