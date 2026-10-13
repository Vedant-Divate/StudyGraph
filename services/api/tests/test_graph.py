"""Graph validity tests: no cycles survive, edges need valid endpoints."""

import uuid

from app.kb.graph import is_acyclic, remove_cycles, resolve_edge_ids

CID = {name: uuid.uuid4() for name in ("a", "b", "c")}


def _concepts() -> list:
    return [
        {"id": CID[name], "name": name, "summary": "", "level": "concept"}
        for name in ("a", "b", "c")
    ]


def test_resolve_drops_unknown_and_self_edges() -> None:
    edges = [
        {"prerequisite": "a", "concept": "b", "weight": 0.8},
        {"prerequisite": "nope", "concept": "b", "weight": 0.5},
        {"prerequisite": "a", "concept": "a", "weight": 0.9},
    ]
    resolved = resolve_edge_ids(edges, _concepts())
    assert len(resolved) == 1
    assert resolved[0]["prerequisite_id"] == CID["a"]


def test_cycle_removal_drops_weakest() -> None:
    edges = [
        {"prerequisite_id": CID["a"], "concept_id": CID["b"], "weight": 0.9},
        {"prerequisite_id": CID["b"], "concept_id": CID["c"], "weight": 0.8},
        {"prerequisite_id": CID["c"], "concept_id": CID["a"], "weight": 0.3},
    ]
    assert not is_acyclic(edges)
    clean = remove_cycles(edges)
    assert is_acyclic(clean) and len(clean) == 2
    assert all(
        not (e["prerequisite_id"] == CID["c"] and e["concept_id"] == CID["a"]) for e in clean
    )


def test_dag_passes_through() -> None:
    edges = [
        {"prerequisite_id": CID["a"], "concept_id": CID["b"], "weight": 0.9},
        {"prerequisite_id": CID["b"], "concept_id": CID["c"], "weight": 0.8},
    ]
    assert is_acyclic(edges)
    assert remove_cycles(edges) == edges
