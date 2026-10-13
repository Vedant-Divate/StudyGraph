"""Disk cache for LLM responses keyed by input hash (ingestion/eval reuse)."""

import hashlib
import json
import os
from typing import Any


def cache_key(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def read_json(cache_dir: str, key: str) -> dict[str, Any] | None:
    path = os.path.join(cache_dir, key + ".json")
    try:
        with open(path, encoding="utf-8") as handle:
            data: Any = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_json(cache_dir: str, key: str, payload: dict[str, Any]) -> None:
    os.makedirs(cache_dir, exist_ok=True)
    tmp = os.path.join(cache_dir, key + ".tmp")
    final = os.path.join(cache_dir, key + ".json")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    os.replace(tmp, final)
