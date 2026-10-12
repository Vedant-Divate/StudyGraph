# ADR-0005: LLM provider is NVIDIA NIM (endpoint + chat locked, rest proposed)

- Status: accepted (endpoint/chat confirmed 2026-10-12; vision/verifier/judge/embed IDs await human confirmation)
- Date: 2026-10-12
- Phase: 0

## Context

Amendment 1 to PROJECT.md: AI provider is NVIDIA NIM behind the provider interface
(Sections 6/8), not Anthropic. Model IDs are configuration, never guessed. Phase 0
adds config, the provider-interface stub, the mock provider and this ADR — no live
API calls.

## Decision (structure; values pending)

- Endpoint is OpenAI-compatible: `NIM_BASE_URL=https://integrate.api.nvidia.com/v1`
  (confirmed from the human's working snippet). Client: the `openai` package
  against `NIM_BASE_URL` (allowed by PROJECT.md 14.1 since the docs confirm an
  OpenAI-compatible API); plain `httpx` fallback stays available.
- One `$NVIDIA_API_KEY` serves all models; it lives only in `.env.local` (gitignored)
  and the deploy environment. Never printed, echoed, or committed.
- Env vars: `LLM_PROVIDER=nim|mock`, `NIM_BASE_URL`, `NIM_API_KEY`, `LLM_MODEL`
  (chat), `VISION_MODEL` (vision-capable, for figures/frames), `VERIFIER_MODEL`
  (≠ `LLM_MODEL`), `JUDGE_MODEL` (≠ `LLM_MODEL`), `EMBED_BACKEND` (`nim|local|hash`),
  `EMBED_MODEL`, `LLM_RPM` + `LLM_CONCURRENCY` caps.
- Structured output: schema-prompt + Pydantic validate + one retry fallback, unless
  a chosen model documents guided/forced JSON — recorded per model below once known.
- Reasoning models (e.g. Nemotron-3.5) accept `extra_body.chat_template_kwargs`
  (`enable_thinking`) plus a `reasoning_budget`, and stream `reasoning_content`
  deltas; `nim_provider` (Phase 1) must read `delta.content` only and ignore
  reasoning deltas. Observed defaults: `temperature=1`, `top_p=0.95`.
- Rate limiting/backoff configurable (`LLM_RPM` unset — no limits published on the
  account so far; start conservative); LLM responses cached by input hash during
  ingestion/eval; tests/CI use the mock provider only.
- Key handling: never printed, echoed, or written into any committed file, doc, ADR,
  log or verification output; rotate after the hackathon.

## Chosen models

Confirmed IDs come from the human's snippets; proposed IDs are NOT used until the
human confirms the exact string.

| Role | Model ID | Status | Vision? | Structured-output mode | Notes |
|------|----------|--------|---------|------------------------|-------|
| `LLM_MODEL` (chat) | `nvidia/nemotron-3.5-lightning-30b-a3b` | confirmed | no (text) | schema-prompt + validate + retry (tool calling exists; verify in Phase 1) | fast 30B A3B MoE, agentic |
| `VISION_MODEL` | `meta/muse-glimmer-30b` (proposed) | **awaiting exact ID** | must be yes | TBD (native tool calling per card) | fallback: `meta/llama-3.2-11b-vision-instruct` (proposed) |
| `VERIFIER_MODEL` | `openai/gpt-oss-20b` (proposed) | **awaiting exact ID** | n/a | schema-prompt + validate + retry | ≠ chat; math/reasoning, small/fast |
| `JUDGE_MODEL` | `z-ai/glm-5-3` (proposed) | **awaiting exact ID** | n/a | schema-prompt + validate + retry | ≠ chat; 753B reasoner |
| embeddings | `nvidia/nemotron-3-embed-1b` (proposed), `EMBED_BACKEND=nim` | **awaiting exact ID** | n/a | n/a | tests always `hash` |

## Consequences

Phase 1 implements `nim_provider.py` against the models recorded here. If any
required capability (vision, structured output, a second distinct model) is missing
from the human's list, work stops and asks before building around it.
