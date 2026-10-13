"""Concept candidate extraction + merge (one structured call per source, sprint)."""

import logging
import uuid
from typing import Any

from app.llm.provider import StructuredResult

logger = logging.getLogger(__name__)

EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "level": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["name", "level", "summary"],
            },
        }
    },
    "required": ["concepts"],
}

MERGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "level": {"type": "string"},
                    "parent": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["name", "level", "summary"],
            },
        }
    },
    "required": ["concepts"],
}


def extract_candidates(
    source_label: str,
    unit_texts: list[str],
    *,
    complete: Any,
    model: str,
    max_chars_per_unit: int = 220,
    max_units: int = 60,
) -> list[dict[str, str]]:
    digest = "\n".join(
        f"- {t[:max_chars_per_unit].replace(chr(10), ' ')}" for t in unit_texts[:max_units]
    )
    prompt = (
        f"List the taught topics, subtopics and key concepts in {source_label} "
        "(probability course material). level is one of topic|subtopic|concept. "
        f"Return 8-15 items.\n\nContent:\n{digest}"
    )
    result: StructuredResult = complete(prompt=prompt, schema=EXTRACT_SCHEMA, model=model)
    concepts = result.data.get("concepts", [])
    return [c for c in concepts if isinstance(c, dict) and c.get("name")]


def merge_candidates(
    per_source: list[list[dict[str, str]]], *, complete: Any, model: str
) -> list[dict[str, str]]:
    flat: list[str] = []
    for i, candidates in enumerate(per_source):
        for cand in candidates:
            flat.append(
                f"[S{i}] {cand.get('name', '')} ({cand.get('level', '')}): "
                f"{cand.get('summary', '')[:200]}"
            )
    prompt = (
        "Merge these candidate concepts from multiple sources of one probability "
        "course into ONE canonical list of 15-25 concepts with depth <= 3 "
        "(topic > subtopic > concept). Use 'parent' with the parent NAME for "
        "subtopics/concepts, omit it for topics.\n\nCandidates:\n" + "\n".join(flat)
    )
    result: StructuredResult = complete(prompt=prompt, schema=MERGE_SCHEMA, model=model)
    concepts = result.data.get("concepts", [])
    return [c for c in concepts if isinstance(c, dict) and c.get("name")]


def assign_ids(merged: list[dict[str, str]], course_id: uuid.UUID) -> list[dict[str, Any]]:
    """Attach UUIDs and resolve parent names to ids (topics first)."""
    by_name: dict[str, uuid.UUID] = {}
    out: list[dict[str, Any]] = []
    for cand in merged:
        cid = uuid.uuid4()
        by_name[cand["name"].strip().lower()] = cid
    for cand in merged:
        parent_name = (cand.get("parent") or "").strip().lower()
        out.append(
            {
                "id": by_name[cand["name"].strip().lower()],
                "course_id": course_id,
                "level": cand.get("level", "concept"),
                "name": cand["name"].strip(),
                "summary": cand.get("summary", "")[:1000],
                "parent_id": by_name.get(parent_name) if parent_name else None,
            }
        )
    return out
