"""Tiny-input unit tests for eval/metrics.py (run: pytest eval/test_metrics.py)."""

import metrics


def test_recall_at_k_partial_hit() -> None:
    retrieved = ["u1", "u2", "u3"]
    gold = [{"unit_id": "u2"}, {"unit_id": "u9"}]
    assert metrics.recall_at_k(retrieved, gold, 2) == 0.5
    assert metrics.recall_at_k(retrieved, gold, 1) == 0.0


def test_reciprocal_rank_first_hit_rank_two() -> None:
    retrieved = ["u1", "u2"]
    assert metrics.reciprocal_rank(retrieved, [{"unit_id": "u2"}]) == 0.5
    assert metrics.reciprocal_rank(retrieved, [{"unit_id": "zzz"}]) == 0.0


def test_location_matches_page_slide_and_timestamp() -> None:
    src = "s1"
    assert metrics.location_matches({"source_id": src, "page": 3}, {"source_id": src, "page": 3})
    assert not metrics.location_matches(
        {"source_id": src, "page": 3}, {"source_id": src, "page": 4}
    )
    assert metrics.location_matches({"source_id": src, "slide": 7}, {"source_id": src, "slide": 7})
    gold = {"source_id": src, "t_start_s": 100.0, "t_end_s": 130.0}
    assert metrics.location_matches({"source_id": src, "t_start_s": 115.0}, gold)
    assert metrics.location_matches({"source_id": src, "t_start_s": 85.0}, gold)  # boundary
    assert not metrics.location_matches({"source_id": src, "t_start_s": 116.0}, gold)
    assert not metrics.location_matches({"source_id": "other", "page": 3}, {"source_id": src})


def test_citation_hit_prefers_unit_id_then_location() -> None:
    gold = [{"unit_id": "u5", "source_id": "s", "page": 2}]
    assert metrics.citation_hit([{"unit_id": "u5"}], gold)
    assert metrics.citation_hit([{"source_id": "s", "page": 2}], gold)
    assert not metrics.citation_hit([{"source_id": "s", "page": 9}], gold)


def test_aggregate_retrieval_excludes_goldless_records() -> None:
    records = [
        {"id": "a", "retrieved": ["u1"], "gold_locations": [{"unit_id": "u1"}]},
        {"id": "b", "retrieved": [], "gold_locations": []},
    ]
    out = metrics.aggregate_retrieval(records, k=5)
    assert out["n"] == 1
    assert out["excluded_no_gold"] == 1
    assert out["recall@5"] == 1.0
    assert out["mrr"] == 1.0


def test_refusal_precision_recall_by_type() -> None:
    records = [
        {"id": "1", "type": "unrelated", "must_refuse": True, "predicted_refused": True},
        {"id": "2", "type": "unrelated", "must_refuse": True, "predicted_refused": False},
        {"id": "3", "type": "near_miss", "must_refuse": True, "predicted_refused": True},
        {"id": "4", "type": "in_scope", "must_refuse": False, "predicted_refused": True},
        {"id": "5", "type": "in_scope", "must_refuse": False, "predicted_refused": False},
    ]
    out = metrics.refusal_metrics(records)
    assert (out["tp"], out["fp"], out["fn"]) == (2, 1, 1)
    assert abs(out["precision"] - 2 / 3) < 1e-9
    assert abs(out["recall"] - 2 / 3) < 1e-9
    assert out["recall_by_type"] == {"unrelated": 0.5, "near_miss": 1.0}
