"""Custom RAG metrics per PROJECT.md 11.3. Pure python, LLM-free, no I/O.

Conventions (shared with eval/run_rag_eval.py and eval/testset/rag.jsonl):

- A gold location is a dict with ``source_id`` plus one of ``page``,
  ``slide``, or (``t_start_s``, ``t_end_s``). Test-set locations also carry
  ``unit_id`` and a human-readable ``source`` label; both are ignored here
  except ``unit_id``, which is the primary retrieval-match key.
- A retrieved entry is either a unit-id string or a dict with ``unit_id``
  and/or location fields.
- A citation is a dict with ``unit_id`` and/or location fields, as resolved
  server-side from ``unit_id`` (PROJECT.md rule 8).
- An eval record is a dict with ``id``, ``type``, ``must_refuse`` (bool),
  ``predicted_refused`` (bool), ``retrieved`` (ranked list), ``citations``
  (list), and ``gold_locations`` (list).

Aggregation rules:

- Retrieval (recall@k, MRR) is averaged only over records with non-empty
  ``gold_locations``. Refusal items have no answerable location, so they are
  excluded (reported as ``excluded_no_gold``) rather than scored zero.
- Citation accuracy is the fraction of gold-bearing records with at least one
  citation overlapping a gold location (page/slide equal on the same source;
  timestamp start within +-15 s).
- Refusal precision/recall use ``must_refuse`` as ground truth and
  ``predicted_refused`` as the prediction; recall is additionally broken down
  by off-material ``type`` (unrelated / near_miss / false_premise).
"""

from __future__ import annotations

from typing import Any

TIMESTAMP_TOLERANCE_S = 15.0


def _unit_key(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        value = entry.get("unit_id")
        return str(value) if value is not None else None
    return None


def location_matches(pred: dict[str, Any], gold: dict[str, Any], tol_s: float = 15.0) -> bool:
    """True when a predicted location overlaps a gold location (11.3)."""
    if not isinstance(pred, dict) or not isinstance(gold, dict):
        return False
    if str(pred.get("source_id", "")) != str(gold.get("source_id", "")):
        return False
    if pred.get("page") is not None and gold.get("page") is not None:
        return bool(pred["page"] == gold["page"])
    if pred.get("slide") is not None and gold.get("slide") is not None:
        return bool(pred["slide"] == gold["slide"])
    pred_t = pred.get("t_start_s")
    gold_t = gold.get("t_start_s")
    if pred_t is not None and gold_t is not None:
        return abs(float(pred_t) - float(gold_t)) <= tol_s
    return False


def _retrieval_hit(retrieved: Any, gold: dict[str, Any]) -> bool:
    key = _unit_key(retrieved)
    if key is not None and key == str(gold.get("unit_id", "")):
        return True
    if isinstance(retrieved, dict):
        return location_matches(retrieved, gold)
    return False


def recall_at_k(retrieved: list[Any], gold_locations: list[dict[str, Any]], k: int) -> float:
    """Fraction of gold locations found in the top-k retrieved entries."""
    if not gold_locations or k <= 0:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for gold in gold_locations if any(_retrieval_hit(r, gold) for r in top))
    return hits / len(gold_locations)


def reciprocal_rank(retrieved: list[Any], gold_locations: list[dict[str, Any]]) -> float:
    """1/rank of the first retrieved entry matching any gold location (0 if none)."""
    if not gold_locations:
        return 0.0
    for rank, entry in enumerate(retrieved, start=1):
        if any(_retrieval_hit(entry, gold) for gold in gold_locations):
            return 1.0 / rank
    return 0.0


def aggregate_retrieval(records: list[dict[str, Any]], k: int = 5) -> dict[str, Any]:
    """Mean recall@k and MRR over gold-bearing records (LLM-free, CI-safe)."""
    recalls: list[float] = []
    mrrs: list[float] = []
    excluded = 0
    for record in records:
        gold = [g for g in record.get("gold_locations", []) if isinstance(g, dict)]
        if not gold:
            excluded += 1
            continue
        retrieved = record.get("retrieved", [])
        recalls.append(recall_at_k(retrieved, gold, k))
        mrrs.append(reciprocal_rank(retrieved, gold))
    n = len(recalls)
    return {
        "k": k,
        "n": n,
        "excluded_no_gold": excluded,
        f"recall@{k}": sum(recalls) / n if n else 0.0,
        "mrr": sum(mrrs) / n if n else 0.0,
    }


def citation_hit(
    citations: list[Any],
    gold_locations: list[dict[str, Any]],
    tol_s: float = TIMESTAMP_TOLERANCE_S,
) -> bool:
    """True when at least one citation overlaps a gold location (11.3)."""
    for citation in citations:
        key = _unit_key(citation)
        for gold in gold_locations:
            if key is not None and key == str(gold.get("unit_id", "")):
                return True
            if isinstance(citation, dict) and location_matches(citation, gold, tol_s):
                return True
    return False


def citation_accuracy(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Fraction of gold-bearing records with at least one overlapping citation."""
    hits = 0
    n = 0
    for record in records:
        gold = [g for g in record.get("gold_locations", []) if isinstance(g, dict)]
        if not gold:
            continue
        n += 1
        if citation_hit(record.get("citations", []), gold):
            hits += 1
    return {"n": n, "accuracy": hits / n if n else 0.0}


def refusal_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Refusal precision/recall overall, plus recall by off-material type."""
    tp = fp = fn = 0
    by_type: dict[str, dict[str, int]] = {}
    for record in records:
        must = bool(record.get("must_refuse", False))
        predicted = bool(record.get("predicted_refused", False))
        if must and predicted:
            tp += 1
        elif must and not predicted:
            fn += 1
        elif not must and predicted:
            fp += 1
        if must:
            slot = by_type.setdefault(str(record.get("type", "unknown")), {"tp": 0, "fn": 0})
            slot["tp" if predicted else "fn"] += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    recall_by_type = {}
    for name, counts in by_type.items():
        total = counts["tp"] + counts["fn"]
        recall_by_type[name] = counts["tp"] / total if total else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "recall_by_type": recall_by_type,
        "counts_by_type": by_type,
    }
