"""Snapshot the verified question bank + concept graph for LLM-free simulation.

Reads Neon (SELECT-only; never prints secrets) and writes
eval/simulation/bank_snapshot.json: concept/edge/question metadata only (no
stems), course order from lecture-flow unit timestamps, and held-out concepts
by fixed rule (4 lowest-importance question-bearing concepts).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "api"))


def load_dotlocal_env() -> None:
    dotlocal = REPO / ".env.local"
    if dotlocal.is_file():
        for line in dotlocal.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key in ("DATABASE_URL", "NIM_API_KEY") and key not in os.environ:
                    os.environ[key] = value


def main() -> None:
    load_dotlocal_env()
    from sqlalchemy import select

    from app.db import models
    from app.db.session import make_session_factory

    ns = uuid.UUID("a4301776-1a6a-49ec-b265-27717d3c7634")
    course_id = uuid.uuid5(ns, "mit-ocw-6.041sc-fall-2013")
    session = make_session_factory()()
    try:
        concepts = session.scalars(
            select(models.Concept).where(models.Concept.course_id == course_id)
        ).all()
        edges = session.scalars(
            select(models.ConceptEdge).where(models.ConceptEdge.course_id == course_id)
        ).all()
        questions = session.scalars(
            select(models.Question).where(models.Question.course_id == course_id)
        ).all()
        unit_concepts = session.scalars(select(models.UnitConcept)).all()
        # Materialize everything to plain data before the session closes.
        concept_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "level": c.level,
                "importance": c.importance,
                "parent_id": str(c.parent_id) if c.parent_id else None,
            }
            for c in concepts
        ]
        edge_data = [
            [str(e.prerequisite_id), str(e.concept_id), e.weight] for e in edges
        ]
        question_data = []
        for q in questions:
            assert (q.verification_json or {}).get("ok") is True, f"unverified {q.id}"
            question_data.append(
                {
                    "id": str(q.id),
                    "concept_id": str(q.concept_id) if q.concept_id else None,
                    "difficulty": str(q.difficulty).lower(),
                    "type": q.type,
                    "num_options": len((q.options_json or {}).get("options", []) or [1, 2, 3, 4]),
                }
            )
        unit_times: dict[str, list[float]] = {}
        for link in unit_concepts:
            unit = session.get(models.ContentUnit, link.unit_id)
            if unit is not None and unit.t_start_s is not None:
                unit_times.setdefault(str(link.concept_id), []).append(float(unit.t_start_s))
    finally:
        session.rollback()
        session.close()

    by_id = {c["id"]: c for c in concept_data}
    mean_time = {
        cid: (sum(times) / len(times) if times else float("inf"))
        for cid, times in unit_times.items()
    }
    ordered = sorted(by_id, key=lambda cid: (mean_time.get(cid, float("inf")), by_id[cid]["name"]))
    course_order = {cid: rank for rank, cid in enumerate(ordered)}

    def topic_of(cid: str) -> str:
        seen = set()
        while cid in by_id and by_id[cid]["parent_id"] is not None and cid not in seen:
            seen.add(cid)
            cid = str(by_id[cid]["parent_id"])
        return cid

    concept_rows = [
        {
            "id": cid,
            "name": by_id[cid]["name"],
            "level": by_id[cid]["level"],
            "importance": by_id[cid]["importance"],
            "parent_id": by_id[cid]["parent_id"],
            "topic_id": topic_of(cid),
            "course_order": course_order[cid],
        }
        for cid in by_id
    ]
    edge_rows = edge_data
    question_rows = question_data
    with_questions = {q["concept_id"] for q in question_rows if q["concept_id"]}
    bearers = sorted(
        [c for c in concept_rows if c["id"] in with_questions],
        key=lambda c: (c["importance"], c["id"]),
    )
    held_out = [c["id"] for c in bearers[:4]]
    snapshot = {
        "course_id": str(course_id),
        "snapshot_utc": datetime.now(UTC).isoformat(),
        "held_out_rule": "4 lowest-importance question-bearing concepts (fixed, untuned)",
        "held_out": held_out,
        "normalizations": ["difficulty lower-cased ('Easy' -> 'easy')"],
        "concepts": concept_rows,
        "edges": edge_rows,
        "questions": question_rows,
    }
    out = REPO / "eval" / "simulation" / "bank_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"concepts={len(concept_rows)} edges={len(edge_rows)} "
          f"questions={len(question_rows)} held_out={len(held_out)} -> {out}")


if __name__ == "__main__":
    main()
