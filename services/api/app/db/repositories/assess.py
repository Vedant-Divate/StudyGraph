"""Assessment-time repositories: students, mastery, assessments, responses."""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import models


def create_student(
    session: Session, *, course_id: uuid.UUID, display_name: str | None = None
) -> models.Student:
    student = models.Student(course_id=course_id, display_name=display_name)
    session.add(student)
    session.flush()
    return student


def get_student(session: Session, student_id: uuid.UUID) -> models.Student | None:
    return session.get(models.Student, student_id)


def ensure_mastery(
    session: Session, *, student_id: uuid.UUID, concept_id: uuid.UUID
) -> models.MasteryState:
    row = session.get(models.MasteryState, (student_id, concept_id))
    if row is None:
        row = models.MasteryState(student_id=student_id, concept_id=concept_id)
        session.add(row)
        session.flush()
    return row


def list_mastery(session: Session, student_id: uuid.UUID) -> list[models.MasteryState]:
    return list(
        session.scalars(
            select(models.MasteryState).where(models.MasteryState.student_id == student_id)
        ).all()
    )


def create_assessment(
    session: Session,
    *,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    mode: str,
    scope: dict[str, Any],
) -> models.Assessment:
    assessment = models.Assessment(
        student_id=student_id, course_id=course_id, mode=mode, scope_json=scope
    )
    session.add(assessment)
    session.flush()
    return assessment


def get_assessment(session: Session, assessment_id: uuid.UUID) -> models.Assessment | None:
    return session.get(models.Assessment, assessment_id)


def add_item(
    session: Session,
    *,
    assessment_id: uuid.UUID,
    question_id: uuid.UUID,
    position: int,
    reason: str,
    mastery_before: float | None,
) -> models.AssessmentItem:
    item = models.AssessmentItem(
        assessment_id=assessment_id,
        question_id=question_id,
        position=position,
        selection_reason=reason,
        mastery_before=mastery_before,
    )
    session.add(item)
    session.flush()
    return item


def list_items(session: Session, assessment_id: uuid.UUID) -> list[models.AssessmentItem]:
    return list(
        session.scalars(
            select(models.AssessmentItem)
            .where(models.AssessmentItem.assessment_id == assessment_id)
            .order_by(models.AssessmentItem.position)
        ).all()
    )


def seen_question_ids(session: Session, student_id: uuid.UUID) -> set[uuid.UUID]:
    rows = session.execute(
        select(models.AssessmentItem.question_id)
        .join(
            models.Response,
            models.Response.assessment_item_id == models.AssessmentItem.id,
        )
        .where(models.Response.student_id == student_id)
    ).all()
    return {r[0] for r in rows}


def record_response(
    session: Session,
    *,
    item_id: uuid.UUID,
    student_id: uuid.UUID,
    response: dict[str, Any],
    score: float,
    is_correct: bool,
    misconception_id: uuid.UUID | None,
    feedback: dict[str, Any],
    time_ms: int = 0,
) -> models.Response:
    row = models.Response(
        assessment_item_id=item_id,
        student_id=student_id,
        response_json=response,
        score=score,
        is_correct=is_correct,
        chosen_misconception_id=misconception_id,
        feedback_json=feedback,
        time_ms=time_ms,
    )
    session.add(row)
    session.flush()
    return row


def list_responses(session: Session, assessment_id: uuid.UUID) -> list[models.Response]:
    return list(
        session.scalars(
            select(models.Response)
            .join(
                models.AssessmentItem,
                models.AssessmentItem.id == models.Response.assessment_item_id,
            )
            .where(models.AssessmentItem.assessment_id == assessment_id)
        ).all()
    )


def delete_student_data(session: Session, student_id: uuid.UUID) -> None:
    session.execute(delete(models.Response).where(models.Response.student_id == student_id))
    session.execute(delete(models.MasteryState).where(models.MasteryState.student_id == student_id))
    session.flush()
