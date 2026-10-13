"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Course {
  id: string;
  title: string;
  description: string;
}

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ courses: Course[] }>("/api/courses")
      .then((d) => setCourses(d.courses))
      .catch(() => setError("Could not reach the API."));
  }, []);

  return (
    <main>
      <h1>Library</h1>
      {error && <p role="alert">{error}</p>}
      <ul>
        {courses.map((c) => (
          <li key={c.id}>
            <Link href={`/courses/${c.id}`}>{c.title}</Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
