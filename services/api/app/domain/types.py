"""Core domain types. Pure data + enums; no I/O, no imports from other app packages."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


class UnitKind(str, Enum):
    TEXT = "text"
    TRANSCRIPT = "transcript"
    FIGURE = "figure"
    SLIDE_TEXT = "slide_text"
    OCR = "ocr"


class ConceptLevel(str, Enum):
    TOPIC = "topic"
    SUBTOPIC = "subtopic"
    CONCEPT = "concept"


class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    NUMERICAL = "numerical"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SegmentLabel(str, Enum):
    SOURCE_BACKED = "source_backed"
    OUTSIDE_KNOWLEDGE = "outside_knowledge"
    NOT_COVERED = "not_covered"


@dataclass(frozen=True)
class Location:
    """Exactly one of page / slide / (t_start_s, t_end_s) must be set."""

    source_id: UUID
    page: int | None = None
    slide: int | None = None
    t_start_s: float | None = None
    t_end_s: float | None = None

    def kind(self) -> str:
        set_forms = [
            self.page is not None,
            self.slide is not None,
            self.t_start_s is not None or self.t_end_s is not None,
        ]
        if sum(set_forms) != 1:
            raise ValueError("location must have exactly one form")
        if self.page is not None:
            return "page"
        if self.slide is not None:
            return "slide"
        if self.t_start_s is None or self.t_end_s is None:
            raise ValueError("video location needs both t_start_s and t_end_s")
        if self.t_end_s < self.t_start_s:
            raise ValueError("t_end_s must be >= t_start_s")
        return "video"


@dataclass(frozen=True)
class ContentUnitRef:
    """Lightweight citable handle passed to the LLM (never a location)."""

    unit_id: UUID
    kind: UnitKind
    location: Location


@dataclass(frozen=True)
class Concept:
    concept_id: UUID
    course_id: UUID
    level: ConceptLevel
    name: str
    summary: str = ""
    parent_id: UUID | None = None
    importance: float = 0.0


@dataclass(frozen=True)
class ConceptEdge:
    prerequisite_id: UUID
    concept_id: UUID
    weight: float
    evidence_unit_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class MasteryState:
    student_id: UUID
    concept_id: UUID
    p_mastery: float
    stability_days: float = 3.0
    n_correct: int = 0
    n_incorrect: int = 0
    last_seen_at: str = ""


@dataclass(frozen=True)
class AnswerSegment:
    text: str
    label: SegmentLabel
    unit_ids: tuple[UUID, ...] = field(default_factory=tuple)
