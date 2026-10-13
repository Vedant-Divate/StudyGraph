"""CRUD repositories (Phase 1-2 slice: courses, sources, units, jobs)."""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import models


def create_course(
    session: Session, *, title: str, description: str = "", is_demo: bool = False
) -> models.Course:
    course = models.Course(title=title, description=description, is_demo=is_demo)
    session.add(course)
    session.flush()
    return course


def get_course(session: Session, course_id: uuid.UUID) -> models.Course | None:
    return session.get(models.Course, course_id)


def create_source(
    session: Session,
    *,
    course_id: uuid.UUID,
    kind: str,
    filename: str,
    path: str,
    sha256: str,
    license_note: str | None = None,
) -> models.Source:
    source = models.Source(
        course_id=course_id,
        kind=kind,
        filename=filename,
        path=path,
        sha256=sha256,
        license_note=license_note,
    )
    session.add(source)
    session.flush()
    return source


def get_source(session: Session, source_id: uuid.UUID) -> models.Source | None:
    return session.get(models.Source, source_id)


def set_source_status(
    session: Session,
    source: models.Source,
    status: str,
    *,
    error: str | None = None,
    page_count: int | None = None,
    duration_s: float | None = None,
    quality_json: dict[str, Any] | None = None,
) -> models.Source:
    source.status = status
    source.error = error
    if page_count is not None:
        source.page_count = page_count
    if duration_s is not None:
        source.duration_s = duration_s
    if quality_json is not None:
        source.quality_json = quality_json
    session.flush()
    return source


def replace_source_units(
    session: Session, *, source_id: uuid.UUID, units: list[models.ContentUnit]
) -> list[models.ContentUnit]:
    """Idempotent re-ingest: delete units for (source, sha) scope, insert fresh."""
    existing = session.scalars(
        select(models.ContentUnit).where(models.ContentUnit.source_id == source_id)
    ).all()
    for unit in existing:
        session.delete(unit)
    session.flush()
    session.add_all(units)
    session.flush()
    return units


def list_source_units(session: Session, source_id: uuid.UUID) -> list[models.ContentUnit]:
    return list(
        session.scalars(
            select(models.ContentUnit)
            .where(models.ContentUnit.source_id == source_id)
            .order_by(models.ContentUnit.page, models.ContentUnit.created_at)
        ).all()
    )


def create_job(session: Session, *, kind: str, payload: dict[str, Any] | None = None) -> models.Job:
    job = models.Job(kind=kind, payload_json=payload or {})
    session.add(job)
    session.flush()
    return job


def get_job(session: Session, job_id: uuid.UUID) -> models.Job | None:
    return session.get(models.Job, job_id)


def claim_next_job(session: Session) -> models.Job | None:
    job = session.scalars(
        select(models.Job)
        .where(models.Job.status == "queued")
        .order_by(models.Job.created_at)
        .limit(1)
    ).first()
    if job is None:
        return None
    job.status = "processing"
    job.attempts += 1
    session.flush()
    return job


def finish_job(
    session: Session,
    job: models.Job,
    *,
    progress: float = 1.0,
    error: str | None = None,
) -> models.Job:
    job.progress = progress
    if error is None:
        job.status = "done"
    else:
        job.status = "failed"
        job.error = error
    session.flush()
    return job


def delete_job(session: Session, job_id: uuid.UUID) -> None:
    session.execute(delete(models.Job).where(models.Job.id == job_id))
    session.flush()
