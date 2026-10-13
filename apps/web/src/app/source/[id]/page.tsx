"use client";

import { use, useEffect, useRef } from "react";
import { API_BASE } from "@/lib/api";

export default function SourceViewer({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ page?: string; slide?: string; t?: string }>;
}) {
  const { id } = use(params);
  const query = use(searchParams);
  const videoRef = useRef<HTMLVideoElement>(null);

  const page = query.page ? Number(query.page) : null;
  const slide = query.slide ? Number(query.slide) : null;
  const t = query.t ? Number(query.t) : null;

  useEffect(() => {
    if (t !== null && videoRef.current) {
      videoRef.current.currentTime = t;
    }
  }, [t, id]);

  return (
    <main>
      <h1>Source</h1>
      {page !== null && (
        <iframe
          title={`page ${page}`}
          src={`${API_BASE}/api/sources/${id}/file#page=${page}`}
          width="100%"
          height="800"
        />
      )}
      {slide !== null && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          alt={`slide ${slide}`}
          src={`${API_BASE}/api/sources/${id}/page/${slide}`}
          style={{ maxWidth: "100%" }}
        />
      )}
      {t !== null && (
        <video
          ref={videoRef}
          controls
          src={`${API_BASE}/api/sources/${id}/file`}
          style={{ maxWidth: "100%" }}
        />
      )}
      {page === null && slide === null && t === null && <p>No location given.</p>}
    </main>
  );
}
