"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { SiteShell } from "@/components/site-shell";
import { API_BASE, api } from "@/lib/api";

interface SourceInfo {
  id: string;
  kind: string;
  filename: string;
  status: string;
}

export default function SourceViewer({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ page?: string; slide?: string; t?: string }>;
}) {
  const { id } = use(params);
  const query = use(searchParams);
  const page = query.page ? Number(query.page) : null;
  const slide = query.slide ? Number(query.slide) : null;
  const time = query.t ? Number(query.t) : null;
  const hasLocation = page !== null || slide !== null || time !== null;
  const [source, setSource] = useState<SourceInfo | null>(null);
  const [sourceError, setSourceError] = useState("");
  const [mediaState, setMediaState] = useState<"loading" | "ready" | "error">(
    "loading",
  );

  useEffect(() => {
    let active = true;
    setSource(null);
    setSourceError("");
    setMediaState("loading");
    api<SourceInfo>(`/api/sources/${id}`)
      .then((result) => {
        if (active) setSource(result);
      })
      .catch(() => {
        if (active) setSourceError("We couldn’t find this source in your course.");
      });
    return () => {
      active = false;
    };
  }, [id]);

  useEffect(() => {
    setMediaState("loading");
  }, [id, page, slide, time]);

  const sourceUrl = `${API_BASE}/api/sources/${id}/file`;
  const videoTime = time ?? 0;
  const showVideo = time !== null || (!hasLocation && source?.kind === "video");

  return (
    <SiteShell active="library">
      <main>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/courses">Library</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Source viewer</span>
        </nav>
        <header className="page-heading">
          <p className="eyebrow">Back to the original</p>
          <h1>{source?.filename ?? "Source viewer"}</h1>
          <p className="lede">
            Review the material behind this citation, at the page, slide, or moment
            you’re studying.
          </p>
        </header>
        {sourceError && <p className="status-error" role="alert">{sourceError}</p>}
        {!source && !sourceError && (
          <p className="status-row" role="status">
            <span className="spinner" aria-hidden="true" />
            Finding your source…
          </p>
        )}
        {source && (
          <>
            <p className="muted">
              {hasLocation
                ? page !== null
                  ? `Page ${page}`
                  : slide !== null
                    ? `Slide ${slide}`
                    : `Video · ${formatTime(videoTime)}`
                : `${source.kind} · ${source.status}`}
            </p>
          <section className="media-frame" aria-label="Source material">
            {mediaState === "loading" && (
              <p className="media-state" role="status">
                <span className="spinner" aria-hidden="true" /> Loading your source…
              </p>
            )}
            {mediaState === "error" && (
              <p className="media-state status-error" role="alert">
                The source couldn’t be displayed. Try opening this citation again from
                your course.
              </p>
            )}
            {page !== null && (
              <iframe
                title={`Source page ${page}`}
                src={`${sourceUrl}#page=${page}`}
                onLoad={() => setMediaState("ready")}
                onError={() => setMediaState("error")}
              />
            )}
            {slide !== null && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                alt={`Source slide ${slide}`}
                src={`${API_BASE}/api/sources/${id}/page/${slide}`}
                onLoad={() => setMediaState("ready")}
                onError={() => setMediaState("error")}
              />
            )}
            {showVideo && (
              <VideoSource
                src={sourceUrl}
                time={videoTime}
                onReady={() => setMediaState("ready")}
                onError={() => setMediaState("error")}
              />
            )}
            {!showVideo && page === null && slide === null && (
              <iframe
                title={`${source.filename} full document`}
                src={sourceUrl}
                onLoad={() => setMediaState("ready")}
                onError={() => setMediaState("error")}
              />
            )}
          </section>
          </>
        )}
      </main>
    </SiteShell>
  );
}

function VideoSource({
  src,
  time,
  onReady,
  onError,
}: {
  src: string;
  time: number;
  onReady: () => void;
  onError: () => void;
}) {
  const [video, setVideo] = useState<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (video) video.currentTime = time;
  }, [video, time]);

  return (
    <video
      ref={setVideo}
      aria-label="Course source video"
      controls
      preload="metadata"
      src={src}
      onLoadedData={onReady}
      onError={onError}
    />
  );
}

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60);
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}
