"""Embeddings: NIM-hosted model or deterministic hash (tests)."""

from app.config import Settings, get_settings
from app.db.models import EMBED_DIM
from app.llm.factory import get_embedder
from app.llm.mock_provider import hash_embed


def embed_texts(
    texts: list[str],
    *,
    settings: Settings | None = None,
    input_type: str = "passage",
) -> list[list[float]]:
    settings = settings or get_settings()
    if not texts:
        return []
    if settings.embed_backend == "nim":
        provider = get_embedder(settings)
        vectors = provider.embed(texts=texts, model=settings.embed_model, input_type=input_type)
        if any(len(v) != EMBED_DIM for v in vectors):
            raise ValueError("embedding dimension mismatch")
        return vectors
    return [hash_embed(text) for text in texts]
