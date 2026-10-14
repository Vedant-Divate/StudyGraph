# ADR-0005: LLM provider is NVIDIA NIM (all models confirmed)

- Status: accepted
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

All IDs confirmed verbatim from the human's working snippets (2026-10-12).

| Role | Model ID | Vision? | Structured-output mode | Notes |
|------|----------|---------|------------------------|-------|
| `LLM_MODEL` (chat) | `nvidia/nemotron-3.5-lightning-30b-a3b` | no (text) | schema-prompt + validate + retry (tool calling exists; verify in Phase 1) | fast 30B A3B MoE, agentic; reasoning via `enable_thinking` + budget |
| `VISION_MODEL` | `meta/muse-glimmer-30b` | yes | schema-prompt + validate + retry (native tool calling per card; verify in Phase 1) | 30B multimodal reasoning; fallback if weak: `meta/llama-3.2-11b-vision-instruct` (unconfirmed) |
| `VERIFIER_MODEL` | `openai/gpt-oss-20b` | n/a | schema-prompt + validate + retry | ≠ chat; math/reasoning, small/fast |
| `JUDGE_MODEL` | `meta/muse-glimmer-30b` (same model as vision) | yes | schema-prompt + validate + retry | ≠ chat. `z-ai/glm-5.3` was unresponsive in smoke (no bytes in 150 s even streaming, 2026-10-13); revisit post-deadline. Judge latency ~20–30 s is acceptable (eval is manual). |
| embeddings | `nvidia/nemotron-3-embed-1b` via `EMBED_BACKEND=nim` | n/a | n/a | request shape: `{model, input, input_type: query\|passage, encoding_format: float, truncate: END}`; tests always `hash` |

All chat models accept non-streaming `chat.completions.create` (observed working
params: temperature 0.5–1, top_p 0.95–1). Two model-behavior findings from the
2026-10-13 smoke test (recorded, built around — not guessed):
- `meta/muse-glimmer-30b` returns `content: null` with the full analysis in
  `reasoning_content` for vision calls; `vision_describe` falls back to
  `reasoning_content` when content is empty. `chat_template_kwargs:
  {enable_thinking: false}` is rejected (HTTP 400), so thinking stays on.
- Structured JSON via schema prompt works on `LLM_MODEL` first try
  (`{"answer": ...}` parsed cleanly).

## Consequences

Phase 1 implements `nim_provider.py` against the models recorded here. If any
required capability (vision, structured output, a second distinct model) is missing
from the human's list, work stops and asks before building around it.

## Addendum — NIM candidate availability probe (2026-10-13)

The NIM `/models` endpoint was queried using the key from the local environment;
the key was not printed or recorded. Each listed candidate received one tiny text
prompt (`Reply with OK.`). These are availability/latency checks only and do not
change any configured model.

| Requested candidate | Exact catalog ID | Prompt latency/result |
|---|---|---|
| `deepseek-v4.1-flash` | `deepseek-ai/deepseek-v4.1-flash` | 25,682 ms; timed out |
| `gemma-4-31b-it` | `google/gemma-4-31b-it` | 25,352 ms; timed out |
| `nemotron-3-super-120b-a12b` | `nvidia/nemotron-3-super-120b-a12b` | 1,363 ms; success |
| `glm-5-3-flash` | `z-ai/glm-5.3-flash` | 12,406 ms; success |
| `llama-3.2-11b-vision-instruct` | `meta/llama-3.2-11b-vision-instruct` | 254 ms; success |

No candidate was selected or substituted for the configured chat, vision,
verifier, judge, or embedding models.

## Addendum — chat latency and reasoning control (2026-10-14)

The configured chat model and verifier were timed using a realistic answer and
verification prompt with eight retrieved units. The structured responses were
validated against Pydantic models:

| Role / probe | Model ID | Latency | Timed out | Pydantic result |
|---|---|---:|---|---|
| Generation, reasoning default | `nvidia/nemotron-3.5-lightning-30b-a3b` | 30.947 s | no | valid |
| Verifier | `openai/gpt-oss-20b` | 5.385 s | no | valid |
| Tiny reasoning-control request | `nvidia/nemotron-3.5-lightning-30b-a3b` | 0.317 s | no | accepted |
| Generation, `enable_thinking=false` | `nvidia/nemotron-3.5-lightning-30b-a3b` | 8.656 s | no | valid on standalone repeat |

The tiny request verified that this chat deployment accepts the documented
`extra_body.chat_template_kwargs.enable_thinking` parameter. Generation now
passes `enable_thinking=false` and uses a 90-second role deadline; the separate
verifier has a 60-second role deadline. The NIM provider disables network
retries for structured calls and counts a schema-correction attempt against
the role deadline. No model ID changed, so no alternate catalog candidates
were needed. The live route transcript and per-question verifier outcomes are
recorded in `docs/verification/phase-3-4-5.md`.

The [NVIDIA NIM gpt-oss-20b model page](https://build.nvidia.com/openai/gpt-oss-20b)
documents low/medium/high reasoning effort set through the system prompt. A
tiny structured-output test using the system prefix `Reasoning: low.` completed
in 1.534 s and returned valid JSON. The verifier call now uses that documented
low-reasoning hint; its model ID is unchanged.
