"""Retrieval confidence measures raw cosine while RRF still orders candidates."""

import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from app.config import Settings
from app.kb import retrieval


class _Rows:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


def test_raw_cosine_confidence_and_rrf_order(monkeypatch: Any) -> None:
    ids = [uuid.uuid4() for _ in range(3)]
    units = [
        SimpleNamespace(
            id=uid,
            kind="transcript",
            text=f"unit {index}",
            figure_description=None,
            source_id=uuid.uuid4(),
        )
        for index, uid in enumerate(ids)
    ]
    monkeypatch.setattr(
        retrieval,
        "embed_texts",
        lambda texts, *, settings, input_type: (
            [[1.0, 0.0]] if texts == ["query"] and input_type == "query" else []
        ),
    )
    monkeypatch.setattr(
        retrieval,
        "vector_ranked",
        lambda *_args, **_kwargs: [(ids[0], 0.9), (ids[1], 0.8), (ids[2], 0.7)],
    )
    monkeypatch.setattr(
        retrieval,
        "keyword_ranked",
        lambda *_args, **_kwargs: [(ids[1], 1.0), (ids[2], 0.5), (ids[0], 0.25)],
    )
    monkeypatch.setattr(retrieval, "expand_neighbours", lambda _session, rows: rows)

    class FakeSession:
        def scalars(self, _statement: Any) -> _Rows:
            return _Rows(units)

    rows, confidence, mean_top3 = retrieval.retrieve(
        FakeSession(),
        course_id=uuid.uuid4(),
        query="query",
        settings=Settings(retrieval_top_k=6),
    )

    assert [row["unit_id"] for row in rows] == [ids[1], ids[0], ids[2]]
    assert confidence == 0.9
    assert mean_top3 == pytest.approx(0.8)
    assert len(rows) <= 6
