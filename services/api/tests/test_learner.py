"""Learner tests: BKT bounds, 2-hop propagation, policy rules (no DB)."""

import random

from app.learner import model, policy


def _concepts():
    return [
        {"id": "root", "name": "Sample Space", "importance": 1.0, "topic_id": "t1"},
        {"id": "mid", "name": "Events", "importance": 0.8, "topic_id": "t1"},
        {"id": "leaf", "name": "Bayes", "importance": 0.9, "topic_id": "t2"},
        {"id": "far", "name": "Counting", "importance": 0.5, "topic_id": "t2"},
    ]


def _edges():
    return [("root", "mid", 0.9), ("mid", "leaf", 0.8), ("root", "leaf", 0.4)]


def test_bkt_stays_in_unit_interval() -> None:
    rng = random.Random(7)
    for _ in range(300):
        p = rng.random()
        correct = rng.random() < 0.5
        p_new, stab = model.update_mastery(
            p, 3.0, correct=correct, qtype="mcq", difficulty="medium", num_options=4
        )
        assert 0.0 <= p_new <= 1.0
        assert 1.0 <= stab <= 60.0


def test_propagation_limited_to_2_hops() -> None:
    edges = [("a", "b", 0.9), ("b", "c", 0.9), ("x", "a", 0.9)]
    pmap = {"a": 0.6, "b": 0.6, "c": 0.6, "x": 0.6}
    out = model.propagate_incorrect(pmap, edges, "c")
    assert out["b"] < 0.6 and out["a"] < 0.6  # 1-2 hops move
    assert out["x"] == 0.6  # 3 hops away: untouched
    assert out["c"] == 0.6  # target itself untouched by propagation


def test_prerequisite_first_selection() -> None:
    concepts = [
        {"id": "root", "name": "Sample Space", "importance": 0.5, "topic_id": "t1"},
        {"id": "leaf", "name": "Bayes", "importance": 1.0, "topic_id": "t1"},
    ]
    meffs = {"root": 0.3, "leaf": 0.4}
    pick = policy.choose(
        concepts,
        {"leaf": ["root"]},
        meffs,
        seen_ids=set(),
        last_concept_id=None,
        exploration_rate=0.0,
        rng=random.Random(0),
    )
    assert pick["prereq_first"] is True
    assert pick["concept"]["id"] == "root"


def test_no_back_to_back_repeat() -> None:
    concepts = _concepts()
    meffs = {c["id"]: 0.5 for c in concepts}
    last = None
    for _ in range(10):
        pick = policy.choose(
            concepts,
            {},
            meffs,
            seen_ids=set(),
            last_concept_id=last,
            exploration_rate=0.0,
            rng=random.Random(1),
        )
        assert pick["concept"]["id"] != last
        last = pick["concept"]["id"]


def test_opening_set_covers_topics_first() -> None:
    chosen = policy.opening_set(_concepts(), n=2)
    topics = {c["topic_id"] for c in chosen}
    assert topics == {"t1", "t2"}


def test_difficulty_bands() -> None:
    assert policy.difficulty_for(0.2) == "easy"
    assert policy.difficulty_for(0.5) == "medium"
    assert policy.difficulty_for(0.9) == "hard"


def test_cold_prior_clip() -> None:
    assert model.cold_prior([]) == 0.3
    assert 0.1 <= model.cold_prior([0.9, 0.9]) <= 0.6
