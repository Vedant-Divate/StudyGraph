"""Figure descriptions via the vision model, with per-file caching and a cap."""

import hashlib
from typing import Any

from app.llm import cache as llm_cache

FIGURE_PROMPT = (
    "Describe this figure for a student who cannot see it. Respond with a single "
    "JSON object and nothing else: "
    '{"caption": "...", "what_it_shows": "...", "labels": [...], '
    '"relationships": [...], "quantities": [...]}'
)


def file_sha(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_figure(
    image_path: str,
    *,
    vision_model: str,
    vision_call: Any,
    cache_dir: str,
) -> str:
    """Describe one figure; cached by image sha. `vision_call` is injectable for tests."""
    key = llm_cache.cache_key("figure", vision_model, file_sha(image_path))
    cached = llm_cache.read_json(cache_dir, key)
    if cached is not None and isinstance(cached.get("text"), str):
        text = cached["text"]
        assert isinstance(text, str)
        return text
    description = str(vision_call(image_path=image_path, prompt=FIGURE_PROMPT, model=vision_model))
    llm_cache.write_json(cache_dir, key, {"text": description})
    return description
