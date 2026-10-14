"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { disclaimers } from "@/copy";

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

  useEffect(() => {
    api<Summary>(`/api/assessments/${id}/finish`, { method: "POST" })
      .then(setSummary)
      .catch(() => setSummary(null));
  }, [id]);

  return (
    <main>
      <h1>Quiz summary</h1>
      {!summary && <p>Loading…</p>}
      {summary && (
        <>
          <p>
            Score: {summary.score}/{summary.total}
          </p>
          <h2>Weak topics</h2>
          <ul>
            {summary.weak_concepts.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
          <h2>Likely misconceptions</h2>
          <ul>
            {summary.likely_misconceptions.map((m) => (
              <li key={m.label}>
                {m.label} ({m.origin}, ×{m.count})
              </li>
            ))}
          </ul>
          <p>{summary.next}</p>
          {query.student && (
            <p>
              <Link href={`/courses/${summary.course_id}/map?student=${query.student}`}>
                Open knowledge map
              </Link>
            </p>
          )}
        </>
      )}
      <p>{disclaimers.simulated}</p>
    </main>
  );
}
