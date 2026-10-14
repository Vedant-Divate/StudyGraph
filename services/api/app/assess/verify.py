"""Question verification: cross-model solve, distractor consistency, evaluator checks."""

import logging
from typing import Any

from app.domain import expr
from app.llm.provider import StructuredResult

logger = logging.getLogger(__name__)

SOLVE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "picked_key": {"type": "string"},
        "exactly_one_defensible": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["picked_key", "exactly_one_defensible"],
}

VALUE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"value": {"type": "number"}, "unsure": {"type": "boolean"}},
    "required": ["value"],
}


def verify_mcq(
    question: dict[str, Any],
    unit_context: str,
    misconception_labels: list[str],
    *,
    solve: Any,
    model: str,
) -> dict[str, Any]:
    """Returns verification_json. ok=True only if all hard checks pass."""
    checks: dict[str, Any] = {"type": "mcq", "model": model}
    options = question.get("options", [])
    correct = [o for o in options if o.get("is_correct") is True]
    checks["exactly_one_correct"] = len(correct) == 1
    if not checks["exactly_one_correct"]:
        checks.update(ok=False)
        return checks
    key = str(correct[0].get("key", "")).strip().upper()

    opt_lines = "\n".join(
        f"{o.get('key')}. {o.get('text')}" for o in options if isinstance(o, dict)
    )
    prompt = (
        "Solve this multiple-choice question using ONLY the excerpts. Reply with the "
        "single correct option key and whether exactly one option is defensible.\n\n"
        f"Q: {question.get('stem', '')}\nOptions:\n{opt_lines}\n\nExcerpts:\n{unit_context}"
    )
    try:
        result: StructuredResult = solve(prompt=prompt, schema=SOLVE_SCHEMA, model=model)
        picked = str(result.data.get("picked_key", "")).strip().upper()
        checks["cross_model_pick"] = picked
        checks["cross_model_agrees"] = picked == key
        checks["exactly_one_defensible"] = bool(result.data.get("exactly_one_defensible"))
    except Exception as exc:  # noqa: BLE001 - solver failure fails verification
        checks["cross_model_agrees"] = False
        checks["solver_error"] = type(exc).__name__

    consistent = True
    for opt in options:
        if opt.get("is_correct") is True:
            continue
        label = str(opt.get("misconception") or "")
        if not opt.get("why_wrong") or (
            label
            and not any(label.lower() in known.lower() for known in misconception_labels)
            and label.lower() not in ("new", "llm_suggested")
        ):
            consistent = False
    checks["distractor_consistency"] = consistent
    checks["ok"] = bool(
        checks["exactly_one_correct"] and checks.get("cross_model_agrees") and consistent
    )
    return checks


def verify_numerical(
    question: dict[str, Any],
    *,
    solve: Any,
    model: str,
    tolerance_rel: float = 0.01,
) -> dict[str, Any]:
    checks: dict[str, Any] = {"type": "numerical", "model": model}
    try:
        variables = {k: float(v) for k, v in (question.get("variables") or {}).items()}
        expected = expr.evaluate(str(question.get("solution_expression", "")), variables)
        checks["expression_evaluates"] = True
        checks["expected"] = expected
    except Exception as exc:  # noqa: BLE001
        checks.update(expression_evaluates=False, error=f"{type(exc).__name__}: {exc}", ok=False)
        return checks
    tol = float(question.get("tolerance_rel", tolerance_rel) or tolerance_rel)
    try:
        prompt = (
            "Compute the numerical answer. Reply with JSON {value, unsure}. "
            f"Q: {question.get('stem', '')}"
        )
        result: StructuredResult = solve(prompt=prompt, schema=VALUE_SCHEMA, model=model)
        value = float(result.data.get("value", float("nan")))
        checks["cross_model_value"] = value
        match = expr.within_tolerance(value, expected, tol)
        checks["cross_model_matches"] = bool(match)
        if not match:
            logger.info("numerical cross-model mismatch: %s vs %s", value, expected)
    except Exception as exc:  # noqa: BLE001 - best effort only
        checks["cross_model_matches"] = None
        checks["solver_error"] = type(exc).__name__
    checks["ok"] = bool(checks["expression_evaluates"])
    return checks
