"""Response scoring helpers (pure). Grading prompts live in assess/ (Phase 6)."""

from app.domain import expr


def score_mcq(chosen_key: str, answer_key: str) -> float:
    return 1.0 if chosen_key.strip().upper() == answer_key.strip().upper() else 0.0


def score_numerical(
    response_value: float,
    *,
    solution_expression: str,
    variables: dict[str, float],
    tolerance_rel: float,
) -> float:
    expected = expr.evaluate(solution_expression, variables)
    return 1.0 if expr.within_tolerance(response_value, expected, tolerance_rel) else 0.0


def blend_partial(score: float) -> float:
    return min(1.0, max(0.0, score))
