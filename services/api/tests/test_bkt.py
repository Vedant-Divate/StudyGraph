"""BKT unit + property tests (PROJECT.md 10.2-10.4)."""

import random

from app.domain import bkt

G, S, T = 0.2, 0.1, 0.15


def test_correct_raises_mastery() -> None:
    assert bkt.update(0.3, correct=True, guess=G, slip=S, p_learn=T) > 0.3


def test_incorrect_lowers_mastery() -> None:
    assert bkt.update(0.5, correct=False, guess=G, slip=S, p_learn=T) < 0.5


def test_partial_between_full_and_none() -> None:
    full = bkt.update(0.4, correct=True, guess=G, slip=S, p_learn=T)
    none = bkt.update(0.4, correct=False, guess=G, slip=S, p_learn=T)
    mid = bkt.update_partial(0.4, score=0.5, guess=G, slip=S, p_learn=T)
    assert none <= mid <= full


def test_propagation_only_pulls_down_prereqs() -> None:
    before = 0.6
    after = bkt.propagate_incorrect(before, weight=0.8, hop=1, alpha0=0.4, guess=G, slip=S)
    assert after < before
    two_hop = bkt.propagate_incorrect(before, weight=0.8, hop=2, alpha0=0.4, guess=G, slip=S)
    assert two_hop > after  # hop decay: weaker pull


def test_forgetting_bounds_and_direction() -> None:
    assert bkt.decay_stability(3.0, correct=True) > 3.0
    assert bkt.decay_stability(3.0, correct=False) < 3.0
    assert bkt.decay_stability(100.0, correct=True) == 60.0
    assert bkt.decay_stability(1.0, correct=False) == 1.0


def test_effective_mastery_decay_and_floor() -> None:
    assert bkt.effective_mastery(0.8, days_since_seen=0.0, stability_days=3.0) == 0.8
    assert bkt.effective_mastery(0.8, days_since_seen=30.0, stability_days=3.0) >= 0.8 * 0.4


def test_probabilities_stay_in_unit_interval() -> None:
    rng = random.Random(42)
    for _ in range(500):
        p = rng.random()
        g, s = rng.random() * 0.5, rng.random() * 0.3
        assert 0.0 <= bkt.update(p, correct=True, guess=g, slip=s, p_learn=T) <= 1.0
        assert 0.0 <= bkt.update(p, correct=False, guess=g, slip=s, p_learn=T) <= 1.0


def test_monotonicity_in_evidence() -> None:
    for p in (0.1, 0.5, 0.9):
        up = bkt.update(p, correct=True, guess=G, slip=S, p_learn=0.0)
        down = bkt.update(p, correct=False, guess=G, slip=S, p_learn=0.0)
        assert down <= p <= up
