# Phase 6-7 verification — Quiz engine + learner model (short gate)

Sprint scope per ADR-0008. DB is Neon (hosted PG18 + pgvector).

## What was built (all pushed)

- assess/generate+verify+dedup: MCQ (cross-model solve, distractor consistency),
  numericals (restricted evaluator, best-effort cross-solve), hash+cosine dedup.
- Offline bank: 36 verified MCQs via threaded builder (resumable, cached);
  `docs/review/questions.md` holds 20 for human review.
- learner/model+policy: BKT updates, 2-hop propagation, forgetting, cold priors,
  adaptive choice (score, readiness, prereq-first, interleave, difficulty bands).
- API: students, assessments, adaptive next (opening-8 + fallback loop, no key
  leaked), answers (grading, misconception, citations, mastery delta,
  root-cause trace), finish summary, mastery endpoint, graph with colors.
- Web: quiz runner (why-this-question, feedback, citations, trace link),
  summary page, map colored by mastery with icons + trace highlight.

## Tails

$ ruff check/format, mypy strict → clean (55+ files)
$ pytest (mock) → assess 5, learner 7, tutor/graph/ingest pass
$ pytest tests/test_quiz_api.py (Neon) → 2 passed: no-key-before-answer proven,
  wrong-answer feedback + mastery + summary proven
$ bank: 36 verified stored (MCQ; numericals deferred — none in bank)

## Scripted proof (6 deliberate wrong answers, fresh student)

- Q1–Q6 all correct=False; deltas −0.03…−0.13; misconceptions captured
  ("Ignoring the Denominator", "P(A|B) = P(B|A)", …); 1 root-cause trace fired
  (→ Probability Axioms); reasons recorded each item.
- Mastery 0.30 → 0.16–0.26 on touched concepts; summary score=0/6 with weak
  topics (now named) + likely misconceptions.
- Latencies: next 13–54 s, answers 14–51 s (many sequential Neon round trips
  from this host — works, but slow; batch the mastery snapshot before demo).

## Deviations

- ADR-0008: MCQ-first, no short-answer/figures/diagnostic-mode/dashboard;
  bank offline only.
- JUDGE still glimmer (Phase 8 will use it); chat accepted as-is (3/5).
- `next` falls back across concepts instead of 404 on bank miss.
- Shell environments vary per call here: venv binaries used directly;
  hook prefers venv ruff.

## Threats

- Per-answer latency (15–50 s) will hurt the demo video — batch DB reads in
  the quiz path before recording, or run the API closer to Neon.
- Bank depth thin (36/22 concepts) — fallback loop covers, but more MCQs help.
- Clock: build freeze 14:30; Phase 8 (eval) + video + submission remain.
