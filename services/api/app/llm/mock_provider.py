"""Deterministic mock LLM provider for tests and CI.

Never calls a network API. Returns canned fixtures, including the failure
cases the later grounding tests need (unsupported claim, hallucinated unit_id,
wrong answer key, duplicate question).
"""

from typing import Any

from app.llm.provider import StructuredResult

MOCK_MODEL = "mock-1"

CANNED_REFUSAL = "This isn't covered in your uploaded material."


class MockProvider:
    name = "mock"

    def complete_structured(
        self, *, prompt: str, schema: dict[str, Any], model: str = MOCK_MODEL
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
