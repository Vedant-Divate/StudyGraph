"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Source {
  id: string;
  kind: string;
  filename: string;
  status: string;
}

export default function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [graph, setGraph] = useState<{ concepts: { id: string; name: string }[] } | null>(
    null,
  );

  useEffect(() => {
    api<{ concepts: { id: string; name: string }[] }>(`/api/courses/${id}/graph`)
      .then(setGraph)
      .catch(() => setGraph(null));
  }, [id]);

  return (
    <main>
      <h1>Course</h1>
      <nav>
        <ul>
          <li>
            <Link href={`/courses/${id}/chat`}>Tutor chat</Link>
          </li>
          <li>
            <Link href={`/courses/${id}/map`}>Knowledge map</Link>
          </li>
          <li>
            <StartQuiz courseId={id} />
          </li>
        </ul>
      </nav>
      <h2>Sources</h2>
      <SourceList courseId={id} />
      <h2>Concepts ({graph?.concepts.length ?? 0})</h2>
      <ul>
        {(graph?.concepts ?? []).map((c) => (
          <li key={c.id}>{c.name}</li>
        ))}
      </ul>
    </main>
  );
}

function StartQuiz({ courseId }: { courseId: string }) {
  const [busy, setBusy] = useState(false);

  async function start() {
    setBusy(true);
    try {
      const student = await api<{ id: string }>("/api/students", {
        method: "POST",
        body: JSON.stringify({ course_id: courseId }),
      });
      const assessment = await api<{ id: string }>(
        `/api/courses/${courseId}/assessments`,
        {
          method: "POST",
          body: JSON.stringify({
            student_id: student.id,
            mode: "adaptive",
            scope: { all: true },
            n: 8,
          }),
        },
      );
      window.location.href = `/quiz/${assessment.id}?student=${student.id}`;
    } finally {
      setBusy(false);
    }
  }

  return (
    <button onClick={() => void start()} disabled={busy}>
      Start adaptive quiz (8 questions)
    </button>
  );
}

function SourceList({ courseId }: { courseId: string }) {  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    api<{ sources: Source[] }>(`/api/courses/${courseId}/sources`)
      .then((d) => setSources(d.sources))
      .catch(() => setSources([]));
  }, [courseId]);

  if (sources.length === 0) return <p>No sources ingested yet.</p>;
  return (
    <ul>
      {sources.map((s) => (
        <li key={s.id}>
          <Link href={`/source/${s.id}`}>{s.filename}</Link> ({s.kind}, {s.status})
        </li>
      ))}
    </ul>
  );
}
