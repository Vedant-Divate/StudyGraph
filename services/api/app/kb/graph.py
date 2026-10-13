"""Prerequisite edges with evidence, cycle removal, unit tagging, misconceptions."""

import logging
import math
from typing import Any

from app.llm.provider import StructuredResult

logger = logging.getLogger(__name__)

EDGES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prerequisite": {"type": "string"},
                    "concept": {"type": "string"},
                    "weight": {"type": "number"},
                    "evidence": {"type": "string"},
                },
                "required": ["prerequisite", "concept", "weight"],
            },
        }
    },
    "required": ["edges"],
}

MISCONCEPTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "misconceptions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                    "contrasts_material": {"type": "boolean"},
                },
                "required": ["label", "description"],
            },
        }
    },
    "required": ["misconceptions"],
}


def propose_edges(
    concepts: list[dict[str, Any]],
    unit_index: dict[str, str],
    *,
    complete: Any,
    model: str,
) -> list[dict[str, Any]]:
    names = "\n".join(f"- {c['name']}: {c['summary'][:100]}" for c in concepts)
    sample_units = "\n".join(
        f"[{uid}] {text[:120].replace(chr(10), ' ')}" for uid, text in list(unit_index.items())[:40]
    )
    prompt = (
        "For this probability course, propose prerequisite edges A -> B (A must be "
        "learned before B). Use ONLY the concept names below. Give weight 0-1 and, "
        "where possible, the [unit id] whose text shows B relying on A.\n\nConcepts:\n"
        f"{names}\n\nUnits:\n{sample_units}"
    )
    result: StructuredResult = complete(prompt=prompt, schema=EDGES_SCHEMA, model=model)
    edges = result.data.get("edges", [])
    return [e for e in edges if isinstance(e, dict) and e.get("prerequisite") and e.get("concept")]


def resolve_edge_ids(
    edges: list[dict[str, Any]], concepts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_name = {c["name"].strip().lower(): c["id"] for c in concepts}
    resolved: list[dict[str, Any]] = []
    for edge in edges:
        pre = by_name.get(str(edge.get("prerequisite", "")).strip().lower())
        con = by_name.get(str(edge.get("concept", "")).strip().lower())
        if pre is None or con is None or pre == con:
            continue
        try:
            weight = max(0.0, min(1.0, float(edge.get("weight", 0.5))))
        except (TypeError, ValueError):
            weight = 0.5
        resolved.append({"prerequisite_id": pre, "concept_id": con, "weight": weight})
    return resolved


def remove_cycles(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop the weakest edge in every detected cycle (DFS). Order-stable."""

    def find_cycle(current: list[dict[str, Any]]) -> list[int] | None:
        adj: dict[Any, list[tuple[Any, int]]] = {}
        for i, edge in enumerate(current):
            adj.setdefault(edge["prerequisite_id"], []).append((edge["concept_id"], i))
        color: dict[Any, int] = {}
        stack: list[Any] = []
        stack_idx: dict[Any, int] = {}

        def visit(node: Any) -> list[int] | None:
            color[node] = 1
            stack.append(node)
            stack_idx[node] = len(stack) - 1
            for nxt, _ei in adj.get(node, []):
                if color.get(nxt, 0) == 0:
                    found = visit(nxt)
                    if found is not None:
                        return found
                elif color.get(nxt) == 1:
                    members = stack[stack_idx[nxt] :]
                    out = []
                    for a, b in zip(members, members[1:] + [nxt], strict=True):
                        for to, idx in adj.get(a, []):
                            if to == b:
                                out.append(idx)
                                break
                    return out
            stack.pop()
            stack_idx.pop(node, None)
            color[node] = 2
            return None

        for node in list(adj):
            if color.get(node, 0) == 0:
                found = visit(node)
                if found is not None:
                    return found
        return None

    current = list(edges)
    while True:
        cycle = find_cycle(current)
        if not cycle:
            return current
        weakest = min(cycle, key=lambda i: current[i]["weight"])
        current = [e for i, e in enumerate(current) if i != weakest]


def cosine(a: list[float], b: list[float]) -> float:
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / denom


def tag_units(
    unit_vectors: list[tuple[str, list[float]]],
    concept_vectors: list[tuple[Any, list[float]]],
    *,
    top_k: int = 3,
    min_score: float = 0.15,
) -> dict[str, list[tuple[Any, float]]]:
    """Top-k concept tags per unit by cosine similarity. Returns unit_id -> tags."""
    tags: dict[str, list[tuple[Any, float]]] = {}
    for unit_id, uvec in unit_vectors:
        scored = [
            (cid, cosine(uvec, cvec)) for cid, cvec in concept_vectors if len(cvec) == len(uvec)
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        tags[unit_id] = [(cid, score) for cid, score in scored[:top_k] if score >= min_score]
    return tags


def generate_misconceptions(
    concept_name: str, concept_summary: str, *, complete: Any, model: str
) -> list[dict[str, Any]]:
    prompt = (
        f"List 2-4 common student misconceptions about '{concept_name}' "
        f"({concept_summary[:300]}). For each, say whether course material typically "
        "contrasts/warns against it (contrasts_material true) or it is just a known "
        "trap (false)."
    )
    result: StructuredResult = complete(prompt=prompt, schema=MISCONCEPTIONS_SCHEMA, model=model)
    out: list[dict[str, Any]] = []
    for item in result.data.get("misconceptions", [])[:4]:
        if not isinstance(item, dict) or not item.get("label"):
            continue
        out.append(
            {
                "label": str(item["label"])[:300],
                "description": str(item.get("description", ""))[:1000],
                "origin": "source_anchored"
                if item.get("contrasts_material") is True
                else "llm_suggested",
            }
        )
    return out


def compute_importance(tag_counts: dict[Any, int]) -> dict[Any, float]:
    total = sum(tag_counts.values())
    if total <= 0:
        return dict.fromkeys(tag_counts, 0.0)
    return {cid: count / total for cid, count in tag_counts.items()}


def is_acyclic(edges: list[dict[str, Any]]) -> bool:
    return len(remove_cycles(list(edges))) == len(edges)
