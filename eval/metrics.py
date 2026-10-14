"""Thin re-export of the canonical metrics in services/api/app/eval/metrics.py.

The canonical implementation lives in the API package so CI and the API can
import it as ``app.eval.metrics``; this shim lets repo-root scripts use the
same code as ``eval.metrics`` without duplication.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from app.eval.metrics import (  # noqa: F401,E402
    TIMESTAMP_TOLERANCE_S,
    aggregate_retrieval,
    citation_accuracy,
    citation_hit,
    location_matches,
    reciprocal_rank,
    recall_at_k,
    refusal_metrics,
)
