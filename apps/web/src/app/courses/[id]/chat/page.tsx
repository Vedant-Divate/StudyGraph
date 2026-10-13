"use client";

import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";
import { API_BASE, api, type ChatSegment } from "@/lib/api";
import { disclaimers } from "@/copy";

interface ChatResponse {
  segments: ChatSegment[];
  confidence: number;
}

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [messages, setMessages] = useState<ChatSegment[][]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [allowOutside, setAllowOutside] = useState(false);
  const liveRef = useRef<HTMLDivElement>(null);

  async function send(outside: boolean) {
    if (!input.trim() || busy) return;
    setBusy(true);
    try {
      const res = await api<ChatResponse>(`/api/courses/${id}/chat`, {
        method: "POST",
        body: JSON.stringify({ message: input, allow_outside: outside }),
      });
      setMessages((m) => [...m, res.segments]);
      setInput("");
    } catch {
      setMessages((m) => [
        ...m,
        [{ text: "The tutor is unreachable.", label: "not_covered", unit_ids: [], citations: [] }],
      ]);
    } finally {
      setBusy(false);
    }
  }

  const lastSegments = messages[messages.length - 1] ?? [];
  const refused =
    lastSegments.length === 1 && lastSegments[0].label === "not_covered";

  return (
    <main>
      <h1>Tutor chat</h1>
      <p>
        <Link href={`/courses/${id}`}>Back to course</Link>
      </p>
      <div ref={liveRef} aria-live="polite">
        {messages.map((segments, i) => (
          <div key={i}>
            {segments.map((s, j) => (
              <SegmentView key={j} segment={s} />
            ))}
          </div>
        ))}
      </div>
      {refused && !allowOutside && (
        <button
          onClick={() => {
            setAllowOutside(true);
            void send(true);
          }}
        >
          Show general-knowledge answer
        </button>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setAllowOutside(false);
          void send(false);
        }}
      >
        <label>
          Ask about your material
          <input value={input} onChange={(e) => setInput(e.target.value)} />
        </label>
        <button type="submit" disabled={busy}>
          Send
        </button>
      </form>
      <p>{disclaimers.generated}</p>
      <p>{disclaimers.outside}</p>
    </main>
  );
}

function SegmentView({ segment }: { segment: ChatSegment }) {
  const cls =
    segment.label === "source_backed"
      ? "seg-backed"
      : segment.label === "outside_knowledge"
        ? "seg-outside"
        : "seg-uncovered";
  return (
    <div className={cls}>
      <p>
        {segment.label === "outside_knowledge" && <strong>Outside your material: </strong>}
        {segment.text}
        {segment.check_source && <em> (check the source)</em>}
      </p>
      {segment.citations.map((c) => (
        <Link key={c.unit_id} href={c.link}>
          {c.display}
        </Link>
      ))}
      {segment.related_topics?.map((t) => <span key={t}>{t} </span>)}
    </div>
  );
}
