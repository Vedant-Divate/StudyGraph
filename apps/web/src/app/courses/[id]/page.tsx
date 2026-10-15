"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { SiteShell } from "@/components/site-shell";
import { api } from "@/lib/api";

interface Course {
  id: string;
  title: string;
  description: string;
}

interface Source {
  id: string;
  kind: string;
  filename: string;
  status: string;
}

interface Graph {
  concepts: { id: string; name: string }[];
}

export default function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [course, setCourse] = useState<Course | null>(null);
  const [courseError, setCourseError] = useState("");
  const [graph, setGraph] = useState<Graph | null>(null);
  const [graphError, setGraphError] = useState("");
  const [graphLoading, setGraphLoading] = useState(true);

  useEffect(() => {
    api<{ courses: Course[] }>("/api/courses")
      .then(({ courses }) => {
        const match = courses.find((entry) => entry.id === id);
        if (match) setCourse(match);
        else setCourseError("This course isn’t available in your library.");
      })
      .catch(() => setCourseError("We couldn’t load the course details."));

    setGraphLoading(true);
    setGraphError("");
    api<Graph>(`/api/courses/${id}/graph`)
      .then(setGraph)
      .catch(() => setGraphError("We couldn’t load the concept overview."))
      .finally(() => setGraphLoading(false));
  }, [id]);

  return (
    <SiteShell active="library">
      <main>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/courses">Library</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{course?.title ?? "Course"}</span>
        </nav>
        <header className="page-heading">
          <p className="eyebrow">Your course workspace</p>
          <h1 className="course-title">{course?.title ?? "Course study space"}</h1>
          {course?.description && <p className="lede">{course.description}</p>}
          {courseError && <p className="status-error" role="alert">{courseError}</p>}
          <div className="course-toolbar" aria-label="Course study tools">
            <Link className="button-primary" href={`/courses/${id}/chat`}>
              Ask your tutor
            </Link>
            <Link className="button-secondary" href={`/courses/${id}/map`}>
              Explore knowledge map
            </Link>
            <StartQuiz courseId={id} />
          </div>
        </header>

        <div className="course-overview">
          <section className="panel" aria-labelledby="sources-title">
            <div className="panel-heading">
              <h2 id="sources-title">Course sources</h2>
            </div>
            <SourceList courseId={id} />
          </section>
          <section className="panel" aria-labelledby="concepts-title">
            <div className="panel-heading">
              <h2 id="concepts-title">Concepts</h2>
              <span className="count-label">
                {graphLoading ? "Loading" : graph?.concepts.length ?? 0}
              </span>
            </div>
            {graphLoading && (
              <p className="inline-status" role="status">
                <span className="spinner" aria-hidden="true" />
                Mapping course concepts…
              </p>
            )}
            {graphError && <p className="status-error" role="alert">{graphError}</p>}
            {!graphLoading && !graphError && graph?.concepts.length === 0 && (
              <p className="muted">No concepts have been mapped yet.</p>
            )}
            {!graphLoading && !graphError && graph && graph.concepts.length > 0 && (
              <>
                <ul className="concept-list">
                  {graph.concepts.slice(0, 6).map((concept) => (
                    <li key={concept.id}>{concept.name}</li>
                  ))}
                </ul>
                {graph.concepts.length > 6 && (
                  <p className="muted" style={{ marginTop: "0.8rem", marginBottom: 0 }}>
                    And {graph.concepts.length - 6} more in the knowledge map.
                  </p>
                )}
              </>
            )}
          </section>
        </div>
      </main>
    </SiteShell>
  );
}

function StartQuiz({ courseId }: { courseId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function start() {
    setBusy(true);
    setError("");
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
    } catch {
      setError("We couldn’t prepare your quiz. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button className="button-secondary" onClick={() => void start()} disabled={busy}>
        {busy ? (
          <>
            <span className="spinner" aria-hidden="true" /> Preparing your quiz…
          </>
        ) : (
          "Start an adaptive quiz"
        )}
      </button>
      {error && <p className="status-error" role="alert">{error}</p>}
    </div>
  );
}

function SourceList({ courseId }: { courseId: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadSources = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api<{ sources: Source[] }>(
        `/api/courses/${courseId}/sources`,
      );
      setSources(result.sources);
    } catch {
      setError("We couldn’t load the course sources.");
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void loadSources();
  }, [loadSources]);

  if (loading) {
    return (
      <p className="inline-status" role="status">
        <span className="spinner" aria-hidden="true" />
        Gathering your sources…
      </p>
    );
  }
  if (error) {
    return (
      <div className="status-error" role="alert">
        <p>{error}</p>
        <button className="button-secondary" onClick={() => void loadSources()}>
          Try again
        </button>
      </div>
    );
  }
  if (sources.length === 0) {
    return <p className="muted">No sources are available for this course yet.</p>;
  }

  return (
    <ul className="source-list">
      {sources.map((source) => (
        <li className="source-row" key={source.id}>
          <Link href={`/source/${source.id}`}>{source.filename}</Link>
          <span className="source-kind">
            {source.kind} · {source.status}
          </span>
        </li>
      ))}
    </ul>
  );
}
