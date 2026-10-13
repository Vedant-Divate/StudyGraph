"""Tutor grounding tests with mock provider and an in-memory fake session."""

import uuid
from typing import Any

from app.db import models
from app.tutor import answer as tutor

PDF_ID = uuid.uuid4()
VID_ID = uuid.uuid4()
SRC_PDF = uuid.uuid4()
SRC_VID = uuid.uuid4()


def _unit(uid: uuid.UUID, source: uuid.UUID, **kwargs: Any) -> models.ContentUnit:
    from app.llm.mock_provider import hash_embed

    base: dict[str, Any] = {
        "id": uid,
        "source_id": source,
        "kind": "text",
        "text": "Bayes rule inverts conditional probabilities.",
        "figure_description": None,
        "page": None,
        "slide": None,
        "t_start_s": None,
        "t_end_s": None,
        "embedding": hash_embed("bayes"),
    }
    base.update(kwargs)
    return models.ContentUnit(**base)


PDF_UNIT = _unit(PDF_ID, SRC_PDF, page=3, text="Bayes rule inverts conditional probabilities.")
VID_UNIT = _unit(
    VID_ID,
    SRC_VID,
    kind="transcript",
    t_start_s=872.0,
    t_end_s=900.0,
    text="The lecturer explains Bayes rule at the board.",
)


class _Rows:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows

    def first(self) -> Any | None:
        return self._rows[0] if self._rows else None


class FakeSession:
    """Minimal stand-in: scripted retrieval rows, real model instances for .get()."""

    def __init__(self, units: list[models.ContentUnit]) -> None:
        self._units = {u.id: u for u in units}
        self._sources = {
            SRC_PDF: models.Source(
                id=SRC_PDF,
                course_id=uuid.uuid4(),
                kind="pdf",
                filename="L02.pdf",
                path="/tmp/x.pdf",
                sha256="s",
            ),
            SRC_VID: models.Source(
                id=SRC_VID,
                course_id=uuid.uuid4(),
                kind="video",
                filename="lec02.mp4",
                path="/tmp/x.mp4",
                sha256="s",
            ),
        }

    def execute(self, stmt: Any) -> _Rows:
        from app.llm.mock_provider import hash_embed

        vec = hash_embed("bayes")
        if "ts_rank" in str(stmt):
            return _Rows([(u.id, 0.8) for u in self._units.values()])
        return _Rows([(u.id, vec) for u in self._units.values()])

    def scalars(self, _stmt: Any) -> _Rows:
        return _Rows(list(self._units.values()))

    def get(self, model: Any, ident: Any) -> Any | None:
        if model is models.ContentUnit:
            return self._units.get(ident)
        if model is models.Source:
            return self._sources.get(ident)
        return None

    def query(self, *_args: Any) -> Any:
        class _Q:
            def filter(self, *_a: Any) -> "_Q":
                return self

            def limit(self, *_a: Any) -> "_Q":
                return self

            def all(self) -> list[Any]:
                return [("Probability Models",), ("Bayes Rule",)]

        return _Q()


class ScriptedLLM:
    """Canned answer + verifier. Modes switch per test."""

    def __init__(self, *, answer_segments: list[dict], verdicts: list[dict]) -> None:
        self._answer = answer_segments
        self._verdicts = verdicts
        self.calls = 0

    def complete_structured(self, *, prompt: str, schema: dict, model: str) -> Any:
        from app.llm.provider import StructuredResult

        self.calls += 1
        if "SEGMENT" in prompt:
            return StructuredResult(data={"checks": self._verdicts}, model=model)
        return StructuredResult(data={"segments": self._answer}, model=model)


def _settings() -> Any:
    from app.config import get_settings

    settings = get_settings()
    settings.llm_provider = "mock"
    settings.embed_backend = "hash"
    return settings


def test_unsupported_claim_downgraded() -> None:
    llm = ScriptedLLM(
        answer_segments=[
            {
                "text": "Bayes inverts conditionals.",
                "label": "source_backed",
                "unit_ids": [str(PDF_ID)],
            }
        ],
        verdicts=[{"segment": 0, "supported": "no", "reason": "not in units"}],
    )
    out = tutor.generate_answer(
        FakeSession([PDF_UNIT]),
        course_id=uuid.uuid4(),
        question="What is Bayes?",
        allow_outside=False,
        settings=_settings(),
        llm=llm,
    )
    assert out["segments"][0]["label"] != "source_backed"
    assert out["segments"][0]["label"] in ("outside_knowledge", "not_covered")


def test_hallucinated_unit_id_rejected() -> None:
    ghost = str(uuid.uuid4())
    llm = ScriptedLLM(
        answer_segments=[{"text": "Ghost claim.", "label": "source_backed", "unit_ids": [ghost]}],
        verdicts=[],
    )
    out = tutor.generate_answer(
        FakeSession([PDF_UNIT]),
        course_id=uuid.uuid4(),
        question="Ghost?",
        allow_outside=False,
        settings=_settings(),
        llm=llm,
    )
    labels = [s["label"] for s in out["segments"]]
    assert "source_backed" not in labels


def test_refusal_triggers_on_empty_retrieval() -> None:
    llm = ScriptedLLM(answer_segments=[], verdicts=[])
    out = tutor.generate_answer(
        FakeSession([]),
        course_id=uuid.uuid4(),
        question="Off topic?",
        allow_outside=False,
        settings=_settings(),
        llm=llm,
        min_confidence=0.99,
    )
    assert out["segments"][0]["label"] == "not_covered"


def test_citations_resolve_pdf_and_video() -> None:
    llm = ScriptedLLM(
        answer_segments=[
            {"text": "From slides.", "label": "source_backed", "unit_ids": [str(PDF_ID)]},
            {"text": "From video.", "label": "source_backed", "unit_ids": [str(VID_ID)]},
        ],
        verdicts=[
            {"segment": 0, "supported": "yes", "reason": "ok"},
            {"segment": 1, "supported": "yes", "reason": "ok"},
        ],
    )
    out = tutor.generate_answer(
        FakeSession([PDF_UNIT, VID_UNIT]),
        course_id=uuid.uuid4(),
        question="Bayes?",
        allow_outside=False,
        settings=_settings(),
        llm=llm,
        min_confidence=0.0,
    )
    cites = [c for s in out["segments"] for c in s["citations"]]
    assert len(cites) == 2
    assert any("?page=3" in c["link"] for c in cites)
    assert any("?t=872" in c["link"] for c in cites)
    assert llm.calls == 2  # one generation + ONE batched verifier call
