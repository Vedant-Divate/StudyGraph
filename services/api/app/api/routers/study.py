"""Chat, graph, unit and source-file routes (Phase 3-5 slice)."""

import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.db import models
from app.domain import citation
from app.tutor import answer as tutor

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    allow_outside: bool = False


@router.post("/api/courses/{course_id}/chat")
def chat(
    course_id: uuid.UUID, body: ChatRequest, session: Session = Depends(get_session)
) -> dict[str, Any]:
    from app.db.repositories import library

    if library.get_course(session, course_id) is None:
        raise HTTPException(status_code=404, detail="course not found")
    return tutor.generate_answer(
        session,
        course_id=course_id,
        question=body.message,
        allow_outside=body.allow_outside,
    )


@router.get("/api/courses/{course_id}/graph")
def get_graph(
    course_id: uuid.UUID,
    student_id: uuid.UUID | None = None,  # noqa: ARG001 - mastery colors land in Phase 7
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    concepts = session.scalars(
        select(models.Concept).where(models.Concept.course_id == course_id)
    ).all()
    edges = session.scalars(
        select(models.ConceptEdge).where(models.ConceptEdge.course_id == course_id)
    ).all()
    return {
        "concepts": [
            {
                "id": str(c.id),
                "level": c.level,
                "name": c.name,
                "summary": c.summary,
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "importance": c.importance,
            }
            for c in concepts
        ],
        "edges": [
            {
                "prerequisite_id": str(e.prerequisite_id),
                "concept_id": str(e.concept_id),
                "weight": e.weight,
            }
            for e in edges
        ],
    }


@router.get("/api/units/{unit_id}")
def get_unit(unit_id: uuid.UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    unit = session.get(models.ContentUnit, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="unit not found")
    source = session.get(models.Source, unit.source_id)
    title = source.filename if source else "source"
    from app.domain.types import Location

    if unit.page is not None:
        loc = Location(source_id=unit.source_id, page=unit.page)
    elif unit.slide is not None:
        loc = Location(source_id=unit.source_id, slide=unit.slide)
    else:
        loc = Location(source_id=unit.source_id, t_start_s=unit.t_start_s, t_end_s=unit.t_end_s)
    return {
        "id": str(unit.id),
        "kind": unit.kind,
        "text": unit.text,
        "figure_description": unit.figure_description,
        "display": citation.display_string(loc, title),
        "link": citation.deep_link(loc),
    }


@router.get("/api/sources/{source_id}/file")
def get_source_file(source_id: uuid.UUID, session: Session = Depends(get_session)) -> FileResponse:
    from app.db.repositories import library

    source = library.get_source(session, source_id)
    if source is None or not os.path.exists(source.path):
        raise HTTPException(status_code=404, detail="source file not found")
    media = "video/mp4" if source.path.endswith(".mp4") else "application/pdf"
    return FileResponse(source.path, media_type=media, filename=source.filename)


@router.get("/api/sources/{source_id}/page/{n}")
def get_source_page(
    source_id: uuid.UUID, n: int, session: Session = Depends(get_session)
) -> Response:
    import pymupdf  # local import: render on demand

    from app.db.repositories import library

    source = library.get_source(session, source_id)
    if source is None or not source.path.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="pdf source not found")
    doc: Any = pymupdf.open(source.path)  # type: ignore[no-untyped-call]
    if n < 1 or n > len(doc):
        raise HTTPException(status_code=404, detail="page out of range")
    pix: Any = doc[n - 1].get_pixmap(dpi=110)
    return Response(content=pix.tobytes("png"), media_type="image/png")
