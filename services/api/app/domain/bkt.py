"""Bayesian Knowledge Tracing with prerequisite propagation and forgetting.

Pure math, per PROJECT.md Section 10. Tunable constants live in config, not here.
"""

import math

MIN_STABILITY_DAYS = 1.0
MAX_STABILITY_DAYS = 60.0


def _clip01(x: float) -> float:
    return min(1.0, max(0.0, x))


def posterior_correct(p: float, guess: float, slip: float) -> float:
    denom = p * (1.0 - slip) + (1.0 - p) * guess
    if denom <= 0.0:
        return p
    return _clip01(p * (1.0 - slip) / denom)


def posterior_incorrect(p: float, guess: float, slip: float) -> float:
    denom = p * slip + (1.0 - p) * (1.0 - guess)
    if denom <= 0.0:
        return p
    return _clip01(p * slip / denom)


def learn_step(p: float, p_learn: float) -> float:
    return _clip01(p + (1.0 - p) * p_learn)


def update(p: float, *, correct: bool, guess: float, slip: float, p_learn: float) -> float:
    if correct:
        post = posterior_correct(p, guess, slip)
    else:
        post = posterior_incorrect(p, guess, slip)
    return learn_step(post, p_learn)


def update_partial(p: float, *, score: float, guess: float, slip: float, p_learn: float) -> float:
    """Short-answer partial credit sigma: blend full-credit and no-credit paths."""
    sigma = _clip01(score)
    full = update(p, correct=True, guess=guess, slip=slip, p_learn=p_learn)
    none = update(p, correct=False, guess=guess, slip=slip, p_learn=p_learn)
    return _clip01(sigma * full + (1.0 - sigma) * none)


def propagate_incorrect(
    prereq_p: float,
    *,
    weight: float,
    hop: int,
    alpha0: float,
    guess: float,
    slip: float,
) -> float:
    """Pull a prerequisite down on an incorrect response (no learning step)."""
    if hop < 1:
        raise ValueError("hop must be >= 1")
    alpha = _clip01(alpha0 * weight * 0.5 ** (hop - 1))
    down = posterior_incorrect(prereq_p, guess, slip)
    return _clip01((1.0 - alpha) * prereq_p + alpha * down)


def decay_stability(stability_days: float, *, correct: bool) -> float:
    factor = 1.6 if correct else 0.6
    return min(MAX_STABILITY_DAYS, max(MIN_STABILITY_DAYS, stability_days * factor))


def effective_mastery(p: float, *, days_since_seen: float, stability_days: float) -> float:
    if stability_days <= 0.0:
        return _clip01(p)
    floor = 0.4
    return _clip01(p * max(floor, math.exp(-days_since_seen / stability_days)))


def mastery_band(m_eff: float) -> str:
    if m_eff < 0.4:
        return "weak"
    if m_eff < 0.7:
        return "developing"
    return "strong"
