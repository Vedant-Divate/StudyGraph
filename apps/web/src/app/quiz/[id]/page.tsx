"use client";

import Link from "next/link";
import { use, useState } from "react";
import { SiteShell } from "@/components/site-shell";
import { api } from "@/lib/api";

interface QuizItem {
  id: string;
  type: string;
  stem: string;
  options: { key: string; text: string }[];
  difficulty: string;
  item_id: string;
  selection_reason: string;
  course_id: string;
}

interface Feedback {
  correct: boolean;
  score: number;
  explanation: string;
  why_wrong: string | null;
  misconception: { label: string; origin: string } | null;
  cited_units: { unit_id: string; display: string; link: string }[];
  mastery_delta: number;
  root_cause: {
    concept: string | null;
    weak_prerequisite: string | null;
    weak_name: string;
    recap: { display: string; link: string }[];
  } | null;
}

export default function QuizPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ student?: string }>;
}) {
  const { id: assessmentId } = use(params);
  const query = use(searchParams);
  const [item, setItem] = useState<QuizItem | null>(null);
  const [choice, setChoice] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [studentId] = useState(query.student ?? "");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadNext() {
    setLoading(true);
    setError("");
    try {
      const next = await api<QuizItem>(`/api/assessments/${assessmentId}/next`);
      setItem(next);
      setFeedback(null);
      setChoice("");
      setDone(false);
    } catch (loadError) {
      if (loadError instanceof Error && loadError.message.startsWith("API 404:")) {
        setItem(null);
        setDone(true);
      } else {
        setError("We couldn’t load the next question. Check your connection and retry.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function submit() {
    if (!item || !choice || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const result = await api<Feedback>(`/api/assessments/${assessmentId}/answers`, {
        method: "POST",
        body: JSON.stringify({
          item_id: item.item_id,
          student_id: studentId,
          choice_key: choice,
        }),
      });
      setFeedback(result);
    } catch {
      setError("Your answer couldn’t be checked. Your selection is still here; try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SiteShell>
      <main className="page-narrow">
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/courses">Library</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Quiz</span>
        </nav>
        <header className="page-heading">
          <p className="eyebrow">A quick check-in</p>
          <h1>Study checkpoint</h1>
          <p className="lede">
            Work through each question at your pace. You’ll get feedback and source links
            after you answer.
          </p>
        </header>
        {error && <p className="status-error" role="alert">{error}</p>}
        {!item && !done && (
          <section className="quiz-card">
            <p className="eyebrow">Ready when you are</p>
            <h2>Let’s see what’s clicking.</h2>
            <p className="muted">
              Your next question is selected from the concepts in this course.
            </p>
            {loading ? (
              <p className="status-row" role="status">
                <span className="spinner" aria-hidden="true" />
                Preparing a question… This can take a little while.
              </p>
            ) : (
              <button className="button-primary" onClick={() => void loadNext()}>
                Load first question
              </button>
            )}
          </section>
        )}
        {item && (
          <section className="quiz-card" aria-labelledby="question-title">
            <div className="quiz-meta">
              <span className="tag">Adaptive question</span>
              <span className="tag">{item.difficulty}</span>
            </div>
            <h2 className="quiz-stem" id="question-title">{item.stem}</h2>
            {!feedback && (
              <>
                <p className="muted">
                  <strong>Why this question?</strong> {item.selection_reason}
                </p>
                <fieldset className="quiz-options" disabled={submitting}>
                  <legend className="field-label">Choose one answer</legend>
                  {item.options.map((option) => (
                    <label className="quiz-option" key={option.key}>
                      <input
                        type="radio"
                        name="choice"
                        value={option.key}
                        checked={choice === option.key}
                        onChange={() => setChoice(option.key)}
                      />
                      <strong>{option.key}.</strong>
                      <span>{option.text}</span>
                    </label>
                  ))}
                </fieldset>
                <button
                  className="button-primary"
                  onClick={() => void submit()}
                  disabled={!choice || submitting}
                >
                  {submitting ? (
                    <>
                      <span className="spinner" aria-hidden="true" /> Checking your answer…
                    </>
                  ) : (
                    "Check answer"
                  )}
                </button>
              </>
            )}
            {feedback && (
              <div
                className={`feedback-card ${feedback.correct ? "" : "is-incorrect"}`}
                aria-live="polite"
              >
                <p className="eyebrow">
                  {feedback.correct ? "✓ Correct" : "Not quite"}
                </p>
                <p>{feedback.explanation}</p>
                {feedback.why_wrong && <p>Why that answer misses: {feedback.why_wrong}</p>}
                {feedback.misconception && (
                  <p>
                    Possible misconception: {feedback.misconception.label} (
                    {feedback.misconception.origin})
                  </p>
                )}
                {feedback.cited_units.length > 0 && (
                  <div>
                    <h3>Review in your source</h3>
                    <div className="citation-list">
                      {feedback.cited_units.map((citation) => (
                        <Link
                          className="citation-link"
                          key={citation.unit_id}
                          href={citation.link}
                        >
                          {citation.display}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
                <p className="muted">
                  Mastery change: {(feedback.mastery_delta * 100).toFixed(1)} points
                </p>
                {feedback.root_cause && (
                  <p>
                    Revisit the prerequisite{" "}
                    <strong>{feedback.root_cause.weak_name}</strong>.{" "}
                    {feedback.root_cause.recap.map((recap) => (
                      <Link key={recap.link} href={recap.link}>
                        {recap.display}{" "}
                      </Link>
                    ))}
                    <Link
                      href={`/courses/${item.course_id}/map?student=${studentId}&trace=${feedback.root_cause.concept},${feedback.root_cause.weak_prerequisite}`}
                    >
                      See this learning trace on the map
                    </Link>
                  </p>
                )}
                <div className="quiz-actions">
                  <button
                    className="button-primary"
                    onClick={() => void loadNext()}
                    disabled={loading}
                  >
                    {loading ? "Loading next question…" : "Next question"}
                  </button>
                  <Link
                    className="button-secondary"
                    href={`/quiz/${assessmentId}/report?student=${studentId}`}
                  >
                    Finish and review
                  </Link>
                </div>
                {loading && (
                  <p className="inline-status" role="status">
                    <span className="spinner" aria-hidden="true" />
                    Preparing your next question…
                  </p>
                )}
              </div>
            )}
          </section>
        )}
        {done && (
          <section className="quiz-card">
            <p className="eyebrow">Checkpoint complete</p>
            <h2>No more questions in this scope.</h2>
            <p className="muted">Review what you learned and choose what to revisit next.</p>
            <Link
              className="button-primary"
              href={`/quiz/${assessmentId}/report?student=${studentId}`}
            >
              View quiz summary
            </Link>
          </section>
        )}
      </main>
    </SiteShell>
  );
}
