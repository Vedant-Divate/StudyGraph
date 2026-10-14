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
    m_eff?: number;
    band?: string;
    color?: string;
    icon?: string;
  }[];
  edges: { prerequisite_id: string; concept_id: string; weight: number }[];
}

const BAND_COLOR: Record<string, string> = {
  weak: "#d73027",
  developing: "#fdae61",
  strong: "#1a9850",
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
  const [graph, setGraph] = useState<Graph | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const traceIds = (query.trace ?? "").split(",").filter(Boolean);

  useEffect(() => {
    const url =
      `/api/courses/${id}/graph` + (query.student ? `?student_id=${query.student}` : "");
    api<Graph>(url)
      .then(setGraph)
      .catch(() => setGraph(null));
  }, [id, query.student]);

  useEffect(() => {
    if (!graph || !divRef.current) return;
    const cy = cytoscape({
      container: divRef.current,
      elements: [
        ...graph.concepts.map((c) => ({
          data: { id: c.id, label: `${c.icon ?? ""} ${c.name}`.trim(), band: c.band ?? "" },
        })),
        ...graph.edges.map((e) => ({
          data: { source: e.prerequisite_id, target: e.concept_id },
        })),
      ],
      style: [
        { selector: "node", style: { label: "data(label)", "font-size": 10 } },
        { selector: "node[band = 'weak']", style: { "background-color": BAND_COLOR.weak } },
        {
          selector: "node[band = 'developing']",
          style: { "background-color": BAND_COLOR.developing },
        },
        { selector: "node[band = 'strong']", style: { "background-color": BAND_COLOR.strong } },
        { selector: "edge", style: { "curve-style": "bezier", "target-arrow-shape": "triangle" } },
      ],
      layout: { name: "cose" },
    });
    cy.on("tap", "node", (evt) => setSelected(evt.target.id() as string));
    traceIds.forEach((tid) => {
      const node = cy.getElementById(tid);
      if (node.nonempty()) node.style("border-width", 3);
    });
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
          <h2>
            {detail.icon} {detail.name}
          </h2>
          <p>{detail.summary}</p>
          <p>
            Level: {detail.level} · Importance: {detail.importance.toFixed(2)}
            {detail.m_eff !== undefined &&
              ` · Mastery: ${(detail.m_eff * 100).toFixed(0)}% (${detail.band})`}
          </p>
        </section>
      )}
    </main>
  );
}
