"""Provider factory: mock vs NIM, chosen by config. Tests always use mock."""

from app.config import Settings, get_settings
from app.llm.mock_provider import MockProvider
from app.llm.nim_provider import NIMProvider


def get_llm(settings: Settings | None = None) -> MockProvider | NIMProvider:
    settings = settings or get_settings()
    if settings.llm_provider == "nim":
        return NIMProvider()
    return MockProvider()


def get_embedder(settings: Settings | None = None) -> MockProvider | NIMProvider:
    settings = settings or get_settings()
    if settings.embed_backend == "nim":
        return NIMProvider()
    return MockProvider()
