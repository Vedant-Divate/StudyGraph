"""Learner-model updates over plain state dicts (PROJECT.md 10.2-10.6).

State per concept: {"p": float, "stability": float, "seen": bool}.
Pure functions — the API layer loads/saves mastery_states rows.
"""

from typing import Any

from app.domain import bkt

SLIP_BY_DIFFICULTY = {"easy": 0.05, "medium": 0.10, "hard": 0.20}


def guess_for(qtype: str, num_options: int = 4) -> float:
    if qtype == "mcq":
        return 1.0 / max(2, num_options)
    if qtype == "numerical":
        return 0.03
    return 0.10


def update_mastery(
    p: float,
    stability: float,
    *,
    correct: bool,
    qtype: str,
    difficulty: str,
    num_options: int = 4,
    p_learn: float = 0.15,
) -> tuple[float, float]:
    guess = guess_for(qtype, num_options)
    slip = SLIP_BY_DIFFICULTY.get(difficulty, 0.10)
    p_new = bkt.update(p, correct=correct, guess=guess, slip=slip, p_learn=p_learn)
    return p_new, bkt.decay_stability(stability, correct=correct)


def prereqs_within_2hops(
    edges: list[tuple[Any, Any, float]], target: Any
) -> dict[Any, tuple[float, int]]:
    """BFS over (prerequisite -> concept, weight). Returns {pid: (weight, hop)}."""
    found: dict[Any, tuple[float, int]] = {}
    frontier: list[tuple[Any, float, int]] = [(pre, w, 1) for pre, con, w in edges if con == target]
    while frontier:
        pid, weight, hop = frontier.pop(0)
        if pid in found or hop > 2:
            continue
        found[pid] = (weight, hop)
        if hop < 2:
            frontier.extend((pre, w, hop + 1) for pre, con, w in edges if con == pid)
    return found


def propagate_incorrect(
    p_map: dict[Any, float],
    edges: list[tuple[Any, Any, float]],
    target: Any,
    *,
    alpha0: float = 0.4,
    guess: float = 0.2,
    slip: float = 0.1,
) -> dict[Any, float]:
    """Incorrect-response propagation, limited to 2 hops. Returns updated map."""
    out = dict(p_map)
    for pid, (weight, hop) in prereqs_within_2hops(edges, target).items():
        if pid in out:
            out[pid] = bkt.propagate_incorrect(
                out[pid], weight=weight, hop=hop, alpha0=alpha0, guess=guess, slip=slip
            )
    return out


def cold_prior(prereq_ps: list[float]) -> float:
    if not prereq_ps:
        return 0.3
    return min(0.6, max(0.1, 0.3 + 0.5 * (sum(prereq_ps) / len(prereq_ps) - 0.3)))
