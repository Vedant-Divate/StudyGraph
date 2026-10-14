"""RAGAS-style LLM-judge metrics, custom implementation (NOT RAGAS results).

Why custom: the RAGAS library is not in the API dependencies (adding it would
touch files outside this sprint's scope), and it needs live judge calls plus a
running API/DB. So the four framework metrics from PROJECT.md 11.2 —
faithfulness, answer relevancy, context precision, context recall — are
implemented here as small NIM-judge prompts. Every output field, doc and log
line labels them "ragas_style_custom" / "RAGAS-style, custom implementation".
Never present these numbers as RAGAS library results.

Usage (manual, needs secrets; never in CI):

    uv run --frozen python ../../eval/judge_ragas_style.py \
        --results ../../eval/results/rag_eval.json --dry-run      # prompts only
    uv run --frozen python ../../eval/judge_ragas_style.py \
        --results ../../eval/results/rag_eval.json                # live NIM judge

Judge model: --judge-model (default openai/gpt-oss-20b, the fastest measured
non-generator model that returns parseable structured JSON; see below).
Latency evidence: ADR-0005 measured verifier openai/gpt-oss-20b ~5.4 s per
structured call vs judge meta/muse-glimmer-30b ~20-30 s; on 2026-10-14 a
13-item glimmer pilot returned unparseable (non-JSON) output on ~90% of calls
(recorded, discarded). The repo-configured JUDGE_MODEL is unchanged (config
change out of scope); this script flag only affects the eval run. The NIM key
is read from the environment only and never printed or stored.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "services" / "api"))

IMPLEMENTATION = "RAGAS-style, custom implementation (NOT the RAGAS library)"

PROMPTS: dict[str, str] = {
    "faithfulness": (
        "You judge whether an ANSWER is faithful to the given CONTEXTS. List each "
        "factual claim in the answer, then mark it supported/not-supported by the "
        "contexts. Reply ONLY as JSON {\"score\": <fraction of claims supported, "
        "0.0-1.0>, \"reason\": \"<one line>\"}."
    ),
    "answer_relevancy": (
        "You judge whether an ANSWER addresses the QUESTION. Reply ONLY as JSON "
        "{\"score\": <0.0 irrelevant, 0.5 partial, 1.0 directly answers>, "
        "\"reason\": \"<one line>\"}."
    ),
    "context_precision": (
        "You judge the retrieved CONTEXTS for a QUESTION. Reply ONLY as JSON "
        "{\"score\": <fraction of contexts that are useful for answering, 0.0-1.0>, "
        "\"reason\": \"<one line>\"}."
    ),
    "context_recall": (
        "You judge whether the retrieved CONTEXTS cover the GOLD answer's key points "
        "for a QUESTION. Reply ONLY as JSON {\"score\": <fraction of key points "
        "covered, 0.0-1.0>, \"reason\": \"<one line>\"}."
    ),
}


def build_user_prompt(
    metric: str, question: str, answer: str, contexts: list[str], gold: str
) -> str:
    parts = [f"QUESTION: {question}", f"ANSWER: {answer}"]
    if metric in ("faithfulness", "context_precision", "context_recall"):
        joined = "\n---\n".join(contexts[:6])[:4000]
        parts.append(f"CONTEXTS:\n{joined}")
    if metric == "context_recall":
        parts.append(f"GOLD: {gold[:1000]}")
    return "\n\n".join(parts)


def _extract_score(text: str) -> dict[str, Any] | None:
    """Parse {"score", "reason"} from possibly chatty output; None if impossible."""
    import re as re_mod

    try:
        data = json.loads(text[text.index("{") : text.rindex("}") + 1])
        return {"score": min(1.0, max(0.0, float(data.get("score", 0.0)))),
                "reason": str(data.get("reason", ""))[:300]}
    except (ValueError, KeyError):
        fallback = re_mod.search(
            r'"?score"?\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)', text, re_mod.IGNORECASE
        )
        if fallback:
            return {
                "score": min(1.0, max(0.0, float(fallback.group(1)))),
                "reason": "regex-extracted; " + text[:200],
            }
        return None


def judge_call(
    system: str, user: str, model: str, base_url: str, api_key: str, timeout_s: float
) -> dict[str, Any]:
    """NIM judge with one schema-correction retry; {"score","reason"} or {"error"}."""
    from openai import OpenAI

    started = time.time()
    if "gpt-oss" in model:
        system = "Reasoning: low.\n\n" + system
    try:
        client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout_s)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=600,
        )
        message = completion.choices[0].message
        text = (message.content or "").strip()
        if not text:
            # Reasoning-first models may put analysis in reasoning_content.
            reasoning = getattr(message, "reasoning_content", None)
            if isinstance(reasoning, str) and reasoning.strip():
                text = reasoning.strip()
        parsed = _extract_score(text)
        if parsed is not None:
            parsed["latency_s"] = round(time.time() - started, 3)
            return parsed
        return {
            "error": "unparseable_judge_output",
            "latency_s": round(time.time() - started, 3),
            "output_head": text[:200],
        }
    except Exception as exc:  # noqa: BLE001 - record judge failures per item
        return {"error": type(exc).__name__, "latency_s": round(time.time() - started, 3)}


def main() -> None:
    parser = argparse.ArgumentParser(description="RAGAS-style custom judge (manual).")
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", default="")
    parser.add_argument("--judge-model", default="openai/gpt-oss-20b")
    parser.add_argument("--timeout-s", type=float, default=90.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    payload = json.loads(Path(args.results).read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if args.limit:
        records = records[args.offset : args.offset + args.limit]
    elif args.offset:
        records = records[args.offset :]

    dotlocal = REPO / ".env.local"
    if dotlocal.is_file():
        for line in dotlocal.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key in ("NIM_BASE_URL", "NIM_API_KEY") and key not in os.environ:
                    os.environ[key] = value
    base_url = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    api_key = os.environ.get("NIM_API_KEY", "")
    if not args.dry_run and not api_key:
        raise SystemExit("live judge needs NIM_API_KEY in the environment")

    # Contexts are rebuilt read-only from the same artifacts (no DB).
    sys.path.insert(0, str(REPO / "services" / "api"))
    import run_rag_eval as runner

    corpus = {u["unit_id"]: u for u in runner.load_corpus()}

    judged: list[dict[str, Any]] = []
    for record in records:
        if not record.get("chat_ok") or record.get("predicted_refused"):
            continue  # judge metrics apply to answered items only
        contexts = [
            corpus[uid]["text"][:800] for uid in record.get("retrieved", []) if uid in corpus
        ]
        answer = " ".join(record.get("answer_texts", []))[:1500]
        entry: dict[str, Any] = {"id": record["id"], "type": record.get("type")}
        for metric, system in PROMPTS.items():
            user = build_user_prompt(
                metric,
                record.get("question", ""),
                answer,
                contexts,
                record.get("gold_answer", ""),
            )
            if args.dry_run:
                entry[metric] = {"system": system, "user_chars": len(user)}
            else:
                entry[metric] = judge_call(
                    system, user, args.judge_model, base_url, api_key, args.timeout_s
                )
            entry[metric]["implementation"] = "ragas_style_custom"
        judged.append(entry)

    summary: dict[str, Any] = {"implementation": IMPLEMENTATION, "n_judged": len(judged)}
    if judged and not args.dry_run:
        for metric in PROMPTS:
            scores = [e[metric].get("score") for e in judged if "score" in e[metric]]
            errors = sum(1 for e in judged if "error" in e[metric])
            by_type: dict[str, list[float]] = {}
            for entry in judged:
                if "score" in entry[metric]:
                    by_type.setdefault(str(entry.get("type")), []).append(entry[metric]["score"])
            summary[metric] = {
                "mean": statistics.fmean(scores) if scores else None,
                "stdev": statistics.pstdev(scores) if len(scores) > 1 else None,
                "n": len(scores),
                "n_errors": errors,
                "mean_by_type": {t: statistics.fmean(v) for t, v in by_type.items()},
            }
        latencies = [
            m.get("latency_s", 0.0)
            for e in judged
            for m in (e[metric] for metric in PROMPTS)
            if "latency_s" in m
        ]
        summary["judge_model"] = args.judge_model
        summary["mean_judge_latency_s"] = statistics.fmean(latencies) if latencies else 0.0

    output = {
        "implementation": IMPLEMENTATION,
        "judge_model": args.judge_model,
        "dry_run": args.dry_run,
        "summary": summary,
        "records": judged,
    }
    out_path = Path(args.out) if args.out else Path(args.results).with_name("rag_judge.json")
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"implementation={IMPLEMENTATION}")
    print(f"judged={len(judged)} dry_run={args.dry_run} out={out_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:1500])


if __name__ == "__main__":
    main()
