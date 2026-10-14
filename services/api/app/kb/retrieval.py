"""Hybrid retrieval: vector cosine + Postgres full-text, fused with RRF."""

import math
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import models
from app.kb.embeddings import embed_texts


def cosine(a: list[float], b: list[float]) -> float:
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / denom


def vector_ranked(
    session: Session, *, course_id: UUID, query_vector: list[float], limit: int = 20
) -> list[tuple[UUID, float]]:
    rows = session.execute(
        select(models.ContentUnit.id, models.ContentUnit.embedding)
        .join(models.Source, models.Source.id == models.ContentUnit.source_id)
        .where(models.Source.course_id == course_id)
    ).all()
    scored = [
        (row[0], cosine(query_vector, list(row[1])))
        for row in rows
        if row[1] is not None and len(list(row[1])) == len(query_vector)
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]


def keyword_ranked(
    session: Session, *, course_id: UUID, query: str, limit: int = 20
) -> list[tuple[UUID, float]]:
    rows = session.execute(
        select(
            models.ContentUnit.id,
            func.ts_rank(
                func.to_tsvector("english", models.ContentUnit.text),
                func.websearch_to_tsquery("english", query),
            ).label("rank"),
        )
        .join(models.Source, models.Source.id == models.ContentUnit.source_id)
        .where(models.Source.course_id == course_id)
        .where(
            func.to_tsvector("english", models.ContentUnit.text).op("@@")(
                func.websearch_to_tsquery("english", query)
            )
        )
        .order_by(sql_text("rank DESC"))
        .limit(limit)
    ).all()
    return [(row[0], float(row[1])) for row in rows]


def reciprocal_rank_fusion(
    rankings: list[list[tuple[UUID, float]]], *, k: int = 60
) -> list[tuple[UUID, float]]:
    fused: dict[UUID, float] = {}
    for ranking in rankings:
        for rank, (uid, _score) in enumerate(ranking, start=1):
            fused[uid] = fused.get(uid, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda pair: pair[1], reverse=True)


def expand_neighbours(
    session: Session, units: list[dict[str, Any]], *, per_unit: int = 1
) -> list[dict[str, Any]]:
    """Append up to `per_unit` adjacent units (same source, nearest page/time)."""
    seen = {u["unit_id"] for u in units}
    extra: list[dict[str, Any]] = []
    for unit in units:
        row = session.get(models.ContentUnit, unit["unit_id"])
        if row is None:
            continue
        if row.page is not None:
            neighbor = session.scalars(
                select(models.ContentUnit)
                .where(
                    models.ContentUnit.source_id == row.source_id,
                    models.ContentUnit.page == row.page + 1,
                    models.ContentUnit.id.not_in(seen),
                )
                .limit(1)
            ).first()
        elif row.t_start_s is not None:
            neighbor = session.scalars(
                select(models.ContentUnit)
                .where(
                    models.ContentUnit.source_id == row.source_id,
                    models.ContentUnit.t_start_s > row.t_start_s,
                    models.ContentUnit.id.not_in(seen),
                )
                .order_by(models.ContentUnit.t_start_s)
                .limit(1)
            ).first()
        else:
            neighbor = None
        if neighbor is not None:
            seen.add(neighbor.id)
            extra.append(
                {
                    "unit_id": neighbor.id,
                    "kind": neighbor.kind,
                    "text": neighbor.text,
                    "figure_description": neighbor.figure_description,
                    "source_id": neighbor.source_id,
                    "score": unit["score"] * 0.5,
                }
            )
            if len(extra) >= per_unit * len(units):
                break
    return units + extra


def retrieve(
    session: Session,
    *,
    course_id: UUID,
    query: str,
    settings: Settings | None = None,
) -> tuple[list[dict[str, Any]], float, float]:
    """Return units, the top raw cosine confidence, and the mean top-three cosine."""
    settings = settings or get_settings()
    query_vector = embed_texts([query], settings=settings, input_type="query")[0]
    vec = vector_ranked(session, course_id=course_id, query_vector=query_vector)
    key = keyword_ranked(session, course_id=course_id, query=query)
    fused = reciprocal_rank_fusion([vec, key])
    top = fused[: min(settings.retrieval_top_k, 6)]
    if not top or not vec:
        return [], -1.0, -1.0
    confidence = vec[0][1]
    mean_top_three = sum(score for _uid, score in vec[:3]) / min(len(vec), 3)
    by_id = {uid: score for uid, score in top}
    units = session.scalars(
        select(models.ContentUnit).where(models.ContentUnit.id.in_(list(by_id)))
    ).all()
    unit_map = {u.id: u for u in units}
    ordered = [
        {
            "unit_id": uid,
            "kind": unit_map[uid].kind,
            "text": unit_map[uid].text,
            "figure_description": unit_map[uid].figure_description,
            "source_id": unit_map[uid].source_id,
            "score": score,
        }
        for uid, score in top
        if uid in unit_map
    ]
    expanded = expand_neighbours(session, ordered)
    return expanded[:6], confidence, mean_top_three
