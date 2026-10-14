"""Quiz + learner-model routes (Phase 6-7 slice)."""

import datetime as dt
import math
import random
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.config import get_settings
from app.db import models
from app.db.repositories import assess as repo
from app.db.repositories import library
from app.domain import bkt, expr
from app.domain.scoring import score_mcq
from app.learner import model as learner_model
from app.learner import policy

router = APIRouter()


class StudentCreate(BaseModel):
    course_id: uuid.UUID
    display_name: str | None = None


class AssessmentCreate(BaseModel):
    student_id: uuid.UUID
    mode: str = "adaptive"
    scope: dict[str, Any] = {"all": True}
    n: int = 8


class AnswerSubmit(BaseModel):
    item_id: uuid.UUID
    student_id: uuid.UUID
    choice_key: str | None = None
    value: float | None = None
    time_ms: int = 0


def _course_or_404(session: Session, course_id: uuid.UUID) -> models.Course:
    course = library.get_course(session, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="course not found")
    return course


def _concepts(session: Session, course_id: uuid.UUID) -> list[models.Concept]:
    return list(
        session.scalars(select(models.Concept).where(models.Concept.course_id == course_id)).all()
    )


def _edges(session: Session, course_id: uuid.UUID) -> list[tuple[Any, Any, float]]:
    rows = session.scalars(
        select(models.ConceptEdge).where(models.ConceptEdge.course_id == course_id)
    ).all()
    return [(r.prerequisite_id, r.concept_id, r.weight) for r in rows]


def _prereq_map(edges: list[tuple[Any, Any, float]]) -> dict[Any, list[Any]]:
    out: dict[Any, list[Any]] = {}
    for pre, con, _w in edges:
        out.setdefault(con, []).append(pre)
    return out


def _topic_of(session: Session, concept: models.Concept) -> Any:
    node: models.Concept | None = concept
    while node is not None and node.level != "topic":
        node = session.get(models.Concept, node.parent_id) if node.parent_id else None
    return node.id if node else concept.id


def _mastery_snapshot(
    session: Session, student_id: uuid.UUID, concepts: list[models.Concept]
) -> tuple[dict[Any, float], dict[Any, float], dict[Any, models.MasteryState]]:
    now = dt.datetime.now(dt.UTC)
    m_effs: dict[Any, float] = {}
    p_map: dict[Any, float] = {}
    rows: dict[Any, models.MasteryState] = {}
    for concept in concepts:
        row = repo.ensure_mastery(session, student_id=student_id, concept_id=concept.id)
        days = max(0.0, (now - row.last_seen_at).total_seconds() / 86400.0)
        meff = bkt.effective_mastery(
            row.p_mastery, days_since_seen=days, stability_days=row.stability_days
        )
        m_effs[concept.id] = meff
        p_map[concept.id] = row.p_mastery
        rows[concept.id] = row
    return m_effs, p_map, rows


def _public_question(question: models.Question) -> dict[str, Any]:
    options = (question.options_json or {}).get("options", [])
    return {
        "id": str(question.id),
        "type": question.type,
        "stem": question.stem,
        "options": [{"key": o.get("key"), "text": o.get("text")} for o in options],
        "difficulty": question.difficulty,
        "concept_id": str(question.concept_id) if question.concept_id else None,
        "requires_figure": question.requires_figure,
        "figure_unit_id": str(question.figure_unit_id) if question.figure_unit_id else None,
    }


def _pick_bank_question(
    session: Session,
    *,
    course_id: uuid.UUID,
    concept_id: uuid.UUID,
    difficulty: str,
    exclude_ids: set[uuid.UUID],
    threshold: float,
) -> models.Question | None:
    rows = session.scalars(
        select(models.Question)
        .where(
            models.Question.course_id == course_id,
            models.Question.concept_id == concept_id,
            models.Question.difficulty == difficulty,
        )
        .order_by(models.Question.created_at)
    ).all()
    if not rows:
        rows = session.scalars(
            select(models.Question)
            .where(
                models.Question.course_id == course_id,
                models.Question.concept_id == concept_id,
            )
            .order_by(models.Question.created_at)
        ).all()
    seen_vecs: list[list[float]] = []
    if exclude_ids:
        seen_rows = session.scalars(
            select(models.Question).where(models.Question.id.in_(exclude_ids))
        ).all()
        seen_vecs = [list(q.embedding) for q in seen_rows if q.embedding]
    for question in rows:
        if question.id in exclude_ids:
            continue
        if question.embedding and any(
            _cosine(list(question.embedding), v) >= threshold
            for v in seen_vecs
            if len(v) == len(list(question.embedding))
        ):
            continue
        return question
    return None


def _cosine(a: list[float], b: list[float]) -> float:
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / denom


def _resolve_unit(session: Session, uid: uuid.UUID) -> dict[str, Any] | None:
    from app.domain import citation as cite_mod
    from app.domain.types import Location

    unit = session.get(models.ContentUnit, uid)
    if unit is None:
        return None
    source = session.get(models.Source, unit.source_id)
    title = source.filename if source else "source"
    if unit.page is not None:
        loc = Location(source_id=unit.source_id, page=unit.page)
    elif unit.slide is not None:
        loc = Location(source_id=unit.source_id, slide=unit.slide)
    elif unit.t_start_s is not None and unit.t_end_s is not None:
        loc = Location(source_id=unit.source_id, t_start_s=unit.t_start_s, t_end_s=unit.t_end_s)
    else:
        return None
    return {
        "unit_id": str(uid),
        "display": cite_mod.display_string(loc, title),
        "link": cite_mod.deep_link(loc),
    }


def _recap_citations(
    session: Session, concept_id: uuid.UUID, limit: int = 2
) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(models.UnitConcept)
        .where(models.UnitConcept.concept_id == concept_id)
        .order_by(models.UnitConcept.score.desc())
        .limit(limit)
    ).all()
    out = []
    for row in rows:
        resolved = _resolve_unit(session, row.unit_id)
        if resolved:
            out.append(resolved)
    return out


@router.post("/api/students")
def create_student(body: StudentCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    _course_or_404(session, body.course_id)
    student = repo.create_student(session, course_id=body.course_id, display_name=body.display_name)
    session.commit()
    return {"id": str(student.id), "course_id": str(student.course_id)}


@router.post("/api/courses/{course_id}/assessments")
def create_assessment(
    course_id: uuid.UUID, body: AssessmentCreate, session: Session = Depends(get_session)
) -> dict[str, Any]:
    course = _course_or_404(session, course_id)
    student = repo.get_student(session, body.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="student not found")
    assessment = repo.create_assessment(
        session,
        student_id=student.id,
        course_id=course.id,
        mode=body.mode,
        scope={"n": body.n, **body.scope},
    )
    session.commit()
    return {"id": str(assessment.id), "mode": assessment.mode, "n": body.n}


@router.get("/api/assessments/{assessment_id}/next")
def next_question(
    assessment_id: uuid.UUID, session: Session = Depends(get_session)
) -> dict[str, Any]:
    settings = get_settings()
    assessment = repo.get_assessment(session, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="assessment not found")
    concepts = _concepts(session, assessment.course_id)
    if not concepts:
        raise HTTPException(status_code=400, detail="course has no concepts")
    edges = _edges(session, assessment.course_id)
    m_effs, _p_map, _rows = _mastery_snapshot(session, assessment.student_id, concepts)
    items = repo.list_items(session, assessment.id)
    seen = repo.seen_question_ids(session, assessment.student_id) | {i.question_id for i in items}
    scope = assessment.scope_json or {}
    concept_ids = set(scope.get("concept_ids") or [c.id for c in concepts])
    cand = [c for c in concepts if c.id in concept_ids]
    info = [
        {"id": c.id, "name": c.name, "importance": c.importance, "topic_id": _topic_of(session, c)}
        for c in cand
    ]
    n_target = int(scope.get("n", 8))
    if not items and assessment.mode == "adaptive":
        order = policy.opening_set(info, n=n_target)
    else:
        order = None
    last_concept = None
    if items:
        last_q = session.get(models.Question, items[-1].question_id)
        last_concept = last_q.concept_id if last_q else None
    asked_concepts: set[Any] = set()
    for existing in items:
        existing_q = session.get(models.Question, existing.question_id)
        if existing_q and existing_q.concept_id:
            asked_concepts.add(existing_q.concept_id)
    attempts: list[dict[str, Any]] = []
    if order is not None:
        ordered_targets = [c for c in order if c["id"] not in asked_concepts] or order
        for target in ordered_targets:
            attempts.append(
                {
                    "concept": target,
                    "reason": (
                        f"Opening: {target['name']} (importance {target['importance']:.2f})."
                    ),
                    "difficulty": "medium",
                    "prereq_first": False,
                }
            )
    else:
        first = policy.choose(
            info,
            _prereq_map(edges),
            m_effs,
            seen_ids=set(),
            last_concept_id=last_concept,
            exploration_rate=settings.exploration_rate,
            rng=random.Random(),
        )
        attempts.append(first)
        rest = sorted(
            [c for c in info if c["id"] != first["concept"]["id"]],
            key=lambda c: -c["importance"],
        )
        for concept in rest:
            attempts.append(
                {
                    "concept": concept,
                    "reason": f"Fallback: {concept['name']} (bank exhausted upstream).",
                    "difficulty": policy.difficulty_for(m_effs.get(concept["id"], 0.3)),
                    "prereq_first": False,
                }
            )
    question = None
    pick = attempts[0]
    for attempt in attempts:
        concept = attempt["concept"]
        for diff in (attempt["difficulty"], "medium", "easy", "hard"):
            question = _pick_bank_question(
                session,
                course_id=assessment.course_id,
                concept_id=concept["id"],
                difficulty=diff,
                exclude_ids=seen,
                threshold=settings.question_dup_threshold,
            )
            if question is not None:
                break
        if question is not None:
            pick = attempt
            break
    if question is None:
        raise HTTPException(status_code=404, detail="no unseen questions for this scope")
    concept = pick["concept"]
    item = repo.add_item(
        session,
        assessment_id=assessment.id,
        question_id=question.id,
        position=len(items),
        reason=pick["reason"],
        mastery_before=m_effs.get(concept["id"]),
    )
    session.commit()
    body = _public_question(question)
    body["item_id"] = str(item.id)
    body["selection_reason"] = pick["reason"]
    body["course_id"] = str(assessment.course_id)
    return body


@router.post("/api/assessments/{assessment_id}/answers")
def submit_answer(
    assessment_id: uuid.UUID, body: AnswerSubmit, session: Session = Depends(get_session)
) -> dict[str, Any]:
    settings = get_settings()
    assessment = repo.get_assessment(session, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="assessment not found")
    item = next((i for i in repo.list_items(session, assessment.id) if i.id == body.item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    question = session.get(models.Question, item.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="question not found")
    options = (question.options_json or {}).get("options", [])
    key = (body.choice_key or "").strip().upper()
    answer_key = ((question.answer_key_json or {}).get("key") or "").strip().upper()
    misconception_id = None
    why_wrong = None
    explanation = question.explanation or ""
    if question.type == "mcq":
        correct = score_mcq(key, answer_key) == 1.0
        score = 1.0 if correct else 0.0
        if not correct:
            chosen = next((o for o in options if o.get("key") == key), None)
            if chosen:
                why_wrong = chosen.get("why_wrong")
                mid = chosen.get("misconception_id")
                try:
                    misconception_id = uuid.UUID(mid) if mid else None
                except ValueError:
                    misconception_id = None
    elif question.type == "numerical":
        try:
            key_json = question.answer_key_json or {}
            variables = {k: float(v) for k, v in (key_json.get("variables") or {}).items()}
            expected = expr.evaluate(str(question.solution_expression or ""), variables)
            tol = float(key_json.get("tolerance_rel", 0.01) or 0.01)
            correct = body.value is not None and expr.within_tolerance(body.value, expected, tol)
        except Exception:  # noqa: BLE001 - malformed bank entry counts as wrong
            correct = False
        score = 1.0 if correct else 0.0
    else:
        raise HTTPException(status_code=400, detail="unsupported question type")
    num_options = len(options) if options else 4
    updates_log: list[dict[str, Any]] = []
    mastery_delta = 0.0
    root_trace = None
    if question.concept_id:
        row = repo.ensure_mastery(
            session, student_id=body.student_id, concept_id=question.concept_id
        )
        p_new, stab_new = learner_model.update_mastery(
            row.p_mastery,
            row.stability_days,
            correct=correct,
            qtype=question.type,
            difficulty=question.difficulty,
            num_options=num_options,
            p_learn=settings.bkt_p_learn,
        )
        mastery_delta = p_new - row.p_mastery
        row.p_mastery, row.stability_days = p_new, stab_new
        updates_log.append({"concept_id": str(question.concept_id), "p": p_new})
        if not correct:
            edges = _edges(session, assessment.course_id)
            pmap = {r.concept_id: r.p_mastery for r in repo.list_mastery(session, body.student_id)}
            from app.learner import model as learner_mod

            new_map = learner_mod.propagate_incorrect(
                pmap,
                [(a, b, w) for a, b, w in edges],
                question.concept_id,
                alpha0=settings.propagation_alpha0,
            )
            weakest = None
            for pid, pval in new_map.items():
                if pid == question.concept_id:
                    continue
                old = pmap.get(pid, pval)
                if pval < old - 1e-9 and (weakest is None or pval < new_map[weakest]):
                    weakest = pid
                target_row = repo.ensure_mastery(
                    session, student_id=body.student_id, concept_id=pid
                )
                target_row.p_mastery = pval
            if weakest is not None:
                weak_concept = session.get(models.Concept, weakest)
                root_trace = {
                    "concept": question.concept_id and str(question.concept_id),
                    "weak_prerequisite": str(weakest),
                    "weak_name": weak_concept.name if weak_concept else "?",
                    "recap": _recap_citations(session, weakest),
                }
    misconception = None
    if misconception_id:
        row_m = session.get(models.Misconception, misconception_id)
        if row_m:
            misconception = {"label": row_m.label, "origin": row_m.origin}
    cited = []
    for uid in (question.source_unit_ids_json or [])[:4]:
        try:
            resolved = _resolve_unit(session, uuid.UUID(uid))
        except ValueError:
            continue
        if resolved:
            cited.append(resolved)
    feedback = {
        "correct": correct,
        "score": score,
        "explanation": explanation,
        "why_wrong": why_wrong,
        "misconception": misconception,
        "cited_units": cited,
        "mastery_delta": mastery_delta,
        "root_cause": root_trace,
        "updates": updates_log,
    }
    repo.record_response(
        session,
        item_id=item.id,
        student_id=body.student_id,
        response={"choice_key": key, "value": body.value},
        score=score,
        is_correct=correct,
        misconception_id=misconception_id,
        feedback=feedback,
        time_ms=body.time_ms,
    )
    session.commit()
    return feedback


@router.post("/api/assessments/{assessment_id}/finish")
def finish_assessment(
    assessment_id: uuid.UUID, session: Session = Depends(get_session)
) -> dict[str, Any]:
    assessment = repo.get_assessment(session, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="assessment not found")
    items = repo.list_items(session, assessment.id)
    responses = repo.list_responses(session, assessment.id)
    by_item = {r.assessment_item_id: r for r in responses}
    correct = sum(1 for r in responses if r.is_correct)
    by_concept: dict[str, dict[str, int]] = {}
    misconception_hits: dict[str, int] = {}
    for item in items:
        response = by_item.get(item.id)
        question = session.get(models.Question, item.question_id)
        if question is None or question.concept_id is None:
            continue
        entry = by_concept.setdefault(str(question.concept_id), {"correct": 0, "total": 0})
        entry["total"] += 1
        if response and response.is_correct:
            entry["correct"] += 1
        if response and response.chosen_misconception_id:
            key = str(response.chosen_misconception_id)
            misconception_hits[key] = misconception_hits.get(key, 0) + 1
    mastery_now = {
        str(r.concept_id): r.p_mastery for r in repo.list_mastery(session, assessment.student_id)
    }
    weak = [
        cid
        for cid, entry in by_concept.items()
        if entry["total"] and entry["correct"] / entry["total"] < 0.6
    ]
    assessment.status = "finished"
    import datetime as dt_module

    assessment.finished_at = dt_module.datetime.now(dt_module.UTC)
    session.commit()
    likely = []
    for mid, count in sorted(misconception_hits.items(), key=lambda kv: -kv[1])[:5]:
        row_m = session.get(models.Misconception, uuid.UUID(mid))
        if row_m:
            likely.append({"label": row_m.label, "origin": row_m.origin, "count": count})
    return {
        "score": correct,
        "total": len(items),
        "course_id": str(assessment.course_id),
        "by_concept": by_concept,
        "weak_concepts": weak,
        "likely_misconceptions": likely,
        "mastery": mastery_now,
        "next": "Practice the weak concepts above, easiest first."
        if weak
        else "All strong. Try a harder scope.",
    }


@router.get("/api/students/{student_id}/mastery")
def get_mastery(student_id: uuid.UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    student = repo.get_student(session, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="student not found")
    concepts = _concepts(session, student.course_id)
    m_effs, _p, _rows = _mastery_snapshot(session, student_id, concepts)
    out = []
    for concept in concepts:
        meff = m_effs[concept.id]
        band = bkt.mastery_band(meff)
        color = {"weak": "red", "developing": "amber", "strong": "green"}[band]
        icon = {"weak": "!", "developing": "~", "strong": "✓"}[band]
        out.append(
            {
                "concept_id": str(concept.id),
                "name": concept.name,
                "m_eff": meff,
                "band": band,
                "color": color,
                "icon": icon,
            }
        )
    return {"concepts": out}
