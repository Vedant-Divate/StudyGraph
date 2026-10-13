"""JSON extraction helpers for schema-prompt structured output."""

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class SchemaValidationError(ValueError):
    pass


def extract_json(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of model output (fenced or bare)."""
    stripped = text.strip()
    candidates = [stripped]
    fence = _FENCE_RE.search(stripped)
    if fence:
        candidates.insert(0, fence.group(1).strip())
    # Also try the outermost braces as a last resort.
    start, end = stripped.find("{"), stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            parsed: Any = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise SchemaValidationError("no JSON object found in model output")


def schema_prompt(schema: dict[str, Any]) -> str:
    return (
        "Respond with a single JSON object and nothing else. "
        "It must conform to this JSON schema:\n" + json.dumps(schema)
    )
