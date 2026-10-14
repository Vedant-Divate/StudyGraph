"""Tiny-input checks for the simulator formulas and determinism."""

import math
import random

import simulator


def test_p_correct_formula() -> None:
    student = {"z": {"a": 0.8, "p1": 0.5, "p2": 0.5},
               "params": {"g": 0.1, "s": 0.05, "l": 0.15, "S": 30.0,
                          "gap_days": 7.0, "mis_pref": [0.5, 0.3, 0.2]}}
    assert simulator.z_effective(student["z"], "a", {}) == 0.8
    zeff = simulator.z_effective(student["z"], "a", {"a": ["p1", "p2"]})
    assert abs(zeff - 0.8 * (0.6 + 0.4 * 0.5)) < 1e-9
    assert abs(simulator.p_correct(student, "a", {"a": ["p1", "p2"]})
               - (0.1 + 0.85 * zeff)) < 1e-9


def test_learn_and_forget() -> None:
    student = {"z": {"a": 0.5}, "params": {"g": 0.1, "s": 0.05, "l": 0.2,
                                           "S": 10.0, "gap_days": 7.0,
                                           "mis_pref": [0.5, 0.3, 0.2]}}
    simulator.learn(student, "a")
    assert abs(student["z"]["a"] - 0.6) < 1e-9
    simulator.forget(student)
    assert abs(student["z"]["a"] - 0.6 * math.exp(-0.7)) < 1e-9


def test_init_and_respond_deterministic() -> None:
    cids = ["c1", "c2"]
    first = simulator.init_student("average", cids, set(), random.Random(7))
    second = simulator.init_student("average", cids, set(), random.Random(7))
    assert first == second
    assert all(0.3 <= v <= 0.6 for v in first["z"].values())
    weak = simulator.init_student("weak-foundations", cids, {"c1"}, random.Random(7))
    assert weak["z"]["c1"] < 0.3
    outcomes = [simulator.respond(first, "c1", {}, random.Random(i)) for i in range(3)]
    assert outcomes == [simulator.respond(first, "c1", {}, random.Random(i)) for i in range(3)]
    assert all(isinstance(ok, bool) for ok, _ in outcomes)
