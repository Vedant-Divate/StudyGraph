"""Tutor grounding tests with mock provider and an in-memory fake session."""

import uuid
from typing import Any

import pytest

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
        self.rollback_calls = 0
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

    def rollback(self) -> None:
        self.rollback_calls += 1

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

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: dict,
        model: str,
        timeout_s: float | None = None,
        enable_thinking: bool | None = None,
        system_prompt_prefix: str | None = None,
    ) -> Any:
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


def test_configured_retrieval_threshold_is_used() -> None:
    llm = ScriptedLLM(
        answer_segments=[
            {
                "text": "Bayes rule inverts conditional probabilities.",
                "label": "source_backed",
                "unit_ids": [str(PDF_ID)],
            }
        ],
        verdicts=[{"segment": 0, "supported": "yes", "reason": "supported by the unit"}],
    )
    settings = _settings()
    settings.retrieval_min_confidence = 0.0
    out = tutor.generate_answer(
        FakeSession([PDF_UNIT]),
        course_id=uuid.uuid4(),
        question="What is Bayes?",
        allow_outside=False,
        settings=settings,
        llm=llm,
    )
    assert out["segments"][0]["label"] == "source_backed"


def test_read_transaction_closes_before_model_calls() -> None:
    session = FakeSession([PDF_UNIT])

    class TransactionCheckingLLM(ScriptedLLM):
        def complete_structured(
            self,
            *,
            prompt: str,
            schema: dict,
            model: str,
            timeout_s: float | None = None,
            enable_thinking: bool | None = None,
            system_prompt_prefix: str | None = None,
        ) -> Any:
            assert session.rollback_calls == 1
            return super().complete_structured(
                prompt=prompt,
                schema=schema,
                model=model,
                timeout_s=timeout_s,
                enable_thinking=enable_thinking,
                system_prompt_prefix=system_prompt_prefix,
            )

    llm = TransactionCheckingLLM(
        answer_segments=[
            {
                "text": "Bayes rule inverts conditional probabilities.",
                "label": "source_backed",
                "unit_ids": [str(PDF_ID)],
            }
        ],
        verdicts=[{"segment": 0, "supported": "yes", "reason": "supported by the unit"}],
    )
    tutor.generate_answer(
        session,
        course_id=uuid.uuid4(),
        question="What is Bayes?",
        allow_outside=False,
        settings=_settings(),
        llm=llm,
        min_confidence=-1.0,
    )
    assert session.rollback_calls == 1


def test_chat_closes_course_lookup_before_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routers import study
    from app.db.repositories import library

    session = FakeSession([])
    monkeypatch.setattr(library, "get_course", lambda *_args: object())

    def generate_answer(session_arg: Any, **_kwargs: Any) -> dict[str, Any]:
        assert session_arg.rollback_calls == 1
        return {"segments": []}

    monkeypatch.setattr(study.tutor, "generate_answer", generate_answer)
    result = study.chat(uuid.uuid4(), study.ChatRequest(message="Question"), session)
    assert result == {"segments": []}


def test_role_timeouts_and_prompt_unit_truncation() -> None:
    settings = _settings()
    session = FakeSession([PDF_UNIT])

    class RoleCaptureLLM(ScriptedLLM):
        def __init__(self) -> None:
            super().__init__(
                answer_segments=[
                    {
                        "text": "Bayes rule inverts conditional probabilities.",
                        "label": "source_backed",
                        "unit_ids": [str(PDF_ID)],
                    }
                ],
                verdicts=[{"segment": 0, "supported": "yes", "reason": "supported"}],
            )
            self.options: list[tuple[float | None, bool | None]] = []
            self.prompts: list[str] = []
            self.system_prefixes: list[str | None] = []

        def complete_structured(
            self,
            *,
            prompt: str,
            schema: dict,
            model: str,
            timeout_s: float | None = None,
            enable_thinking: bool | None = None,
            system_prompt_prefix: str | None = None,
        ) -> Any:
            self.options.append((timeout_s, enable_thinking))
            self.prompts.append(prompt)
            self.system_prefixes.append(system_prompt_prefix)
            return super().complete_structured(
                prompt=prompt,
                schema=schema,
                model=model,
                timeout_s=timeout_s,
                enable_thinking=enable_thinking,
                system_prompt_prefix=system_prompt_prefix,
            )

    llm = RoleCaptureLLM()
    tutor.generate_answer(
        session,
        course_id=uuid.uuid4(),
        question="What is Bayes?",
        allow_outside=False,
        settings=settings,
        llm=llm,
        min_confidence=-1.0,
    )
    assert llm.options == [
        (settings.generation_timeout_s, settings.llm_enable_thinking),
        (settings.verifier_timeout_s, None),
    ]
    assert "Question: What is Bayes?" in llm.prompts[1]
    assert "directly answer the question" in llm.prompts[1]
    assert llm.system_prefixes[1] == "Reasoning: low."
    assert len(tutor._unit_text({"text": "x" * 700})) == 600


def test_verifier_failure_refuses_unverified_source_answer() -> None:
    class VerifierTimeoutLLM(ScriptedLLM):
        verifier_attempts = 0

        def complete_structured(
            self,
            *,
            prompt: str,
            schema: dict,
            model: str,
            timeout_s: float | None = None,
            enable_thinking: bool | None = None,
            system_prompt_prefix: str | None = None,
        ) -> Any:
            self.verifier_attempts += 1
            if self.verifier_attempts == 2:
                raise TimeoutError("verifier timeout")
            return super().complete_structured(
                prompt=prompt,
                schema=schema,
                model=model,
                timeout_s=timeout_s,
                enable_thinking=enable_thinking,
                system_prompt_prefix=system_prompt_prefix,
            )

    llm = VerifierTimeoutLLM(
        answer_segments=[
            {
                "text": "Bayes rule inverts conditional probabilities.",
                "label": "source_backed",
                "unit_ids": [str(PDF_ID)],
            }
        ],
        verdicts=[],
    )
    result = tutor.generate_answer(
        FakeSession([PDF_UNIT]),
        course_id=uuid.uuid4(),
        question="What is Bayes?",
        allow_outside=False,
        settings=_settings(),
        llm=llm,
        min_confidence=-1.0,
    )
    assert llm.verifier_attempts == 2
    assert result["segments"][0]["label"] == "not_covered"


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
        min_confidence=-1.0,
    )
    cites = [c for s in out["segments"] for c in s["citations"]]
    assert len(cites) == 2
    assert any("?page=3" in c["link"] for c in cites)
    assert any("?t=872" in c["link"] for c in cites)
    assert llm.calls == 2  # one generation + ONE batched verifier call
