"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { SiteShell } from "@/components/site-shell";
import { disclaimers } from "@/copy";
import { api } from "@/lib/api";

interface Summary {
  score: number;
  total: number;
  course_id: string;
  by_concept: Record<string, { correct: number; total: number }>;
  weak_concepts: string[];
  likely_misconceptions: { label: string; origin: string; count: number }[];
  mastery: Record<string, number>;
  next: string;
}

export default function ReportPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ student?: string }>;
}) {
  const { id } = use(params);
  const query = use(searchParams);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api<Summary>(`/api/assessments/${id}/finish`, {
        method: "POST",
      });
      setSummary(result);
    } catch {
      setError("We couldn’t prepare your summary. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  const percentage =
    summary && summary.total > 0
      ? Math.round((summary.score / summary.total) * 100)
      : 0;

  return (
    <SiteShell active="library">
      <main>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/courses">Library</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Quiz summary</span>
        </nav>
        <header className="page-heading">
          <p className="eyebrow">Take stock, then take the next step</p>
          <h1>Your quiz summary</h1>
          <p className="lede">
            A snapshot of what felt solid and what may be worth revisiting.
          </p>
        </header>
        {loading && (
          <p className="status-row" role="status">
            <span className="spinner" aria-hidden="true" />
            Bringing your results together…
          </p>
        )}
        {error && (
          <div className="status-error" role="alert">
            <p>{error}</p>
            <button className="button-secondary" onClick={() => void loadSummary()}>
              Try again
            </button>
          </div>
        )}
        {summary && !loading && (
          <>
            <section className="summary-hero" aria-labelledby="score-title">
              <div>
                <p className="eyebrow">Your result</p>
                <h2 id="score-title">
                  {summary.score} of {summary.total} correct
                </h2>
                <p className="muted">
                  {percentage}% on this checkpoint. Use the notes below to guide your
                  next study session.
                </p>
              </div>
              <div className="score-mark" aria-label={`${percentage} percent`}>
                {percentage}%
              </div>
            </section>
            <div className="summary-grid">
              <section className="panel" aria-labelledby="revisit-title">
                <div className="panel-heading">
                  <h2 id="revisit-title">Worth another look</h2>
                </div>
                {summary.weak_concepts.length > 0 ? (
                  <ul className="plain-list">
                    {summary.weak_concepts.map((concept) => (
                      <li key={concept} className="concept-list-item">
                        {concept}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No topics were flagged for review this time.</p>
                )}
              </section>
              <section className="panel" aria-labelledby="misconceptions-title">
                <div className="panel-heading">
                  <h2 id="misconceptions-title">Thinking patterns to notice</h2>
                </div>
                {summary.likely_misconceptions.length > 0 ? (
                  <ul className="plain-list">
                    {summary.likely_misconceptions.map((misconception) => (
                      <li key={misconception.label} className="concept-list-item">
                        <strong>{misconception.label}</strong>
                        <span className="muted">
                          {misconception.origin} · noticed {misconception.count}×
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No recurring misconception was identified.</p>
                )}
              </section>
              <section className="panel" aria-labelledby="next-step-title">
                <p className="eyebrow">One next step</p>
                <h2 id="next-step-title">Keep the momentum</h2>
                <p>{summary.next}</p>
                <div className="course-toolbar">
                  {query.student && (
                    <Link
                      className="button-primary"
                      href={`/courses/${summary.course_id}/map?student=${query.student}`}
                    >
                      Open your knowledge map
                    </Link>
                  )}
                  <Link className="button-secondary" href={`/courses/${summary.course_id}`}>
                    Back to course
                  </Link>
                </div>
              </section>
            </div>
          </>
        )}
        <aside className="disclaimer-inline">{disclaimers.simulated}</aside>
      </main>
    </SiteShell>
  );
}
