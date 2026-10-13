"""Grounded answer generation per PROJECT.md 8.4 + ONE batched verifier call."""

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import models
from app.domain import citation
from app.kb import retrieval as kb_retrieval
from app.llm.provider import StructuredResult

logger = logging.getLogger(__name__)

ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "label": {"type": "string"},
                    "unit_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "label", "unit_ids"],
            },
        }
    },
    "required": ["segments"],
}

VERIFY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment": {"type": "integer"},
                    "supported": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["segment", "supported"],
            },
        }
    },
    "required": ["checks"],
}


def _unit_context(units: list[dict[str, Any]]) -> str:
    parts = []
    for unit in units:
        body = unit["text"]
        if unit.get("figure_description"):
            body += "\n[figure] " + unit["figure_description"]
        parts.append(f"[{unit['unit_id']}] ({unit['kind']}) {body[:1200]}")
    return "\n\n".join(parts)


def generate_answer(
    session: Session,
    *,
    course_id: uuid.UUID,
    question: str,
    allow_outside: bool,
    settings: Settings | None = None,
    llm: Any = None,
    min_confidence: float | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    if llm is None:
        from app.llm.factory import get_llm

        llm = get_llm(settings)
    threshold = min_confidence if min_confidence is not None else 0.05
    units, confidence = kb_retrieval.retrieve(
        session, course_id=course_id, query=question, settings=settings
    )
    retrieved_ids = {str(u["unit_id"]) for u in units}
    if not units or confidence < threshold:
        return _not_covered(session, course_id, allow_outside, llm, settings, question)

    prompt = (
        "Answer the student's question using ONLY the course units below. Output "
        "segments with label source_backed (citing [unit_id]s you were given), "
        "outside_knowledge (no citations), or not_covered. NEVER write page, slide "
        "or timestamp numbers — cite unit_ids only.\n\nQuestion: "
        f"{question}\n\nUnits:\n{_unit_context(units)}"
    )
    result: StructuredResult = llm.complete_structured(
        prompt=prompt, schema=ANSWER_SCHEMA, model=settings.llm_model
    )
    segments = _enforce_ids(result.data.get("segments", []), retrieved_ids)
    verdicts = _verify_batch(segments, units, llm=llm, settings=settings)
    final = _apply_verdicts(segments, verdicts)
    if not any(s["label"] == "source_backed" for s in final):
        return _not_covered(session, course_id, allow_outside, llm, settings, question)
    return {
        "segments": _resolve(session, final),
        "confidence": confidence,
        "verifier": verdicts,
    }


def _enforce_ids(segments: list[dict[str, Any]], retrieved_ids: set[str]) -> list[dict[str, Any]]:
    """Hallucinated unit_ids are rejected: segment becomes outside_knowledge."""
    clean: list[dict[str, Any]] = []
    for seg in segments:
        if not isinstance(seg, dict) or not seg.get("text"):
            continue
        label = seg.get("label", "outside_knowledge")
        ids = [str(i) for i in (seg.get("unit_ids") or []) if str(i) in retrieved_ids]
        if label == "source_backed" and not ids:
            label = "outside_knowledge"
        clean.append({"text": str(seg["text"]), "label": label, "unit_ids": ids})
    return clean


def _verify_batch(
    segments: list[dict[str, Any]],
    units: list[dict[str, Any]],
    *,
    llm: Any,
    settings: Settings,
) -> list[dict[str, Any]]:
    backed = [(i, s) for i, s in enumerate(segments) if s["label"] == "source_backed"]
    if not backed:
        return []
    by_id = {str(u["unit_id"]): u for u in units}
    lines = []
    for i, seg in backed:
        cited = "\n".join(
            f"({uid}) {(by_id.get(uid, {}).get('text', ''))[:800]}" for uid in seg["unit_ids"]
        )
        lines.append(f"SEGMENT {i}: {seg['text'][:600]}\nCITED:\n{cited}")
    prompt = (
        "For each SEGMENT, judge whether its CITED units support it: supported, "
        "partial or no, with a short reason. One batched call.\n\n" + "\n\n".join(lines)
    )
    try:
        result: StructuredResult = llm.complete_structured(
            prompt=prompt, schema=VERIFY_SCHEMA, model=settings.verifier_model
        )
        checks = result.data.get("checks", [])
    except Exception as exc:  # noqa: BLE001 - fail open to 'partial'
        logger.warning("verifier failed: %s", type(exc).__name__)
        return [
            {"segment": i, "supported": "partial", "reason": "verifier error"} for i, _ in backed
        ]
    verdicts = []
    for item in checks:
        if isinstance(item, dict) and item.get("segment") in [i for i, _ in backed]:
            verdicts.append(
                {
                    "segment": item["segment"],
                    "supported": item.get("supported", "partial"),
                    "reason": str(item.get("reason", ""))[:300],
                }
            )
    return verdicts


def _apply_verdicts(
    segments: list[dict[str, Any]], verdicts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_segment = {v["segment"]: v for v in verdicts}
    out = []
    for i, seg in enumerate(segments):
        if seg["label"] != "source_backed" or i not in by_segment:
            out.append(seg)
            continue
        verdict = by_segment[i]["supported"]
        if verdict == "no":
            out.append({**seg, "label": "outside_knowledge", "unit_ids": []})
        elif verdict == "partial":
            out.append({**seg, "check_source": True})
        else:
            out.append(seg)
    return out


def _resolve(session: Session, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    resolved = []
    for seg in segments:
        citations = []
        for uid in seg.get("unit_ids", []):
            try:
                unit = session.get(models.ContentUnit, uuid.UUID(uid))
            except ValueError:
                continue
            if unit is None:
                continue
            source = session.get(models.Source, unit.source_id)
            title = source.filename if source else "source"
            if unit.page is not None:
                loc = citation.display_string(_loc(unit.source_id, page=unit.page), title)
                link = citation.deep_link(_loc(unit.source_id, page=unit.page))
            elif unit.slide is not None:
                loc = citation.display_string(_loc(unit.source_id, slide=unit.slide), title)
                link = citation.deep_link(_loc(unit.source_id, slide=unit.slide))
            else:
                assert unit.t_start_s is not None and unit.t_end_s is not None
                loc = citation.display_string(
                    _loc(unit.source_id, t_start_s=unit.t_start_s, t_end_s=unit.t_end_s),
                    title,
                )
                link = citation.deep_link(
                    _loc(unit.source_id, t_start_s=unit.t_start_s, t_end_s=unit.t_end_s)
                )
            citations.append({"unit_id": uid, "display": loc, "link": link})
        resolved.append({**seg, "citations": citations})
    return resolved


def _loc(source_id: uuid.UUID, **kwargs: Any) -> Any:
    from app.domain.types import Location

    return Location(source_id=source_id, **kwargs)


def _not_covered(
    session: Session,
    course_id: uuid.UUID,
    allow_outside: bool,
    llm: Any,
    settings: Settings,
    question: str,
) -> dict[str, Any]:
    if allow_outside:
        prompt = (
            "The course material does not cover this. Answer from general knowledge, "
            f"one segment labelled outside_knowledge, no citations.\n\nQuestion: {question}"
        )
        result: StructuredResult = llm.complete_structured(
            prompt=prompt, schema=ANSWER_SCHEMA, model=settings.llm_model
        )
        segments = _enforce_ids(result.data.get("segments", []), set())
        return {"segments": _resolve(session, segments), "confidence": 0.0, "verifier": []}
    topics = _related_topics(session, course_id)
    return {
        "segments": [
            {
                "text": "This isn't covered in your uploaded material.",
                "label": "not_covered",
                "unit_ids": [],
                "citations": [],
                "related_topics": topics,
            }
        ],
        "confidence": 0.0,
        "verifier": [],
    }


def _related_topics(session: Session, course_id: uuid.UUID) -> list[str]:
    rows = (
        session.query(models.Concept.name)
        .filter(models.Concept.course_id == course_id, models.Concept.level == "topic")
        .limit(5)
        .all()
    )
    return [row[0] for row in rows]
