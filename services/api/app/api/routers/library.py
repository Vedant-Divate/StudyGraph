"""Course / source / job routes (Phase 1-2 slice)."""

import hashlib
import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.config import get_settings
from app.db.repositories import library

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf": "pdf"}


class CourseCreate(BaseModel):
    title: str
    description: str = ""
    is_demo: bool = False


def _not_found(resource: str, ident: uuid.UUID) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"error": {"code": "not_found", "message": f"{resource} {ident} not found"}},
    )


def _public_course(course: Any) -> dict[str, Any]:
    return {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "is_demo": course.is_demo,
    }


@router.post("/api/courses")
def create_course(body: CourseCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    course = library.create_course(
        session, title=body.title, description=body.description, is_demo=body.is_demo
    )
    session.commit()
    return _public_course(course)


@router.get("/api/courses/{course_id}")
def get_course(course_id: uuid.UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    course = library.get_course(session, course_id)
    if course is None:
        raise _not_found("course", course_id)
    return _public_course(course)


def _public_source(source: Any) -> dict[str, Any]:
    return {
        "id": str(source.id),
        "course_id": str(source.course_id),
        "kind": source.kind,
        "filename": source.filename,
        "status": source.status,
        "page_count": source.page_count,
        "error": source.error,
        "quality": source.quality_json,
    }


@router.post("/api/courses/{course_id}/sources")
async def upload_source(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    license_note: str | None = Form(default=None),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    settings = get_settings()
    course = library.get_course(session, course_id)
    if course is None:
        raise _not_found("course", course_id)
    filename = os.path.basename(file.filename or "upload")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "unsupported_type",
                    "message": f"only {sorted(ALLOWED_EXTENSIONS)} uploads in Phase 1-2",
                }
            },
        )
    limit_bytes = settings.max_upload_mb * 1024 * 1024
    upload_dir = os.path.join(settings.data_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, f"{uuid.uuid4().hex}{ext}")
    digest = hashlib.sha256()
    size = 0
    with open(dest, "wb") as handle:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > limit_bytes:
                handle.close()
                os.remove(dest)
                raise HTTPException(
                    status_code=413,
                    detail={"error": {"code": "too_large", "message": "file exceeds size limit"}},
                )
            handle.write(chunk)
            digest.update(chunk)
    source = library.create_source(
        session,
        course_id=course.id,
        kind=ALLOWED_EXTENSIONS[ext],
        filename=filename,
        path=dest,
        sha256=digest.hexdigest(),
        license_note=license_note,
    )
    job = library.create_job(session, kind="ingest_pdf", payload={"source_id": str(source.id)})
    session.commit()
    body = _public_source(source)
    body["job_id"] = str(job.id)
    return body


@router.get("/api/sources/{source_id}")
def get_source(source_id: uuid.UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    source = library.get_source(session, source_id)
    if source is None:
        raise _not_found("source", source_id)
    return _public_source(source)


@router.get("/api/jobs/{job_id}")
def get_job(job_id: uuid.UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    job = library.get_job(session, job_id)
    if job is None:
        raise _not_found("job", job_id)
    return {
        "id": str(job.id),
        "kind": job.kind,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "attempts": job.attempts,
    }
