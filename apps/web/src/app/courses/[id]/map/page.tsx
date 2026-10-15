"use client";

import cytoscape, { type Core } from "cytoscape";
import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";
import { SiteShell } from "@/components/site-shell";
import { api } from "@/lib/api";

interface Graph {
  concepts: {
    id: string;
    level: string;
    name: string;
    summary: string;
    parent_id: string | null;
    importance: number;
    m_eff?: number;
    band?: string;
    color?: string;
    icon?: string;
  }[];
  edges: { prerequisite_id: string; concept_id: string; weight: number }[];
}

const BAND_STYLE: Record<
  string,
  { color: string; icon: string; label: string }
> = {
  weak: { color: "#f1d8cf", icon: "!", label: "Needs review" },
  developing: { color: "#f2e6c3", icon: "◐", label: "In progress" },
  strong: { color: "#d9e9dd", icon: "✓", label: "Strong" },
};

export default function MapPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ student?: string; trace?: string }>;
}) {
  const { id } = use(params);
  const query = use(searchParams);
  const divRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const traceKey = (query.trace ?? "").split(",").filter(Boolean).join(",");

  useEffect(() => {
    let active = true;
    const url =
      `/api/courses/${id}/graph` +
      (query.student ? `?student_id=${query.student}` : "");
    setLoading(true);
    setError("");
    api<Graph>(url)
      .then((result) => {
        if (active) setGraph(result);
      })
      .catch(() => {
        if (active) setError("We couldn’t load the knowledge map.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id, query.student]);

  useEffect(() => {
    if (!graph || graph.concepts.length === 0 || !divRef.current) return;
    const cy = cytoscape({
      container: divRef.current,
      elements: [
        ...graph.concepts.map((concept) => {
          const band = BAND_STYLE[concept.band ?? ""];
          const icon = concept.icon ?? band?.icon ?? "•";
          return {
            data: {
              id: concept.id,
              label: `${icon} ${concept.name}`,
              color: band?.color ?? "#e9e9df",
            },
          };
        }),
        ...graph.edges.map((edge) => ({
          data: { source: edge.prerequisite_id, target: edge.concept_id },
        })),
      ],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "background-color": "data(color)",
            color: "#172b27",
            "font-size": 11,
            "font-weight": "bold",
            "text-wrap": "wrap",
            "text-max-width": "120px",
            "text-valign": "center",
            "text-halign": "center",
            width: 150,
            height: 56,
            shape: "round-rectangle",
            "border-width": 1,
            "border-color": "#9cae9f",
          },
        },
        {
          selector: "node:selected",
          style: { "border-width": 3, "border-color": "#185b49" },
        },
        {
          selector: "edge",
          style: {
            "curve-style": "bezier",
            "line-color": "#aab7ac",
            "target-arrow-color": "#748a7b",
            "target-arrow-shape": "triangle",
            width: 1.5,
          },
        },
      ],
      layout: { name: "cose", animate: false, padding: 35 },
      minZoom: 0.25,
      maxZoom: 2,
    });
    cyRef.current = cy;
    cy.on("tap", "node", (event) => setSelected(event.target.id()));
    traceKey.split(",").filter(Boolean).forEach((traceId) => {
      const node = cy.getElementById(traceId);
      if (node.nonempty()) node.style({ "border-width": 4, "border-color": "#a33f2d" });
    });
    return () => {
      cyRef.current = null;
      cy.destroy();
    };
  }, [graph, traceKey]);

  const detail = graph?.concepts.find((concept) => concept.id === selected) ?? null;

  function selectConcept(conceptId: string) {
    setSelected(conceptId);
    const node = cyRef.current?.getElementById(conceptId);
    if (node?.nonempty()) {
      cyRef.current?.elements().unselect();
      node.select();
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        cyRef.current?.fit(node, 50);
      } else {
        cyRef.current?.animate({ fit: { eles: node, padding: 50 }, duration: 220 });
      }
    }
  }

  return (
    <SiteShell active="library">
      <main>
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/courses">Library</Link>
          <span aria-hidden="true">/</span>
          <Link href={`/courses/${id}`}>Course</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Knowledge map</span>
        </nav>
        <header className="page-heading">
          <p className="eyebrow">See the connections</p>
          <h1>Knowledge map</h1>
          <p className="lede">
            Explore the ideas in this course and how each one builds on the others.
          </p>
        </header>
        {loading && (
          <p className="status-row" role="status">
            <span className="spinner" aria-hidden="true" />
            Drawing connections between your course concepts…
          </p>
        )}
        {error && <p className="status-error" role="alert">{error}</p>}
        {!loading && !error && graph?.concepts.length === 0 && (
          <p className="status-row">
            This course doesn’t have any mapped concepts yet.
          </p>
        )}
        {!loading && !error && graph && graph.concepts.length > 0 && (
          <>
            <div className="map-legend" aria-label="Mastery key">
              <span className="mastery-label" data-band="weak">
                ! Needs review
              </span>
              <span className="mastery-label" data-band="developing">
                ◐ In progress
              </span>
              <span className="mastery-label" data-band="strong">
                ✓ Strong
              </span>
              <span className="mastery-label">• Not assessed</span>
            </div>
            <div className="map-layout">
              <section className="panel" aria-label="Interactive concept map">
                <div
                  className="map-canvas"
                  ref={divRef}
                  role="img"
                  aria-label="Interactive map of concepts and prerequisite relationships"
                />
                {traceKey.length > 0 && (
                  <p className="inline-status" role="status">
                    <span className="mastery-label" data-band="weak">!</span>
                    The outlined concepts mark the learning trace from your quiz.
                  </p>
                )}
              </section>
              <aside className="panel map-concepts">
                <div className="panel-heading">
                  <h2>Course concepts</h2>
                  <span className="count-label">{graph.concepts.length}</span>
                </div>
                {detail && (
                  <section className="map-selection" aria-live="polite">
                    <p className="eyebrow">Selected concept</p>
                    <h3>
                      {detail.icon} {detail.name}
                    </h3>
                    <p>{detail.summary}</p>
                    <p className="muted">
                      Level: {detail.level} · Importance: {detail.importance.toFixed(2)}
                      {detail.m_eff !== undefined &&
                        ` · Mastery: ${(detail.m_eff * 100).toFixed(0)}% (${detail.band})`}
                    </p>
                  </section>
                )}
                <ul className="plain-list">
                  {graph.concepts.map((concept) => {
                    const band = BAND_STYLE[concept.band ?? ""];
                    const icon = concept.icon ?? band?.icon ?? "•";
                    const label = band?.label ?? "Not assessed";
                    return (
                      <li key={concept.id}>
                        <button
                          className="concept-button"
                          type="button"
                          aria-pressed={selected === concept.id}
                          onClick={() => selectConcept(concept.id)}
                        >
                          <span aria-hidden="true">{icon} </span>
                          {concept.name}
                          <span className="mastery-label" data-band={concept.band}>
                            {label}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </aside>
            </div>
          </>
        )}
      </main>
    </SiteShell>
  );
}
