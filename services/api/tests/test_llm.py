"""LLM helpers tests (mock backends only — no network, no keys)."""

from pathlib import Path

import pytest

from app.llm import cache as llm_cache
from app.llm.mock_provider import MockProvider, hash_embed
from app.llm.ratelimit import backoff_delay, is_retryable_status
from app.llm.structured import SchemaValidationError, extract_json


def test_extract_json_fenced_bare_and_reject() -> None:
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('noise {"a": 1} tail') == {"a": 1}
    with pytest.raises(SchemaValidationError):
        extract_json("no json here")


def test_backoff_and_retryable() -> None:
    assert backoff_delay(0) == 1.0
    assert backoff_delay(1) == 2.0
    assert backoff_delay(100) == 30.0
    assert is_retryable_status(429) and is_retryable_status(503)
    assert not is_retryable_status(400) and not is_retryable_status(None)


def test_cache_round_trip(tmp_path: Path) -> None:
    key = llm_cache.cache_key("a", "b")
    assert llm_cache.read_json(str(tmp_path), key) is None
    llm_cache.write_json(str(tmp_path), key, {"data": {"x": 1}})
    assert llm_cache.read_json(str(tmp_path), key) == {"data": {"x": 1}}


def test_mock_embed_deterministic_and_sized() -> None:
    provider = MockProvider()
    first = provider.embed(texts=["hello world", "other"], model="mock-1")
    second = provider.embed(texts=["hello world"], model="mock-1")
    assert len(first) == 2 and len(first[0]) == 2048
    assert first[0] == second[0]
    assert first[0] != first[1]
    assert hash_embed("x") == hash_embed("x")
