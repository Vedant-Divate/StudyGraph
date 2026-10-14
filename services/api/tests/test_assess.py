"""Assess verification + dedup tests (mock solver, no network)."""

from typing import Any

from app.assess import dedup
from app.assess.generate import normalize_stem, stem_hash
from app.assess.verify import verify_mcq, verify_numerical
from app.llm.provider import StructuredResult

MISCS = ["Confusing P(A|B) with P(B|A)", "Assuming independence"]


def _mcq(key: str = "B") -> dict[str, Any]:
    return {
        "stem": "Given P(A)=0.5, P(B|A)=0.4, P(B)=0.3, find P(A|B).",
        "options": [
            {
                "key": "A",
                "text": "0.2",
                "is_correct": False,
                "misconception": MISCS[0],
                "why_wrong": "Inverts the conditional.",
            },
            {
                "key": "B",
                "text": "0.67",
                "is_correct": key == "B",
                "misconception": "",
                "why_wrong": "",
            },
            {
                "key": "C",
                "text": "1.2",
                "is_correct": False,
                "misconception": MISCS[1],
                "why_wrong": "Multiplies as if independent.",
            },
            {
                "key": "D",
                "text": "0.5",
                "is_correct": key == "D",
                "misconception": "new",
                "why_wrong": "Ignores the given data.",
            },
        ],
    }


def _solver(pick: str) -> Any:
    class _S:
        def complete_structured(self, *, prompt: str, schema: dict, model: str) -> StructuredResult:
            if "value" in str(schema):
                return StructuredResult(data={"value": 0.667}, model=model)
            return StructuredResult(
                data={"picked_key": pick, "exactly_one_defensible": True}, model=model
            )

    return _S()


def test_wrong_key_rejected() -> None:
    q = _mcq(key="B")
    checks = verify_mcq(q, "units", MISCS, solve=_solver("A").complete_structured, model="mock")
    assert checks["ok"] is False


def test_correct_key_accepted() -> None:
    q = _mcq(key="B")
    checks = verify_mcq(q, "units", MISCS, solve=_solver("B").complete_structured, model="mock")
    assert checks["ok"] is True


def test_two_correct_keys_rejected() -> None:
    q = _mcq(key="B")
    q["options"][3]["is_correct"] = True
    checks = verify_mcq(q, "units", MISCS, solve=_solver("B").complete_structured, model="mock")
    assert checks["ok"] is False


def test_numerical_expression_checked() -> None:
    good = {
        "stem": "Compute 3 squared plus 1.",
        "variables": {"x": 3.0},
        "solution_expression": "x**2 + 1",
        "tolerance_rel": 0.01,
    }
    assert (
        verify_numerical(good, solve=_solver("B").complete_structured, model="mock")["ok"] is True
    )
    bad = dict(good, solution_expression="__import__('os').system('x')")
    assert (
        verify_numerical(bad, solve=_solver("B").complete_structured, model="mock")["ok"] is False
    )


def test_dedup_exact_and_semantic() -> None:
    stem = "What is  P(A|B) ?"
    assert normalize_stem(stem) == "what is p(a|b) ?"
    assert stem_hash(stem) == stem_hash("what is  p(a|b) ?")
    assert dedup.is_duplicate(stem, None, {stem_hash(stem)}, [], threshold=0.88)
    assert not dedup.is_duplicate("other question", None, {stem_hash(stem)}, [], threshold=0.88)
    vec = [1.0, 0.0]
    assert dedup.is_duplicate("near dup", vec, set(), [[1.0, 0.0]], threshold=0.88)
    assert not dedup.is_duplicate("near dup", vec, set(), [[0.0, 1.0]], threshold=0.88)
