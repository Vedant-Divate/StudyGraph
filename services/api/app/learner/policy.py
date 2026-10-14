"""Adaptive selection per PROJECT.md 10.7 (pure functions)."""

import random
from typing import Any


def readiness(m_effs: dict[Any, float], prereqs: list[Any]) -> float:
    if not prereqs:
        return 1.0
    values = [m_effs.get(p, 0.3) for p in prereqs]
    if all(v >= 0.5 for v in values):
        return 1.0
    return 0.5 + 0.5 * min(values)


def difficulty_for(m_eff: float) -> str:
    if m_eff < 0.4:
        return "easy"
    if m_eff < 0.7:
        return "medium"
    return "hard"


def opening_set(concepts: list[dict[str, Any]], *, n: int = 8) -> list[dict[str, Any]]:
    """Cold start: top importance, one per top-level topic first."""
    by_topic: dict[Any, dict[str, Any]] = {}
    rest: list[dict[str, Any]] = []
    for concept in sorted(concepts, key=lambda c: -c["importance"]):
        topic = concept.get("topic_id") or concept["id"]
        if topic not in by_topic:
            by_topic[topic] = concept
        else:
            rest.append(concept)
    ordered = list(by_topic.values()) + sorted(rest, key=lambda c: -c["importance"])
    return ordered[:n]


def choose(
    concepts: list[dict[str, Any]],
    prereq_map: dict[Any, list[Any]],
    m_effs: dict[Any, float],
    *,
    seen_ids: set[Any],
    last_concept_id: Any | None,
    exploration_rate: float = 0.2,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Pick next concept. Returns {concept, reason, difficulty, prereq_first}."""
    rng = rng or random.Random()
    pool = [c for c in concepts if c["id"] not in seen_ids] or list(concepts)
    scored = []
    for concept in pool:
        cid = concept["id"]
        prereqs = prereq_map.get(cid, [])
        score = (1 - m_effs.get(cid, 0.3)) * concept["importance"] * readiness(m_effs, prereqs)
        scored.append((score, concept))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top5 = [c for _, c in scored[:5]]
    if rng.random() < exploration_rate and len(top5) > 1:
        candidates = [c for c in top5 if c["id"] != last_concept_id] or top5
        picked = rng.choice(candidates)
        explored = True
    else:
        picked = next((c for _, c in scored if c["id"] != last_concept_id), scored[0][1])
        explored = False
    # Prerequisite-first rule.
    prereq_first = None
    for pid in prereq_map.get(picked["id"], []):
        if m_effs.get(pid, 1.0) < 0.4:
            prereq_first = pid
            break
    if prereq_first is not None:
        target = next((c for c in concepts if c["id"] == prereq_first), picked)
        reason = (
            f"Weak prerequisite first: {target['name']} is at "
            f"{m_effs.get(target['id'], 0.0):.0%} and {picked['name']} needs it."
        )
        return {
            "concept": target,
            "reason": reason,
            "difficulty": difficulty_for(m_effs.get(target["id"], 0.3)),
            "prereq_first": True,
            "explored": explored,
        }
    meff = m_effs.get(picked["id"], 0.3)
    reason = f"{picked['name']} is at {meff:.0%} mastery (importance {picked['importance']:.2f})."
    return {
        "concept": picked,
        "reason": reason,
        "difficulty": difficulty_for(meff),
        "prereq_first": False,
        "explored": explored,
    }
    reason = (
        f"{picked['name']} is at {picked['m_eff']:.0%} mastery "
        f"(importance {picked['importance']:.2f})."
    )
    return {
        "concept": picked,
        "reason": reason,
        "difficulty": difficulty_for(picked["m_eff"]),
        "prereq_first": False,
        "explored": explored,
    }
