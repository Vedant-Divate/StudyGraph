# Agent instructions for StudyGraph

Read `PROJECT.md` fully before writing any code. It is the ground truth.

Rules:

1. Work one phase at a time (PROJECT.md Section 15). Do not start the next phase
   until the current phase's Verification Gate is written to
   `docs/verification/phase-N.md` with real, pasted command output.
2. After implementing and verifying each individual feature (not the whole
   phase), commit it separately using Conventional Commits
   (PROJECT.md Section 14.3). Never use `git commit --no-verify`.
3. Run `make verify` before every commit. Do not commit if it fails.
4. Never invent requirements not in PROJECT.md. If something is ambiguous,
   apply the documented default, log it in `docs/questions.md`, and continue.
5. Any deviation from PROJECT.md requires an ADR in `docs/decisions/`
   (template in PROJECT.md Appendix C), committed in the same or an earlier commit.
6. Never commit secrets. `.env.example` only, with placeholders.
7. `app/domain` must not import other app packages or do I/O. The web app talks
   to the API over HTTP only.
8. Citations are resolved server-side from `unit_id`. The LLM must never output
   a page, slide or timestamp. Never execute model-generated code.
9. Tests and CI use mock backends only (LLM, ASR, embeddings). Never download
   large models or call paid or live APIs in tests.
10. Any accuracy or gain number you write into docs must come from a script
    output you actually ran. Label simulated results as simulated.
11. AI provider is NVIDIA NIM. Never guess a model ID or endpoint. Choose models
    only from the list the human provides (screenshots) and the NIM docs, and
    record the choice and each model's capabilities in ADR-0005. If a needed
    capability (vision, structured output, a second distinct model) is missing,
    stop and ask.
12. The NIM API key lives only in `.env.local` and the deployment environment.
    Never print it, echo it, or write it into any committed file, doc, ADR, log
    or verification output.
13. Hosting is $0: an Oracle Cloud Always Free arm64 VM running docker compose.
    Build multi-arch images. Never create or change cloud resources yourself;
    the human provisions them.
