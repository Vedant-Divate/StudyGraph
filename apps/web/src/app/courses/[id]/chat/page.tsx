"use client";

import Link from "next/link";
import { use, useState } from "react";
import { SiteShell } from "@/components/site-shell";
import { disclaimers } from "@/copy";
import { api, type ChatSegment } from "@/lib/api";

interface ChatResponse {
  segments: ChatSegment[];
  confidence: number;
}

interface ChatTurn {
  question: string;
  segments: ChatSegment[];
}

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [allowOutside, setAllowOutside] = useState(false);
  const [error, setError] = useState("");

  async function send(outside: boolean, questionText?: string) {
    const question = (questionText ?? input).trim();
    if (!question || busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await api<ChatResponse>(`/api/courses/${id}/chat`, {
        method: "POST",
        body: JSON.stringify({ message: question, allow_outside: outside }),
      });
      setTurns((current) => [...current, { question, segments: response.segments }]);
      setInput("");
    } catch {
      setError("The tutor couldn’t reach your course material. Your question is still here.");
    } finally {
      setBusy(false);
    }
  }

  const lastTurn = turns[turns.length - 1];
  const refused =
    lastTurn?.segments.length === 1 &&
    lastTurn.segments[0].label === "not_covered";

  return (
    <SiteShell active="library">
      <main>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/courses">Library</Link>
          <span aria-hidden="true">/</span>
          <Link href={`/courses/${id}`}>Course</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Tutor</span>
        </nav>
        <header className="page-heading">
          <p className="eyebrow">Study with your sources</p>
          <h1>Tutor chat</h1>
          <p className="lede">
            Ask a question about your material. Answers include links back to the source.
          </p>
        </header>
        <div className="chat-layout">
          <section className="chat-main" aria-label="Course tutor conversation">
            <div className="chat-transcript" aria-live="polite" aria-relevant="additions">
              {turns.length === 0 && !busy && (
                <div className="chat-welcome">
                  <span className="chat-welcome-mark" aria-hidden="true">
                    ?
                  </span>
                  <h2>What are you working through?</h2>
                  <p>
                    Ask about an idea, a definition, or how two concepts from your course
                    fit together.
                  </p>
                </div>
              )}
              {turns.map((turn, index) => (
                <div className="chat-turn" key={`${index}-${turn.question}`}>
                  <div className="chat-question">
                    <p>{turn.question}</p>
                  </div>
                  {turn.segments.map((segment, segmentIndex) => (
                    <SegmentView
                      key={`${index}-${segmentIndex}`}
                      segment={segment}
                    />
                  ))}
                </div>
              ))}
              {busy && (
                <p className="inline-status" role="status">
                  <span className="spinner" aria-hidden="true" />
                  Looking through your course material…
                </p>
              )}
              {error && <p className="status-error" role="alert">{error}</p>}
            </div>
            {refused && !allowOutside && (
              <div className="chat-composer">
                <p className="muted">
                  I couldn’t find this in your course material. You can ask for a general
                  answer instead.
                </p>
                <button
                  className="button-secondary"
                  onClick={() => {
                    setAllowOutside(true);
                    void send(true, lastTurn?.question);
                  }}
                  disabled={busy}
                >
                  Show general-knowledge answer
                </button>
              </div>
            )}
            <form
              className="chat-composer"
              onSubmit={(event) => {
                event.preventDefault();
                setAllowOutside(false);
                void send(false);
              }}
            >
              <label className="field-label" htmlFor="chat-question">
                Ask about your material
                <input
                  className="text-input"
                  id="chat-question"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="What would you like to understand?"
                  disabled={busy}
                />
              </label>
              <button
                className="button-primary"
                type="submit"
                disabled={busy || !input.trim()}
              >
                {busy ? "Thinking…" : "Send"}
              </button>
            </form>
          </section>
          <aside className="chat-note">
            <p className="eyebrow">Source first</p>
            <h2>Grounded in your course</h2>
            <p className="muted">
              Follow citations to check an explanation against the original material.
            </p>
            <ul className="disclaimer-list">
              <li>{disclaimers.generated}</li>
              <li>{disclaimers.outside}</li>
            </ul>
          </aside>
        </div>
      </main>
    </SiteShell>
  );
}

function SegmentView({ segment }: { segment: ChatSegment }) {
  const label =
    segment.label === "source_backed"
      ? "From your material"
      : segment.label === "outside_knowledge"
        ? "Outside your material"
        : "Not found in your material";
  const cls =
    segment.label === "source_backed"
      ? "seg-backed"
      : segment.label === "outside_knowledge"
        ? "seg-outside"
        : "seg-uncovered";

  return (
    <article className={`chat-answer ${cls}`}>
      <span className="segment-label">{label}</span>
      <p>
        {segment.text}
        {segment.check_source && <em> Check the source.</em>}
      </p>
      {segment.citations.length > 0 && (
        <div className="citation-list" aria-label="Cited sources">
          {segment.citations.map((citation) => (
            <Link
              className="citation-link"
              key={citation.unit_id}
              href={citation.link}
            >
              {citation.display}
            </Link>
          ))}
        </div>
      )}
      {segment.related_topics && segment.related_topics.length > 0 && (
        <p className="muted">Related: {segment.related_topics.join(", ")}</p>
      )}
    </article>
  );
}
