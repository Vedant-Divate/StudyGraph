# StudyGraph

> **Status: Phase 0 — Foundations.** The app skeleton (web + api + worker + db) is
> being built. See [PROJECT.md](PROJECT.md) (ground truth) and
> [docs/verification/phase-0.md](docs/verification/phase-0.md) for progress.

StudyGraph is a source-grounded, misconception-aware AI study companion that turns
lecture videos, textbooks and slides into a cited concept graph, then tutors and
assesses each student against it. Built for Track D (Personalized Tutoring &
Adaptive Learning) of the Multimodal AI Hackathon 2026.

- Answers are generated from the material you uploaded and can contain errors.
  Check the cited source.
- Content marked "Outside your material" is general AI knowledge, not from your course.
- Simulated-student results are simulations, not results from real learners.

## Quick start (Phase 0)

```bash
cp .env.example .env
docker compose up --build
curl localhost:8000/api/health
```

Open http://localhost:3000 for the landing page.

## Docs

- [PROJECT.md](PROJECT.md) — specification (wins over code unless an ADR amends it)
- [docs/decisions/](docs/decisions/) — architecture decision records
- [docs/verification/](docs/verification/) — per-phase verification evidence
- [docs/questions.md](docs/questions.md) — open questions and assumption log

Built with an AI coding agent (opencode) under human direction using PROJECT.md.
AI-assisted development is disclosed here per the hackathon rules.
