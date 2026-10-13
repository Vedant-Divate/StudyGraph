"use client";

import cytoscape from "cytoscape";
import { use, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

interface Graph {
  concepts: {
    id: string;
    level: string;
    name: string;
    summary: string;
    parent_id: string | null;
    importance: number;
  }[];
  edges: { prerequisite_id: string; concept_id: string; weight: number }[];
}

export default function MapPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const divRef = useRef<HTMLDivElement>(null);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api<Graph>(`/api/courses/${id}/graph`)
      .then(setGraph)
      .catch(() => setGraph(null));
  }, [id]);

  useEffect(() => {
    if (!graph || !divRef.current) return;
    const cy = cytoscape({
      container: divRef.current,
      elements: [
        ...graph.concepts.map((c) => ({ data: { id: c.id, label: c.name } })),
        ...graph.edges.map((e) => ({
          data: { source: e.prerequisite_id, target: e.concept_id },
        })),
      ],
      style: [
        { selector: "node", style: { label: "data(label)", "font-size": 10 } },
        { selector: "edge", style: { "curve-style": "bezier", "target-arrow-shape": "triangle" } },
      ],
      layout: { name: "cose" },
    });
    cy.on("tap", "node", (evt) => setSelected(evt.target.id() as string));
    return () => {
      cy.destroy();
    };
  }, [graph]);

  const detail = graph?.concepts.find((c) => c.id === selected) ?? null;

  return (
    <main>
      <h1>Knowledge map</h1>
      <div ref={divRef} style={{ width: "100%", height: 480, border: "1px solid #ccc" }} />
      {detail && (
        <section aria-live="polite">
          <h2>{detail.name}</h2>
          <p>{detail.summary}</p>
          <p>
            Level: {detail.level} · Importance: {detail.importance.toFixed(2)}
          </p>
        </section>
      )}
    </main>
  );
}
