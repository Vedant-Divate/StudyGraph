"""Simulated students per PROJECT.md 11.4. LLM-free, seeded, deterministic.

Each simulated student has latent mastery z_c in [0, 1] per concept:

- P(correct) = g + (1 - g - s) * z_eff,
  with z_eff = z_c * (0.6 + 0.4 * mean(z of prerequisites)).
- After answering with feedback: z_c += l_profile * (1 - z_c).
- Between sessions (gap days): z_c *= exp(-gap / S_profile).
- Wrong MCQ answers sample a distractor from a profile-specific preference.

Profiles: strong, average, weak-foundations (low z on root concepts),
forgetful (small S), guesser (high guess/slip). Parameters are fixed a priori
below and documented; they were NOT tuned to favour any policy.

All randomness flows through an explicit random.Random instance so runs are
exactly reproducible from seeds.
"""

from __future__ import annotations

import math
import random
from typing import Any

# Fixed a priori; changing these to favour a policy is forbidden (11.4).
PROFILES: dict[str, dict[str, Any]] = {
    "strong": {
        "z_lo": 0.6, "z_hi": 0.9, "root_lo": None, "root_hi": None,
        "g": 0.10, "s": 0.05, "l": 0.15, "S": 30.0, "gap_days": 7.0,
        "mis_pref": [0.50, 0.30, 0.20],
    },
    "average": {
        "z_lo": 0.3, "z_hi": 0.6, "root_lo": None, "root_hi": None,
        "g": 0.15, "s": 0.10, "l": 0.12, "S": 14.0, "gap_days": 7.0,
        "mis_pref": [0.40, 0.35, 0.25],
    },
    "weak-foundations": {
        "z_lo": 0.2, "z_hi": 0.5, "root_lo": 0.05, "root_hi": 0.25,
        "g": 0.15, "s": 0.10, "l": 0.12, "S": 14.0, "gap_days": 7.0,
        "mis_pref": [0.60, 0.25, 0.15],
    },
    "forgetful": {
        "z_lo": 0.3, "z_hi": 0.6, "root_lo": None, "root_hi": None,
        "g": 0.15, "s": 0.10, "l": 0.12, "S": 3.0, "gap_days": 7.0,
        "mis_pref": [0.40, 0.35, 0.25],
    },
    "guesser": {
        "z_lo": 0.2, "z_hi": 0.5, "root_lo": None, "root_hi": None,
        "g": 0.35, "s": 0.25, "l": 0.08, "S": 14.0, "gap_days": 7.0,
        "mis_pref": [0.34, 0.33, 0.33],
    },
}


def init_student(
    profile: str,
    concept_ids: list[str],
    root_ids: set[str],
    rng: random.Random,
) -> dict[str, Any]:
    """Latent mastery map + profile params for one simulated student."""
    spec = PROFILES[profile]
    z = {}
    for cid in concept_ids:
        if cid in root_ids and spec["root_lo"] is not None:
            lo, hi = spec["root_lo"], spec["root_hi"]
        else:
            lo, hi = spec["z_lo"], spec["z_hi"]
        z[cid] = rng.uniform(lo, hi)
    return {"profile": profile, "z": z, "params": dict(spec)}


def z_effective(z: dict[str, float], concept_id: str, prereq_map: dict[str, list[str]]) -> float:
    prereqs = prereq_map.get(concept_id, [])
    if not prereqs:
        return z[concept_id]
    mean_pre = sum(z[p] for p in prereqs) / len(prereqs)
    return z[concept_id] * (0.6 + 0.4 * mean_pre)


def p_correct(student: dict[str, Any], concept_id: str, prereq_map: dict[str, list[str]]) -> float:
    params = student["params"]
    zeff = z_effective(student["z"], concept_id, prereq_map)
    return params["g"] + (1.0 - params["g"] - params["s"]) * zeff


def respond(
    student: dict[str, Any],
    concept_id: str,
    prereq_map: dict[str, list[str]],
    rng: random.Random,
) -> tuple[bool, int | None]:
    """Sample correctness; on a wrong answer also sample a distractor index."""
    correct = rng.random() < p_correct(student, concept_id, prereq_map)
    if correct:
        return True, None
    pref = student["params"]["mis_pref"]
    roll, acc, pick = rng.random(), 0.0, len(pref) - 1
    for i, weight in enumerate(pref):
        acc += weight
        if roll < acc:
            pick = i
            break
    return False, pick


def learn(student: dict[str, Any], concept_id: str) -> None:
    """Post-feedback latent update: z_c += l * (1 - z_c)."""
    step = student["params"]["l"]
    student["z"][concept_id] += step * (1.0 - student["z"][concept_id])


def forget(student: dict[str, Any], gap_days: float | None = None) -> None:
    """Between-session decay: z_c *= exp(-gap / S)."""
    params = student["params"]
    gap = params["gap_days"] if gap_days is None else gap_days
    factor = math.exp(-gap / params["S"])
    for cid in student["z"]:
        student["z"][cid] *= factor
