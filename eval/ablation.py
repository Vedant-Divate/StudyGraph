"""Policy ablation on simulated students (PROJECT.md 11.4). LLM-free, seeded.

Protocol: 30 students per profile x 5 profiles x 5 sessions of 10 questions,
fixed seeds, real verified bank snapshot (eval/simulation/bank_snapshot.json).
Policies random / sequential (lecture-flow course order) / adaptive (the real
app/learner/policy.choose over the estimator's beliefs) run on identical
students (same latent inits; response streams are per-policy but seeded).

Estimator: the real learner model (app/learner/model.update_mastery +
propagate_incorrect on wrong answers) tracks p_mastery from simulated
responses; MAE vs true z is reported by session.

Reported with 95% bootstrap CIs (2000 resamples over students): mean true
mastery gain (all concepts + held-out), estimator MAE by session,
weak-targeting precision (share of asks on concepts with true z < 0.6),
question repetition rate, and at least one failure case where adaptive does
not win. Labelled "simulated, not real learners" in the report.

Nothing here is tuned to favour the adaptive policy: profile params are fixed
in simulator.py, the estimator is the production BKT (which mismatches the
guesser profile on purpose-blindness: same code as production), and held-out
concepts follow a fixed rule.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

import simulator  # noqa: E402
from app.learner import model as learner_model  # noqa: E402
from app.learner import policy as learner_policy  # noqa: E402

N_STUDENTS = 30
N_SESSIONS = 5
N_PER_SESSION = 10
BOOTSTRAP_REPS = 2000
MASTER_SEED = 20261014
WEAK_THRESHOLD = 0.6


def load_snapshot() -> dict[str, Any]:
    path = REPO / "eval" / "simulation" / "bank_snapshot.json"
    return json.loads(path.read_text(encoding="utf-8"))


def bootstrap_ci(values: list[float], reps: int = BOOTSTRAP_REPS) -> tuple[float, float, float]:
    rng = random.Random(MASTER_SEED + 7919)
    n = len(values)
    means = [
        statistics.fmean(values[rng.randrange(n)] for _ in range(n)) for _ in range(reps)
    ]
    means.sort()
    return (
        statistics.fmean(values),
        means[int(0.025 * reps)],
        means[int(0.975 * reps) - 1],
    )


class World:
    """Bank + graph + policy pools derived from the snapshot."""

    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.concepts = snapshot["concepts"]
        self.by_id = {c["id"]: c for c in self.concepts}
        self.prereq_map: dict[str, list[str]] = {c["id"]: [] for c in self.concepts}
        for pre, con, _w in snapshot["edges"]:
            if con in self.prereq_map and pre in self.by_id:
                self.prereq_map[con].append(pre)
        self.edge_tuples = [
            (pre, con, w) for pre, con, w in snapshot["edges"]
            if pre in self.by_id and con in self.by_id
        ]
        self.held_out: set[str] = set(snapshot["held_out"])
        self.questions = [q for q in snapshot["questions"] if q["concept_id"]]
        self.by_concept: dict[str, list[dict[str, Any]]] = {}
        for q in self.questions:
            self.by_concept.setdefault(q["concept_id"], []).append(q)
        for qs in self.by_concept.values():
            qs.sort(key=lambda q: q["id"])
        self.askable = sorted(
            [cid for cid in self.by_concept if cid not in self.held_out],
            key=lambda cid: self.by_id[cid]["course_order"],
        )
        self.roots = {cid for cid in self.by_id if not self.prereq_map[cid]}
        self.all_ids = [c["id"] for c in self.concepts]

    def pick_question(
        self, concept_id: str, difficulty: str, asked: set[str], rng: random.Random
    ) -> tuple[dict[str, Any], bool]:
        pool = self.by_concept[concept_id]
        unseen = [q for q in pool if q["id"] not in asked]
        matching = [q for q in unseen if q["difficulty"] == difficulty]
        if matching:
            return matching[0], False
        if unseen:
            return unseen[0], False
        return rng.choice(pool), True  # repetition: bank exhausted for concept


def run_student_policy(
    world: World, profile: str, student_idx: int, policy_name: str
) -> dict[str, Any]:
    rng_init = random.Random(MASTER_SEED + 1000 * _profile_index(profile) + student_idx)
    student = simulator.init_student(profile, world.all_ids, world.roots, rng_init)
    rng = random.Random(MASTER_SEED + 100000 * _profile_index(profile)
                        + 1000 * student_idx + _policy_index(policy_name))
    estimator_p = {cid: 0.3 for cid in world.all_ids}
    estimator_s = {cid: 3.0 for cid in world.all_ids}
    asked_qids: set[str] = set()
    asked_concepts: set[str] = set()
    concept_list = [
        {"id": c["id"], "importance": c["importance"], "topic_id": c["topic_id"],
         "name": c["name"]}
        for c in world.concepts
    ]
    # Eval-pool masking: held-out and question-less concepts are invisible to
    # selection (as if absent), but stay in the estimator and prereq maps.
    # Scoring is otherwise identical to production.
    askable_list = [c for c in concept_list if c["id"] in set(world.askable)]
    fallbacks = 0
    seq_pos = 0
    last_concept: str | None = None
    z_start = dict(student["z"])
    asks = 0
    weak_hits = 0
    repetitions = 0
    distractor_counts = [0, 0, 0]
    mae_by_session: list[float] = []

    for _session in range(N_SESSIONS):
        for _ in range(N_PER_SESSION):
            if policy_name == "random":
                cid = rng.choice(world.askable)
                difficulty = "medium"
            elif policy_name == "sequential":
                cid = world.askable[seq_pos % len(world.askable)]
                seq_pos += 1
                difficulty = "medium"
            else:
                m_effs = dict(estimator_p)
                choice = learner_policy.choose(
                    askable_list, world.prereq_map, m_effs,
                    seen_ids=set(asked_concepts), last_concept_id=last_concept,
                    exploration_rate=0.2, rng=rng,
                )
                cid = choice["concept"]["id"]
                if cid not in world.by_concept or cid in world.held_out:
                    # Should not happen under pool masking; counted, not hidden.
                    fallbacks += 1
                    cid = world.askable[0]
                difficulty = choice["difficulty"]
            question, repeated = world.pick_question(cid, difficulty, asked_qids, rng)
            asked_qids.add(question["id"])
            asked_concepts.add(cid)
            last_concept = cid
            asks += 1
            if student["z"][cid] < WEAK_THRESHOLD:
                weak_hits += 1
            repetitions += 1 if repeated else 0
            correct, distractor = simulator.respond(student, cid, world.prereq_map, rng)
            if distractor is not None:
                distractor_counts[distractor] += 1
            simulator.learn(student, cid)
            p_new, s_new = learner_model.update_mastery(
                estimator_p[cid], estimator_s[cid], correct=correct,
                qtype=question["type"], difficulty=question["difficulty"],
                num_options=question["num_options"],
            )
            estimator_p[cid], estimator_s[cid] = p_new, s_new
            if not correct:
                estimator_p = learner_model.propagate_incorrect(
                    estimator_p, world.edge_tuples, cid
                )
        mae_by_session.append(
            statistics.fmean(abs(estimator_p[c] - student["z"][c]) for c in world.all_ids)
        )
        simulator.forget(student)
    z_end = student["z"]
    gain_all = statistics.fmean(z_end[c] - z_start[c] for c in world.all_ids)
    held = [c for c in world.held_out]
    gain_held = statistics.fmean(z_end[c] - z_start[c] for c in held)
    return {
        "gain_all": gain_all,
        "gain_held": gain_held,
        "mae_by_session": mae_by_session,
        "weak_precision": weak_hits / asks if asks else 0.0,
        "repetition_rate": repetitions / asks if asks else 0.0,
        "distractors": distractor_counts,
        "fallbacks": fallbacks,
    }


def _profile_index(profile: str) -> int:
    return list(simulator.PROFILES).index(profile)


def _policy_index(policy: str) -> int:
    return ["random", "sequential", "adaptive"].index(policy)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the policy ablation.")
    parser.add_argument("--out", default=str(REPO / "eval" / "results" / "ablation.json"))
    parser.add_argument("--profiles", default=",".join(simulator.PROFILES))
    parser.add_argument("--students", type=int, default=N_STUDENTS)
    args = parser.parse_args()

    snapshot = load_snapshot()
    world = World(snapshot)
    profiles = args.profiles.split(",")
    policies = ["random", "sequential", "adaptive"]
    per_student: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for profile in profiles:
        per_student[profile] = {}
        for policy_name in policies:
            runs = [
                run_student_policy(world, profile, i, policy_name)
                for i in range(args.students)
            ]
            per_student[profile][policy_name] = runs
    # Determinism self-check: re-run one cell exactly.
    repeat = run_student_policy(world, profiles[0], 0, "adaptive")
    first = per_student[profiles[0]]["adaptive"][0]
    deterministic = repeat == first

    report: dict[str, Any] = {
        "label": "Simulated students — not real learners",
        "seeds": {"master": MASTER_SEED, "students_per_profile": args.students,
                  "sessions": N_SESSIONS, "per_session": N_PER_SESSION,
                  "bootstrap_reps": BOOTSTRAP_REPS},
        "assumptions": {
            "response_model": "P(correct) = g + (1-g-s)*z_eff, z_eff with prereq mean",
            "learning": "z += l*(1-z) after every ask (feedback assumed)",
            "forgetting": "z *= exp(-gap/S), gap 7 days between sessions",
            "held_out": snapshot["held_out"],
            "held_out_rule": snapshot["held_out_rule"],
            "policies_share_identical_inits": True,
            "estimator": "production BKT update_mastery + propagate_incorrect",
        },
        "deterministic_rerun_equal": deterministic,
        "profiles": {},
    }
    for profile in profiles:
        cell = {}
        for policy_name in policies:
            runs = per_student[profile][policy_name]
            gains = [r["gain_all"] for r in runs]
            gains_h = [r["gain_held"] for r in runs]
            weak = [r["weak_precision"] for r in runs]
            rep = [r["repetition_rate"] for r in runs]
            mae_sessions = [
                [r["mae_by_session"][s] for r in runs] for s in range(N_SESSIONS)
            ]
            cell[policy_name] = {
                "gain_all_ci": bootstrap_ci(gains),
                "gain_held_ci": bootstrap_ci(gains_h),
                "weak_precision_ci": bootstrap_ci(weak),
                "repetition_ci": bootstrap_ci(rep),
                "mae_by_session_ci": [bootstrap_ci(m) for m in mae_sessions],
            }
        report["profiles"][profile] = cell
    # Failure cases: profiles where adaptive gain_all mean <= best baseline mean.
    failures = []
    for profile in profiles:
        means = {p: report["profiles"][profile][p]["gain_all_ci"][0] for p in policies}
        best_base = max(means["random"], means["sequential"])
        if means["adaptive"] <= best_base:
            failures.append({
                "profile": profile,
                "adaptive_mean": means["adaptive"],
                "best_baseline_mean": best_base,
            })
    report["failure_cases_adaptive_not_winning_gain"] = failures
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"deterministic={deterministic} out={out_path}")
    for profile in profiles:
        means = {p: report["profiles"][profile][p]["gain_all_ci"][0] for p in policies}
        print(f"{profile}: gain " + ", ".join(f"{p}={means[p]:.4f}" for p in policies)
              + f" | failures={len(failures)}")


if __name__ == "__main__":
    main()
