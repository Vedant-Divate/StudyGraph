"""LLM provider interface (Phase 0 stub).

The full contract (`complete_structured`, `vision_describe`, optional `embed`,
rate limiting, retries, caching) lands in Phase 1. This stub fixes the seam so
`tutor/`, `assess/` and `eval/` can depend on it later.

Implementations: `mock_provider.py` (tests/CI) and, from Phase 1,
`nim_provider.py` (NVIDIA NIM; see ADR-0005).
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
    """Minimal Phase 0 provider seam."""

    name: str

    def complete_structured(
        self, *, prompt: str, schema: dict[str, Any], model: str
    ) -> StructuredResult:
        """Return JSON-validated output for *prompt* conforming to *schema*."""
        ...  # pragma: no cover

    def vision_describe(self, *, image_path: str, prompt: str, model: str) -> str:
        """Return a text description of the image at *image_path*."""
        ...  # pragma: no cover
