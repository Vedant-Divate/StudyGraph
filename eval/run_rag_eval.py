"""RAG eval runner: calls the real chat route, computes custom metrics.

Modes:

- ``--retrieval-only`` (default if the API is unreachable): LLM-free local
  retrieval baseline. Rebuilds the transcript (+figure) unit corpus from the
  same read-only artifacts the DB rows were built from, embeds with the same
  deterministic hash vectors as ``EMBED_BACKEND=hash``, fuses vector cosine
  with a token-overlap keyword score via RRF (mirroring
  ``app.kb.retrieval``; Postgres full-text and neighbour expansion are NOT
  replicated — see caveats), and scores recall@k / MRR on gold locations.
  Needs no LLM, no API server, no DB.
- ``--db-retrieval``: REAL retrieval baseline. Runs the server's own
  ``app.kb.retrieval.retrieve`` (vector cosine over stored DB embeddings +
  Postgres full-text + RRF + neighbour expansion) against Neon with
  ``EMBED_BACKEND=nim`` for query embeddings. Retrieval only, no chat LLM.
  Reads ``DATABASE_URL``/``NIM_API_KEY`` from ``.env.local`` (never printed).
  DB access is SELECT-only; sessions are rolled back, never committed.
- full (default): POSTs each test-set question to the real chat route
  ``POST /api/courses/{course_id}/chat`` with a per-request timeout, derives
  ``predicted_refused`` (all segments ``not_covered``) and citations, and
  computes refusal + citation-accuracy metrics. Retrieval rankings are NOT
  exposed by the chat route, so retrieval metrics reuse the local-retrieval
  function and are labelled ``local_proxy`` in the output.

Output: ``eval/results/rag_eval.json`` (configurable via ``--out``).

Never prints secrets. Model IDs are read from the local environment (same
defaults as app.config) and recorded as client-reported, not server-proven.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "services" / "api"))

import metrics  # noqa: E402
from app.ingestion.video import merge_windows, parse_srt  # noqa: E402
from app.kb.retrieval import cosine, reciprocal_rank_fusion  # noqa: E402
from app.llm.mock_provider import hash_embed  # noqa: E402

NAMESPACE = "a4301776-1a6a-49ec-b265-27717d3c7634"

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _stable(kind: str, key: str) -> str:
    import uuid

    return str(uuid.uuid5(uuid.UUID(NAMESPACE), f"{kind}:{key}"))


def load_corpus() -> list[dict[str, Any]]:
    """Rebuild the 190-unit corpus (178 transcript + 12 figure) read-only."""
    units: list[dict[str, Any]] = []
    for lecture in (1, 2):
        base = REPO / "data" / "demo-course"
        windows = merge_windows(parse_srt(str(base / f"lec{lecture:02d}.srt")))
        source_id = _stable("source", f"lecture-{lecture:02d}")
        for index, (start, end, text) in enumerate(windows):
            units.append(
                {
                    "unit_id": _stable("transcript", f"{lecture}:{index}:{start:.3f}:{end:.3f}"),
                    "source_id": source_id,
                    "t_start_s": start,
                    "t_end_s": end,
                    "text": text,
                }
            )
    frames = json.loads((REPO / "data" / "demo-course" / "thumb_desc.json").read_text())
    for index, frame in enumerate(frames):
        lecture = int(str(frame["lec"]))
        timestamp = float(frame["t"])
        source_id = _stable("source", f"lecture-{lecture:02d}")
        units.append(
            {
                "unit_id": _stable("figure", f"{lecture}:{timestamp:.3f}:{index}"),
                "source_id": source_id,
                "t_start_s": timestamp,
                "t_end_s": timestamp,
                "text": f"Video frame at {timestamp:.0f}s. {frame.get('desc', '')}",
            }
        )
    return units


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def document_frequencies(units: list[dict[str, Any]]) -> dict[str, int]:
    """Number of corpus units containing each token (for IDF-style weighting)."""
    freq: dict[str, int] = {}
    for unit in units:
        for tok in _tokens(unit["text"]):
            freq[tok] = freq.get(tok, 0) + 1
    return freq


def keyword_ranked(
    query: str, units: list[dict[str, Any]], doc_freq: dict[str, int]
) -> list[tuple[str, float]]:
    """IDF-weighted token-overlap ranking (local stand-in for ts_rank)."""
    qtok = _tokens(query)
    weights = {tok: 1.0 / (1 + doc_freq.get(tok, 0)) for tok in qtok}
    norm = sum(weights.values()) or 1.0
    keyed: list[tuple[str, float]] = []
    for unit in units:
        score = sum(weights[tok] for tok in (qtok & _tokens(unit["text"]))) / norm
        if score > 0:
            keyed.append((unit["unit_id"], score))
    keyed.sort(key=lambda pair: pair[1], reverse=True)
    return keyed


def keyword_retrieve(
    query: str, units: list[dict[str, Any]], doc_freq: dict[str, int], top_k: int = 6
) -> list[dict[str, Any]]:
    """Keyword-only ranking, recorded as a diagnostic alongside the RRF mirror."""
    by_id = {u["unit_id"]: u for u in units}
    return [by_id[uid] for uid, _ in keyword_ranked(query, units, doc_freq)[:top_k] if uid in by_id]


def local_retrieve(
    query: str,
    units: list[dict[str, Any]],
    vectors: list[list[float]],
    top_k: int = 6,
    doc_freq: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """RRF fusion of hash-cosine ranking and IDF-weighted keyword ranking (LLM-free).

    The keyword side weights query tokens by 1/(1+document-frequency), mirroring
    how Postgres ``ts_rank`` down-weights common terms; it is a local stand-in,
    not the server ranker.
    """
    qvec = hash_embed(query)
    vec_ranked = sorted(
        [(u["unit_id"], cosine(qvec, v)) for u, v in zip(units, vectors)],
        key=lambda pair: pair[1],
        reverse=True,
    )[:20]
    if doc_freq is None:
        doc_freq = document_frequencies(units)
    keyed = keyword_ranked(query, units, doc_freq)[:20]
    fused = reciprocal_rank_fusion(
        [vec_ranked, [(uid, s) for uid, s in keyed]],
    )
    by_id = {u["unit_id"]: u for u in units}
    return [by_id[uid] for uid, _ in fused[:top_k] if uid in by_id]


def post_chat(base_url: str, course_id: str, question: str, timeout_s: float) -> dict[str, Any]:
    payload = json.dumps({"message": question, "allow_outside": False}).encode()
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/courses/{course_id}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = json.loads(response.read().decode())
        return {"ok": True, "body": body, "latency_s": round(time.time() - started, 3)}
    except Exception as exc:  # noqa: BLE001 - record transport failures per item
        return {"ok": False, "error": type(exc).__name__, "latency_s": round(time.time() - started, 3)}


def chat_to_record(item: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": item["id"],
        "type": item["type"],
        "question": item["question"],
        "must_refuse": item["must_refuse"],
        "gold_locations": item["gold_locations"],
        "chat_ok": result["ok"],
        "latency_s": result.get("latency_s"),
    }
    if not result["ok"]:
        record.update({"predicted_refused": None, "citations": [], "error": result.get("error")})
        return record
    segments = result["body"].get("segments", [])
    labels = [s.get("label") for s in segments if isinstance(s, dict)]
    record["predicted_refused"] = bool(segments) and all(label == "not_covered" for label in labels)
    record["labels"] = labels
    record["answer_texts"] = [str(s.get("text", ""))[:600] for s in segments if isinstance(s, dict)]
    record["gold_answer"] = item.get("gold_answer", "")
    citations: list[dict[str, Any]] = []
    for seg in segments:
        for citation in (seg.get("citations", []) or []):
            if isinstance(citation, dict) and citation.get("unit_id"):
                citations.append({"unit_id": str(citation["unit_id"])})
    record["citations"] = citations
    record["confidence"] = result["body"].get("confidence")
    return record


def load_dotlocal_env() -> None:
    """Load DATABASE_URL/NIM_API_KEY from repo .env.local into env (never logged)."""
    dotlocal = REPO / ".env.local"
    if not dotlocal.is_file():
        return
    for line in dotlocal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key in ("DATABASE_URL", "NIM_API_KEY") and key not in os.environ:
            os.environ[key] = value


def db_retrieve_all(
    items: list[dict[str, Any]], course_id: str, timeout_note: str = ""
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run server retrieval per item against Neon (SELECT-only). Returns records + info."""
    import uuid

    from app.config import get_settings
    from app.db import models
    from app.db.session import make_session_factory
    from app.kb import retrieval as kb_retrieval

    settings = get_settings()
    settings.embed_backend = "nim"
    settings.llm_provider = "mock"  # retrieval only; no chat LLM in this mode
    _ = timeout_note
    factory = make_session_factory()
    probe = factory()
    try:
        course = probe.get(models.Course, uuid.UUID(course_id))
        assert course is not None, f"course {course_id} not found in DB"
    finally:
        probe.rollback()
        probe.close()
    records: list[dict[str, Any]] = []
    for item in items:
        session = factory()
        started = time.time()
        try:
            units, confidence, mean_top3 = kb_retrieval.retrieve(
                session, course_id=uuid.UUID(course_id), query=item["question"], settings=settings
            )
            records.append(
                {
                    "id": item["id"],
                    "type": item["type"],
                    "question": item["question"],
                    "must_refuse": item["must_refuse"],
                    "gold_locations": item["gold_locations"],
                    "retrieved": [str(u["unit_id"]) for u in units],
                    "confidence": confidence,
                    "mean_top3_similarity": mean_top3,
                    "latency_s": round(time.time() - started, 3),
                }
            )
        except Exception as exc:  # noqa: BLE001 - record per-item failures honestly
            records.append(
                {
                    "id": item["id"],
                    "type": item["type"],
                    "question": item["question"],
                    "must_refuse": item["must_refuse"],
                    "gold_locations": item["gold_locations"],
                    "retrieved": [],
                    "error": type(exc).__name__,
                    "latency_s": round(time.time() - started, 3),
                }
            )
        finally:
            session.rollback()
            session.close()
    info = {
        "course_id": course_id,
        "embed_backend": "nim",
        "retrieval": "server app.kb.retrieval.retrieve (vector + ts_rank + RRF + neighbours)",
        "db_access": "SELECT-only; sessions rolled back, never committed",
    }
    return records, info


def load_testset(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    header, items = rows[0], rows[1:]
    assert header.get("header") is True, "testset first line must be the header record"
    return header, items


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RAG eval (custom metrics).")
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--db-retrieval", action="store_true")
    parser.add_argument("--testset", default=str(REPO / "eval" / "testset" / "rag.jsonl"))
    parser.add_argument("--out", default=str(REPO / "eval" / "results" / "rag_eval.json"))
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--course-id", default=os.environ.get("EVAL_COURSE_ID", ""))
    parser.add_argument("--timeout-s", type=float, default=150.0)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    header, items = load_testset(Path(args.testset))
    if args.limit:
        items = items[args.offset : args.offset + args.limit]
    elif args.offset:
        items = items[args.offset :]
    digest = hashlib.sha256(Path(args.testset).read_bytes()).hexdigest()[:16]

    db_info: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    mode = ""
    if args.db_retrieval:
        import uuid as uuid_mod

        load_dotlocal_env()
        default_course = str(
            uuid_mod.uuid5(uuid_mod.UUID(NAMESPACE), "mit-ocw-6.041sc-fall-2013")
        )
        records, db_info = db_retrieve_all(items, args.course_id or default_course)
        mode = "db-retrieval"
        corpus = []
    else:
        corpus = load_corpus()
    vectors = [hash_embed(u["text"]) for u in corpus]
    doc_freq = document_frequencies(corpus)

    if mode == "db-retrieval":
        pass
    elif args.retrieval_only:
        for item in items:
            ranked = local_retrieve(item["question"], corpus, vectors, doc_freq=doc_freq)
            kwonly = keyword_retrieve(item["question"], corpus, doc_freq)
            records.append(
                {
                    "id": item["id"],
                    "type": item["type"],
                    "question": item["question"],
                    "must_refuse": item["must_refuse"],
                    "gold_locations": item["gold_locations"],
                    "retrieved": [u["unit_id"] for u in ranked],
                    "retrieved_kwonly": [u["unit_id"] for u in kwonly],
                }
            )
        mode = "retrieval-only"
    else:
        if not args.course_id:
            raise SystemExit("full mode needs --course-id (or EVAL_COURSE_ID)")
        for item in items:
            result = post_chat(args.base_url, args.course_id, item["question"], args.timeout_s)
            record = chat_to_record(item, result)
            ranked = local_retrieve(item["question"], corpus, vectors, doc_freq=doc_freq)
            kwonly = keyword_retrieve(item["question"], corpus, doc_freq)
            # Chat route exposes no retrieval ranking; local proxy, clearly labelled.
            record["retrieved"] = [u["unit_id"] for u in ranked]
            record["retrieved_kwonly"] = [u["unit_id"] for u in kwonly]
            record["retrieval_is_local_proxy"] = True
            records.append(record)
        mode = "full"

    if mode == "db-retrieval":
        db_info["summary"] = metrics.aggregate_retrieval(records, k=args.k)
        summary = {
            "retrieval": db_info.pop("summary"),
            "retrieval_backend": db_info,
        }
    else:
        kwonly_records = [
            {**r, "retrieved": r.get("retrieved_kwonly", r.get("retrieved", []))}
            for r in records
        ]
        summary = {
            "retrieval": metrics.aggregate_retrieval(records, k=args.k),
            "retrieval_kwonly_diagnostic": metrics.aggregate_retrieval(kwonly_records, k=args.k),
            "retrieval_note": (
                "Local-corpus proxy: 190 units rebuilt read-only from SRT/thumb "
                "artifacts, hash embeddings, RRF(cosine, token-overlap). Server "
                "Postgres full-text and neighbour expansion NOT replicated."
            ),
        }
    if mode == "full":
        summary["citation"] = metrics.citation_accuracy(records)
        summary["refusal"] = metrics.refusal_metrics(records)

    output = {
        "mode": mode,
        "created_utc": datetime.now(UTC).isoformat(),
        "testset_sha16": digest,
        "testset_header_status": header.get("status", ""),
        "n_items": len(records),
        "k": args.k,
        "timeout_s": args.timeout_s,
        "model_ids_client_reported": {
            "llm_model": os.environ.get("LLM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
            "verifier_model": os.environ.get("VERIFIER_MODEL", "openai/gpt-oss-20b"),
            "judge_model": os.environ.get("JUDGE_MODEL", "meta/muse-glimmer-30b"),
            "embed_backend": "nim" if mode == "db-retrieval" else os.environ.get("EMBED_BACKEND", "hash"),
            "embed_model": os.environ.get("EMBED_MODEL", "nvidia/nemotron-3-embed-1b"),
        },
        "model_ids_caveat": (
            "Client-environment values, not server-proven. "
            "NIM key used from the environment for API calls; never printed or stored."
        ),
        "corpus": (
            {"n_units": 190, "source": "Neon PostgreSQL (SELECT-only read of stored rows)"}
            if mode == "db-retrieval"
            else {"n_units": len(corpus), "source": "read-only SRT/thumb artifacts"}
        ),
        "summary": summary,
        "records": records,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"mode": mode, "n": len(records), "out": str(out_path), "summary": summary},
            ensure_ascii=False,
            indent=2,
        )[:2000]
    )


if __name__ == "__main__":
    main()
