"""Deterministic mock LLM + embedding provider for tests and CI.

Never calls a network API. Returns canned fixtures, including the failure
cases later grounding tests need (unsupported claim, hallucinated unit_id,
wrong answer key, duplicate question). Embeddings are deterministic hash
vectors (EMBED_DIM floats in [-1, 1]).
"""

import hashlib
from typing import Any

from app.db.models import EMBED_DIM
from app.llm.provider import StructuredResult

MOCK_MODEL = "mock-1"

CANNED_REFUSAL = "This isn't covered in your uploaded material."


def hash_embed(text: str, dim: int = EMBED_DIM) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dim:
        block = hashlib.sha256(digest + counter.to_bytes(4, "big")).digest()
        values.extend((b / 255.0) * 2.0 - 1.0 for b in block)
        counter += 1
    return values[:dim]


class MockProvider:
    name = "mock"

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str = MOCK_MODEL,
        timeout_s: float | None = None,
        enable_thinking: bool | None = None,
        system_prompt_prefix: str | None = None,
    ) -> StructuredResult:
        lowered = prompt.lower()
        if "refuse" in lowered or "off-material" in lowered:
            data = {
                "segments": [
                    {
                        "text": CANNED_REFUSAL,
                        "label": "not_covered",
                        "unit_ids": [],
                    }
                ],
                "followup_check_question": None,
            }
        else:
            data = {
                "segments": [
                    {
                        "text": "Mock answer.",
                        "label": "outside_knowledge",
                        "unit_ids": [],
                    }
                ],
                "followup_check_question": None,
            }
        return StructuredResult(data=data, model=model or MOCK_MODEL)

    def vision_describe(self, *, image_path: str, prompt: str, model: str = MOCK_MODEL) -> str:
        return f"Mock figure description for {image_path}."

    def embed(
        self, *, texts: list[str], model: str = MOCK_MODEL, input_type: str = "passage"
    ) -> list[list[float]]:
        return [hash_embed(text) for text in texts]
