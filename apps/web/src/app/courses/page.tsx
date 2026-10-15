"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { SiteShell } from "@/components/site-shell";

interface Course {
  id: string;
  title: string;
  description: string;
}

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadCourses() {
    setLoading(true);
    setError("");
    try {
      const data = await api<{ courses: Course[] }>("/api/courses");
      setCourses(data.courses);
    } catch {
      setError("We couldn’t load your library. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCourses();
  }, []);

  return (
    <SiteShell active="library">
      <main>
        <header className="page-heading">
          <p className="eyebrow">Your learning, gathered here</p>
          <h1>Your library</h1>
          <p className="lede">
            Open a course to explore its sources, connected concepts, and study tools.
          </p>
        </header>
        {loading && (
          <p className="status-row" role="status">
            <span className="spinner" aria-hidden="true" />
            Gathering your courses…
          </p>
        )}
        {error && (
          <div className="status-error" role="alert">
            <p>{error}</p>
            <button className="button-secondary" onClick={() => void loadCourses()}>
              Try again
            </button>
          </div>
        )}
        {!loading && !error && courses.length === 0 && (
          <div className="status-row">
            Your library is empty for now. Courses will appear here when they’re ready.
          </div>
        )}
        {courses.length > 0 && (
          <section className="course-grid" aria-label="Available courses">
            {courses.map((course, index) => (
              <article className="course-card" key={course.id}>
                <span className="course-symbol" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h2>{course.title}</h2>
                {course.description && (
                  <p className="course-description">{course.description}</p>
                )}
                <Link className="card-link" href={`/courses/${course.id}`}>
                  Open course <span aria-hidden="true">→</span>
                </Link>
              </article>
            ))}
          </section>
        )}
      </main>
    </SiteShell>
  );
}
