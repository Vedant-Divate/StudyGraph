#!/usr/bin/env python3
"""ONE-SHOT live NIM smoke test. Manual use only — never run in CI.

Makes exactly one tiny call per capability: chat, structured JSON, vision,
verifier-model chat, judge-model chat, embeddings. Prints pass/fail, model and
latency only. The API key is read from .env.local and NEVER printed.

Usage (from repo root):
    uv run --project services/api --frozen python scripts/nim_smoke.py \
        --pdf data/demo-course/MIT6_041SCF13_L01.pdf
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "services", "api"))


def load_dotenv_local() -> None:
    path = os.path.join(REPO_ROOT, ".env.local")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def chat(base: str, api_key: str, model: str, messages: list[dict], **kwargs: object) -> tuple[int, dict]:
    body = {"model": model, "messages": messages, "stream": False, **kwargs}
    started = time.monotonic()
    request = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(body).encode(),
        headers=_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode())
            return int((time.monotonic() - started) * 1000), payload
    except Exception as exc:  # noqa: BLE001 - report, don't crash the harness
        return int((time.monotonic() - started) * 1000), {"_error": f"{type(exc).__name__}"}


def main() -> int:
    if os.environ.get("CI"):
        print("refusing to run under CI")
        return 2
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="slides PDF whose page 1 is the vision input")
    args = parser.parse_args()

    load_dotenv_local()
    base = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    api_key = os.environ.get("NIM_API_KEY", "")
    if not api_key:
        print("NIM_API_KEY missing from environment/.env.local")
        return 2

    chat_model = os.environ.get("LLM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
    vision_model = os.environ.get("VISION_MODEL", "meta/muse-glimmer-30b")
    verifier_model = os.environ.get("VERIFIER_MODEL", "openai/gpt-oss-20b")
    judge_model = os.environ.get("JUDGE_MODEL", "meta/muse-glimmer-30b")
    embed_model = os.environ.get("EMBED_MODEL", "nvidia/nemotron-3-embed-1b")

    results: list[tuple[str, str, bool, int, str]] = []

    def record(name: str, model: str, ok: bool, ms: int, note: str) -> None:
        results.append((name, model, ok, ms, note))
        print(f"[{'PASS' if ok else 'FAIL'}] {name} model={model} {ms}ms {note}")

    # 1. chat
    ms, out = chat(base, api_key, chat_model, [{"role": "user", "content": "Say OK."}])
    text = (out.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    record("chat", chat_model, "_error" not in out and len(text) > 0, ms, f"chars={len(text)}")

    # 2. structured JSON (schema prompt, no forced tools)
    schema_note = (
        'Respond with a single JSON object and nothing else: {"answer": "<9.11 or 9.8>"}'
    )
    ms, out = chat(
        base,
        api_key,
        chat_model,
        [{"role": "user", "content": "Which is larger, 9.11 or 9.8? " + schema_note}],
        temperature=0,
    )
    text = (out.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    try:
        parsed = json.loads(text[text.find("{") : text.rfind("}") + 1])
        ok = isinstance(parsed, dict) and "answer" in parsed
    except (ValueError, IndexError):
        ok = False
    record("structured", chat_model, "_error" not in out and ok, ms, f"chars={len(text)}")

    # 3. vision: render PDF page 1 to PNG, describe it
    import pymupdf  # local import: only needed for the live smoke run

    with tempfile.TemporaryDirectory() as tmp:
        doc = pymupdf.open(args.pdf)
        pix = doc[0].get_pixmap(dpi=72)
        img_path = os.path.join(tmp, "p1.png")
        pix.save(img_path)
        with open(img_path, "rb") as handle:
            b64 = base64.b64encode(handle.read()).decode()
        ms, out = chat(
            base,
            api_key,
            vision_model,
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this slide in one sentence."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ],
                }
            ],
            temperature=0,
            max_tokens=300,
        )
    message = (out.get("choices") or [{}])[0].get("message", {})
    text = message.get("content") or ""
    if len(text) <= 20 and isinstance(message.get("reasoning_content"), str):
        text = message["reasoning_content"]  # glimmer puts analysis here; provider falls back likewise
    record("vision", vision_model, "_error" not in out and len(text) > 20, ms, f"chars={len(text)}")

    # 4. verifier model chat
    ms, out = chat(
        base, api_key, verifier_model, [{"role": "user", "content": "Reply with: VERIFIED"}]
    )
    text = (out.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    record("verifier", verifier_model, "_error" not in out and "VERIFIED" in text, ms, "")

    # 5. judge model chat
    ms, out = chat(
        base, api_key, judge_model, [{"role": "user", "content": "Reply with: JUDGED"}]
    )
    text = (out.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    record("judge", judge_model, "_error" not in out and "JUDGED" in text, ms, "")

    # 6. embeddings
    body = {
        "model": embed_model,
        "input": ["probability sample space", "conditional probability"],
        "input_type": "passage",
        "encoding_format": "float",
        "truncate": "END",
    }
    started = time.monotonic()
    request = urllib.request.Request(
        base + "/embeddings", data=json.dumps(body).encode(), headers=_headers(api_key), method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode())
        vectors = [row["embedding"] for row in payload.get("data", [])]
        ok = len(vectors) == 2 and len({len(v) for v in vectors}) == 1
        dim = len(vectors[0]) if ok else 0
    except Exception:  # noqa: BLE001
        ok, dim = False, 0
    ms = int((time.monotonic() - started) * 1000)
    record("embeddings", embed_model, ok, ms, f"dim={dim}" if ok else "")

    failed = [name for name, _, ok, _, _ in results if not ok]
    print(f"smoke: {len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
