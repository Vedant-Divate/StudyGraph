"""LLM provider interface (Phase 1 full contract).

Implementations: `mock_provider.py` (tests/CI) and `nim_provider.py`
(NVIDIA NIM; see ADR-0005). Callers never touch HTTP, keys, or image bytes.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class StructuredResult:
    """Validated structured output plus the model identity that produced it."""

    data: dict[str, Any]
    model: str
    attempts: int = 1
    cached: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str,
        timeout_s: float | None = None,
        enable_thinking: bool | None = None,
        system_prompt_prefix: str | None = None,
    ) -> StructuredResult:
        """Return JSON output for *prompt* conforming to *schema* (validated)."""
        ...

    def vision_describe(self, *, image_path: str, prompt: str, model: str) -> str:
        """Return a text description of the image at *image_path*."""
        ...


class EmbeddingProvider(Protocol):
    name: str

    def embed(
        self, *, texts: list[str], model: str, input_type: str = "passage"
    ) -> list[list[float]]:
        """Return one vector per input text, in order."""
        ...
