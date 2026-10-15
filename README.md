# StudyGraph

A source-grounded, misconception-aware AI study companion. Upload lecture videos,
textbooks and slides; it builds a cited concept graph from them, answers questions
only from that material (flagging or refusing everything else), generates verified
misconception-tagged quizzes, and keeps a per-concept learner model that decides
what to teach and ask next — with measured evidence that the personalization works.

Built for Track D (Personalized Tutoring & Adaptive Learning) of the Multimodal AI
Hackathon 2026.

- Answers are generated from the material you uploaded and can contain errors.
  Check the cited source.
- Content marked "Outside your material" is general AI knowledge, not from your course.
- Simulated-student results are simulations, not results from real learners.

## Problem and who it's for

Students study from lecture videos, textbooks and slides scattered across places.
General chatbots answer confidently but are not tied to the course material or to
what the student already understands. Existing "chat with your PDF" tools stop at
text retrieval: they ignore video and diagrams, do not model prerequisites,
generate unverified quiz questions and do not measure whether they help.
StudyGraph is for undergraduates studying for exams, self-learners using open
courses, and instructors/evaluators who need evidence that answers are grounded,
questions are correct, and personalization measurably improves outcomes.

## How it works

```
Browser (Next.js: library, chat, quiz, knowledge map, eval page)
        │ HTTP/JSON
FastAPI ─┬─ ingestion (PDF pages, video transcripts+frames, figure descriptions)
         ├─ kb (embeddings, hybrid retrieval, concept graph, tagging)
         ├─ tutor (grounded generation → verifier → labelled, cited answer)
         ├─ assess (verified MCQ/numericals, grading, misconception reports)
         ├─ learner (BKT + propagation + forgetting, adaptive selection)
         └─ llm (NVIDIA NIM provider, mock for tests)
PostgreSQL + pgvector (units, concepts, questions, mastery, jobs)
```

A student asks a question; the API retrieves the top units, the LLM answers in
labelled segments citing only `unit_id`s it was given, a different model verifies
each cited segment, and the server resolves citations to exact pages, slides or
video timestamps. Wrong quiz answers trace to a named misconception and then to
the weakest prerequisite, with cited recap material.

## Track and criteria addressed

Knowledge Base & Grounding (20%), Assessment Quality (15%), Personalization
Effectiveness (20%), UX & Demo Video (15%), System Evaluation (15%), Technical
Implementation (15%). See `docs/verification/eval-results.md` for the measured
evidence behind each claim.

## What's novel

- **Server-resolved citations**: the model only ever emits `unit_id`s; pages,
  slides and timestamps are resolved server-side and open at the exact location.
- **Three-way answer labels + verifier**: every segment is `source_backed`,
  `outside_knowledge` or `not_covered`, with a cross-model support check.
- **Verified, misconception-tagged MCQs**: cross-model solving, distractor
  consistency checks, dedup; wrong answers name the misconception.
- **BKT learner model with prerequisite propagation** driving an adaptive
  policy and a mastery-coloured Knowledge Map with root-cause traces.

## Tech stack

Next.js + TypeScript + Cytoscape.js + Tailwind (web); Python 3.12, FastAPI,
SQLAlchemy + Alembic, `uv` (API); PostgreSQL + pgvector (Neon hosted or Docker);
faster-whisper (CPU ASR), PyMuPDF, LibreOffice, ffmpeg; NVIDIA NIM models —
chat `nvidia/nemotron-3.5-lightning-30b-a3b`, vision `meta/muse-glimmer-30b`,
verifier `openai/gpt-oss-20b`, judge `openai/gpt-oss-20b` (eval), embeddings
`nvidia/nemotron-3-embed-1b`; mocks for all tests. See
`docs/decisions/ADR-0002-versions.md` and `ADR-0005`.

## Quick start

```bash
cp .env.example .env            # then put NIM_API_KEY (+ Neon DATABASE_URL) in .env.local
docker compose up -d db         # or point DATABASE_URL at Neon
cd services/api && alembic upgrade head
bash scripts/fetch_demo_course.sh        # downloads OCW slides/video + textbook (not committed)
python scripts/store_cached_artifacts.py # loads the cached course into Postgres
uvicorn app.main:app                     # API on :8000 (services/api)
cd apps/web && pnpm install && pnpm dev  # web on :3000
```

`make verify` runs the full gate (ruff, mypy, pytest on mocks, typecheck, lint,
tests, web build, secret scan). CI runs it per commit.

## Evaluation

Full numbers, seeds and caveats: `docs/verification/eval-results.md` (test set
`eval/testset/rag.jsonl`, 30 items, sha16 `a16b8cd2d2b41651`).

- Retrieval (Neon + NIM embeddings, k=5, n=22): recall@5 **0.605**, MRR **0.792**.
- Refusal: precision **0.60**, recall **0.55** (unrelated 1.0, near-miss 0.2,
  false-premise 0.67).
- Citation accuracy: **15/22** overall, **15/16** on answered items; label
  accuracy **8/10** hand-checked.
- RAGAS-style custom judge (not the RAGAS library): faithfulness **0.75**,
  answer relevancy **0.93**, context precision **0.32**, context recall **0.53**.
- Simulated-student ablation (30 students × 5 profiles × 3 policies): under the
  tested forgetting regime, gains are negative in all cells and adaptive does
  not beat random/sequential — reported honestly with CIs and failure analysis
  in the file. Simulated, not real learners.
- **Not completed / not quotable**: the test set is LLM-drafted and
  **unreviewed** (`docs/review/testset-check.md`); the label subset is 10, not
  20; reruns may vary slightly (no ORDER BY in vector ranking).

## Known limits

- Chat produced supported citations for 3 of 5 in-scope probes in the last
  scripted transcript.
- Quiz answers take 14–51 s (sequential database round trips; batch before demo).
- Numerical, figure-dependent and short-answer questions were not built; the
  bank holds 36 verified MCQs and is thin per concept.
- No public deployment — runs locally (or the same compose stack on a VM).
- Full RAGAS-library evaluation was not run (custom RAGAS-style judge instead).

## Demo course attributions and licences

- MIT OpenCourseWare 6.041SC, *Probabilistic Systems Analysis and Applied
  Probability* (Fall 2013, Prof. John Tsitsiklis) — CC BY-NC-SA 4.0
  (https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/).
  Lecture videos/slides used non-commercially with attribution; see
  `data/demo-course/ATTRIBUTIONS.md`.
- OpenStax *Introductory Statistics 2e* (Illowsky/Dean) — CC BY-NC-SA 4.0
  (https://openstax.org/details/books/introductory-statistics-2e), Ch 3–4 used.

## AI-assisted development disclosure

Built with GitHub Copilot and Claude (opencode) under human direction, using a
written specification; NVIDIA NIM hosted models listed above. Per the hackathon
rules this is disclosed here and in Built With.

## Licence

Code: MIT (see LICENSE). Demo course material keeps its own licences above
(CC BY-NC-SA 4.0, non-commercial, attribution required).
