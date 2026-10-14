"use client";

import Link from "next/link";
import { use, useState } from "react";
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
  const [error, setError] = useState("");

  async function loadNext(sid: string) {
    setFeedback(null);
    setChoice("");
    try {
      const nxt = await api<QuizItem>(`/api/assessments/${assessmentId}/next`);
      setItem(nxt);
    } catch {
      setDone(true);
    }
  }

  async function submit() {
    if (!item || !choice) return;
    const sid = studentId;
    const fb = await api<Feedback>(`/api/assessments/${assessmentId}/answers`, {
      method: "POST",
      body: JSON.stringify({ item_id: item.item_id, student_id: sid, choice_key: choice }),
    });
    setFeedback(fb);
  }

  return (
    <main>
      <h1>Quiz</h1>
      {error && <p role="alert">{error}</p>}
      {!item && !done && (
        <button
          onClick={() => {
            setError("");
            loadNext(studentId).catch(() => setError("Could not load question."));
          }}
        >
          Load question
        </button>
      )}
      {item && !feedback && (
        <section>
          <p>{item.stem}</p>
          <p>
            <em>Why this question? {item.selection_reason}</em>
          </p>
          {item.options.map((o) => (
            <label key={o.key}>
              <input
                type="radio"
                name="choice"
                value={o.key}
                checked={choice === o.key}
                onChange={() => setChoice(o.key)}
              />
              {o.key}. {o.text}
            </label>
          ))}
          <button onClick={() => void submit()}>Submit</button>
        </section>
      )}
      {feedback && (
        <section aria-live="polite">
          <h2>{feedback.correct ? "✓ Correct" : "✗ Incorrect"}</h2>
          <p>{feedback.explanation}</p>
          {feedback.why_wrong && <p>Why wrong: {feedback.why_wrong}</p>}
          {feedback.misconception && (
            <p>
              Likely misconception: {feedback.misconception.label} (
              {feedback.misconception.origin})
            </p>
          )}
          <ul>
            {feedback.cited_units.map((c) => (
              <li key={c.unit_id}>
                <Link href={c.link}>{c.display}</Link>
              </li>
            ))}
          </ul>
          <p>Mastery change: {(feedback.mastery_delta * 100).toFixed(1)} pts</p>
          {feedback.root_cause && (
            <p>
              Root cause: weak prerequisite <strong>{feedback.root_cause.weak_name}</strong>{" "}
              {feedback.root_cause.recap.map((r) => (
                <Link key={r.link} href={r.link}>
                  {r.display}
                </Link>
              ))}{" "}
              <Link
                href={`/courses/${item?.course_id}/map?student=${studentId}&trace=${feedback.root_cause.concept},${feedback.root_cause.weak_prerequisite}`}
              >
                See trace on map
              </Link>
            </p>
          )}
          <button onClick={() => void loadNext(studentId)}>Next question</button>{" "}
          <Link href={`/quiz/${assessmentId}/report?student=${studentId}`}>Finish</Link>
        </section>
      )}
      {done && <p>No more questions in this scope.</p>}
    </main>
  );
}
