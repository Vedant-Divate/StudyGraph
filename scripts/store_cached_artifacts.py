"""Persist the cached MIT OCW video and graph artifacts into PostgreSQL."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.config import get_settings  # noqa: E402
from app.db import models  # noqa: E402
from app.db.session import make_session_factory  # noqa: E402
from app.ingestion.video import merge_windows, parse_srt  # noqa: E402
from app.kb.embeddings import embed_texts  # noqa: E402
from app.kb.graph import tag_units  # noqa: E402

COURSE_NAMESPACE = uuid.UUID("a4301776-1a6a-49ec-b265-27717d3c7634")
COURSE_ID = uuid.uuid5(COURSE_NAMESPACE, "mit-ocw-6.041sc-fall-2013")
TABLES: tuple[type[models.Base], ...] = (
    models.Course,
    models.Source,
    models.ContentUnit,
    models.Concept,
    models.ConceptEdge,
    models.UnitConcept,
    models.Misconception,
)


def stable_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(COURSE_NAMESPACE, f"{kind}:{key}")


def _source_id(lecture: int) -> uuid.UUID:
    return stable_id("source", f"lecture-{lecture:02d}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = ROOT / "data" / "demo-course"
    graph = json.loads((base / "graph_draft.json").read_text(encoding="utf-8"))
    frames = json.loads((base / "thumb_desc.json").read_text(encoding="utf-8"))
    if not isinstance(graph.get("merged"), list) or not isinstance(graph.get("edges"), list):
        raise ValueError("graph_draft.json is missing merged concepts or edges")
    if not isinstance(frames, list):
        raise ValueError("thumb_desc.json must contain a list")
    return frames, graph


def _lecture_number(value: Any) -> int:
    match = re.search(r"\d+", str(value))
    if match is None:
        raise ValueError(f"invalid lecture identifier in frame cache: {value!r}")
    return int(match.group())


def _counts(session: Session) -> dict[str, int]:
    return {
        model.__tablename__: int(session.scalar(select(func.count()).select_from(model)) or 0)
        for model in TABLES
    }


def load() -> dict[str, int]:
    settings = get_settings()
    base = ROOT / "data" / "demo-course"
    frames, graph = _cache()

    source_rows: dict[int, models.Source] = {}
    windows_by_lecture: dict[int, list[tuple[float, float, str]]] = {}
    for lecture in (1, 2):
        video_path = base / f"lec{lecture:02d}.mp4"
        subtitle_path = base / f"lec{lecture:02d}.srt"
        if not video_path.is_file() or not subtitle_path.is_file():
            raise FileNotFoundError(f"cached video or subtitle missing for lecture {lecture}")
        segments = parse_srt(str(subtitle_path))
        windows = merge_windows(segments)
        if not windows:
            raise ValueError(f"no transcript windows found for lecture {lecture}")
        windows_by_lecture[lecture] = windows
        duration = max(end for _, end, _ in segments)
        source_rows[lecture] = models.Source(
            id=_source_id(lecture),
            course_id=COURSE_ID,
            kind="video",
            filename=f"MIT 6.041SC Lecture {lecture}",
            path=str(video_path.resolve()),
            sha256=_sha256_file(video_path),
            duration_s=duration,
            status="ready",
            license_note="MIT OpenCourseWare; CC BY-NC-SA 4.0",
        )

    unit_rows: list[models.ContentUnit] = []
    for lecture, windows in windows_by_lecture.items():
        source_id = _source_id(lecture)
        for index, (start, end, text) in enumerate(windows):
            unit_rows.append(
                models.ContentUnit(
                    id=stable_id("transcript", f"{lecture}:{index}:{start:.3f}:{end:.3f}"),
                    source_id=source_id,
                    kind="transcript",
                    text=text,
                    t_start_s=start,
                    t_end_s=end,
                    token_count=max(1, len(text.split())),
                )
            )
    for index, frame in enumerate(frames):
        lecture = _lecture_number(frame["lec"])
        if lecture not in source_rows:
            continue
        timestamp = float(frame["t"])
        duration = source_rows[lecture].duration_s or 0.0
        if timestamp < 0 or timestamp > duration:
            raise ValueError(f"frame timestamp outside lecture {lecture} duration")
        image_path = Path(str(frame.get("img", "")))
        if not image_path.is_absolute():
            image_path = base / image_path
        description = str(frame.get("desc", "")).strip()
        if not description:
            raise ValueError(f"empty cached frame description at record {index}")
        unit_rows.append(
            models.ContentUnit(
                id=stable_id("figure", f"{lecture}:{timestamp:.3f}:{index}"),
                source_id=_source_id(lecture),
                kind="figure",
                text=f"Video frame at {timestamp:.0f}s.",
                figure_description=description,
                t_start_s=timestamp,
                t_end_s=timestamp,
                image_path=str(image_path.resolve()) if image_path.is_file() else None,
                token_count=max(1, len(description.split())),
            )
        )

    concept_specs = graph["merged"]
    concept_ids = {
        item["name"]: stable_id("concept", item["name"].strip().lower()) for item in concept_specs
    }
    current_topic: uuid.UUID | None = None
    current_subtopic: uuid.UUID | None = None
    concept_rows: list[models.Concept] = []
    for item in concept_specs:
        name = str(item["name"])
        level = str(item["level"])
        if level == "topic":
            parent = None
            current_topic = concept_ids[name]
            current_subtopic = None
        elif level == "subtopic":
            parent = current_topic
            current_subtopic = concept_ids[name]
        else:
            parent = current_subtopic or current_topic
        concept_rows.append(
            models.Concept(
                id=concept_ids[name],
                course_id=COURSE_ID,
                parent_id=parent,
                level=level,
                name=name,
                summary=str(item.get("summary", "")),
                importance=0.0,
            )
        )

    unit_texts = [
        row.text + ("\n" + row.figure_description if row.figure_description else "")
        for row in unit_rows
    ]
    concept_texts = [f"{item['name']}\n{item.get('summary', '')}" for item in concept_specs]
    vectors = embed_texts(unit_texts + concept_texts, settings=settings)
    for row, vector in zip(unit_rows, vectors[: len(unit_rows)], strict=True):
        row.embedding = vector
    concept_vectors = [
        (concept_ids[item["name"]], vector)
        for item, vector in zip(concept_specs, vectors[len(unit_rows) :], strict=True)
    ]
    tags = tag_units(
        [(str(row.id), row.embedding or []) for row in unit_rows],
        concept_vectors,
    )
    tagged_rows = [
        models.UnitConcept(unit_id=uuid.UUID(unit_id), concept_id=concept_id, score=score)
        for unit_id, concept_tags in tags.items()
        for concept_id, score in concept_tags
    ]
    tag_counts = Counter(row.concept_id for row in tagged_rows)
    total_tags = sum(tag_counts.values())
    for concept in concept_rows:
        concept.importance = tag_counts[concept.id] / total_tags if total_tags else 0.0

    edge_rows = []
    for edge in graph["edges"]:
        prerequisite = concept_ids.get(str(edge.get("prerequisite", "")))
        concept = concept_ids.get(str(edge.get("concept", "")))
        if prerequisite is None or concept is None or prerequisite == concept:
            continue
        edge_rows.append(
            models.ConceptEdge(
                id=stable_id("edge", f"{prerequisite}:{concept}"),
                course_id=COURSE_ID,
                prerequisite_id=prerequisite,
                concept_id=concept,
                weight=float(edge.get("weight", 0.5)),
                evidence_json={"weak": True, "evidence_unit_ids": []},
            )
        )

    misconception_rows = []
    for cache_key, items in graph.get("misconceptions", {}).items():
        matching_name = next(
            (
                name
                for name in concept_ids
                if cache_key == name or cache_key.startswith(name + ": ")
            ),
            None,
        )
        if matching_name is None:
            continue
        for item in items:
            label = str(item.get("label", "")).strip()
            if not label:
                continue
            misconception_rows.append(
                models.Misconception(
                    id=stable_id("misconception", f"{concept_ids[matching_name]}:{label}"),
                    concept_id=concept_ids[matching_name],
                    label=label[:300],
                    description=str(item.get("description", "")),
                    origin="llm_suggested",
                    evidence_json={"evidence_unit_ids": []},
                )
            )

    factory = make_session_factory(settings.database_url)
    with factory.begin() as session:
        course = session.get(models.Course, COURSE_ID)
        if course is None:
            course = models.Course(
                id=COURSE_ID,
                title="MIT OCW 6.041SC — Probabilistic Systems Analysis and Applied Probability",
                description="Fall 2013 demo course.",
                is_demo=True,
            )
            session.add(course)
        else:
            course.title = (
                "MIT OCW 6.041SC — Probabilistic Systems Analysis and Applied Probability"
            )
            course.description = "Fall 2013 demo course."
            course.is_demo = True
        session.flush()

        session.execute(delete(models.ConceptEdge).where(models.ConceptEdge.course_id == COURSE_ID))
        source_ids = [source.id for source in source_rows.values()]
        existing_sources = list(
            session.scalars(select(models.Source).where(models.Source.id.in_(source_ids)))
        )
        concept_ids_query = select(models.Concept.id).where(
            models.Concept.course_id == COURSE_ID
        )
        source_unit_ids = select(models.ContentUnit.id).where(
            models.ContentUnit.source_id.in_(source_ids)
        )
        session.execute(
            delete(models.UnitConcept).where(
                models.UnitConcept.unit_id.in_(source_unit_ids)
                | models.UnitConcept.concept_id.in_(concept_ids_query)
            )
        )
        session.execute(
            delete(models.Misconception).where(
                models.Misconception.concept_id.in_(concept_ids_query)
            )
        )
        for source in existing_sources:
            session.execute(
                delete(models.ContentUnit).where(models.ContentUnit.source_id == source.id)
            )
        session.flush()
        for source in source_rows.values():
            session.merge(source)
        session.execute(
            update(models.Concept)
            .where(models.Concept.course_id == COURSE_ID)
            .values(parent_id=None)
        )
        session.flush()
        session.execute(delete(models.Concept).where(models.Concept.course_id == COURSE_ID))
        session.flush()
        session.add_all(concept_rows)
        session.add_all(unit_rows)
        session.add_all(edge_rows)
        session.add_all(tagged_rows)
        session.add_all(misconception_rows)
        session.flush()
        counts = _counts(session)
        counts["loaded_video_units"] = len(unit_rows)
        counts["loaded_transcript_units"] = sum(row.kind == "transcript" for row in unit_rows)
        counts["loaded_figure_units"] = sum(row.kind == "figure" for row in unit_rows)
        counts["loaded_concepts"] = len(concept_rows)
        counts["loaded_edges"] = len(edge_rows)
        counts["loaded_unit_tags"] = len(tagged_rows)
        counts["loaded_misconceptions"] = len(misconception_rows)
        counts["untagged_units"] = sum(not tags.get(str(row.id)) for row in unit_rows)
    factory.kw["bind"].dispose()
    return counts


if __name__ == "__main__":
    for table, count in load().items():
        print(f"{table}: {count}")
