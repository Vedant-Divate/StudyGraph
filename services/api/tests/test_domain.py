"""Restricted evaluator + citation + scoring tests."""

import uuid

import pytest

from app.domain import citation, expr, scoring
from app.domain.types import Location


def test_expr_accepts_whitelist() -> None:
    assert expr.evaluate("x**2 + 1", {"x": 3.0}) == 10.0
    assert expr.evaluate("sqrt(16) + sin(0) + pi") > 4.0
    assert expr.evaluate("-3 + 2 * (4 - 1)") == 3.0
    assert expr.check_solution("x**2 + 1", {"x": 3.0}, 10.0, 0.01)


def test_expr_rejects_everything_else() -> None:
    for bad in (
        "__import__('os')",
        "open('f').read()",
        "x.attr",
        "eval('1')",
        "lambda: 1",
        "[1, 2]",
        "True",
        "os.system('x')",
        "pow(2, 3)",
        "2 >> 1",
    ):
        with pytest.raises(expr.UnsafeExpression):
            expr.evaluate(bad, {"x": 1.0})


def test_expr_tolerance_edges() -> None:
    assert expr.within_tolerance(100.0, 100.0, 0.0)
    assert not expr.within_tolerance(101.0, 100.0, 0.0)
    assert expr.within_tolerance(101.0, 100.0, 0.01)


def _loc(**kwargs: object) -> Location:
    return Location(source_id=uuid.uuid4(), **kwargs)  # type: ignore[arg-type]


def test_citation_page_slide_video() -> None:
    page = _loc(page=12)
    assert citation.display_string(page, "Textbook") == "Textbook · p. 12"
    assert citation.deep_link(page).endswith("?page=12")

    slide = _loc(slide=18)
    assert citation.display_string(slide, "Lecture 2") == "Lecture 2 · slide 18"
    assert citation.deep_link(slide).endswith("?slide=18")

    video = _loc(t_start_s=872.0, t_end_s=900.0)
    assert citation.display_string(video, "Lecture 2") == "Lecture 2 · 14:32"
    assert citation.deep_link(video).endswith("?t=872")


def test_citation_rejects_ambiguous_location() -> None:
    with pytest.raises(ValueError):
        citation.display_string(_loc(), "X")
    with pytest.raises(ValueError):
        citation.display_string(_loc(page=1, slide=2), "X")


def test_scoring() -> None:
    assert scoring.score_mcq("b", "B") == 1.0
    assert scoring.score_mcq("A", "B") == 0.0
    assert (
        scoring.score_numerical(
            10.0,
            solution_expression="x**2 + 1",
            variables={"x": 3.0},
            tolerance_rel=0.01,
        )
        == 1.0
    )
