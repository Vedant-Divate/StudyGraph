"""NVIDIA NIM provider (OpenAI-compatible endpoint; see ADR-0005).

Structured output = schema prompt + validate + one retry (no forced tool use is
assumed). Reasoning deltas (`reasoning_content`) are ignored — only the final
message content is used. Keys and image bytes are never logged.
"""

import base64
import logging
import mimetypes
import time
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app.config import get_settings
from app.llm import cache as llm_cache
from app.llm.provider import StructuredResult
from app.llm.ratelimit import RateLimiter, backoff_delay, is_retryable_status
from app.llm.structured import SchemaValidationError, extract_json, schema_prompt

logger = logging.getLogger(__name__)

_RETRYABLE = (APIConnectionError, APITimeoutError)


def _status_of(exc: BaseException) -> int | None:
    if isinstance(exc, APIStatusError):
        return exc.status_code
    return None


class NIMProvider:
    name = "nim"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.nim_api_key:
            raise ValueError("NIM_API_KEY is not set")
        self._client = OpenAI(
            base_url=settings.nim_base_url,
            api_key=settings.nim_api_key,
            timeout=settings.llm_timeout_s,
            max_retries=0,  # retries handled here for full control
        )
        self._limiter = RateLimiter(rpm=settings.llm_rpm, concurrency=settings.llm_concurrency)
        self._cache_dir = settings.llm_cache_dir

    def _call_with_backoff(self, label: str, func: Any, **kwargs: Any) -> Any:
        self._limiter.acquire()
        try:
            attempts = 0
            while True:
                try:
                    return func(**kwargs)
                except APIStatusError as exc:
                    if is_retryable_status(exc.status_code) and attempts < 2:
                        delay = backoff_delay(attempts)
                        logger.warning(
                            "%s: HTTP %s, retrying in %.1fs", label, exc.status_code, delay
                        )
                        time.sleep(delay)
                        attempts += 1
                        continue
                    raise
                except _RETRYABLE as exc:
                    if attempts < 2:
                        delay = backoff_delay(attempts)
                        logger.warning(
                            "%s: %s, retrying in %.1fs", label, type(exc).__name__, delay
                        )
                        time.sleep(delay)
                        attempts += 1
                        continue
                    raise
        finally:
            self._limiter.release()

    def complete_structured(
        self, *, prompt: str, schema: dict[str, Any], model: str
    ) -> StructuredResult:
        key = llm_cache.cache_key("structured", model, prompt, str(sorted(schema.items())))
        cached = llm_cache.read_json(self._cache_dir, key)
        if cached is not None and isinstance(cached.get("data"), dict):
            data = cached["data"]
            assert isinstance(data, dict)
            return StructuredResult(data=data, model=model, attempts=0, cached=True)

        system = schema_prompt(schema)
        attempts = 0
        last_error = ""
        current_user = prompt
        while attempts < 2:
            attempts += 1
            response = self._call_with_backoff(
                "complete_structured",
                self._client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": current_user},
                ],
                temperature=0,
                top_p=1,
                stream=False,
            )
            content = (response.choices[0].message.content or "").strip()
            try:
                data = extract_json(content)
            except SchemaValidationError as exc:
                last_error = str(exc)
                current_user = (
                    f"{prompt}\n\nYour previous output failed validation "
                    f"({last_error}). Respond with a single JSON object only."
                )
                continue
            llm_cache.write_json(self._cache_dir, key, {"data": data, "model": model})
            return StructuredResult(data=data, model=model, attempts=attempts)
        raise SchemaValidationError(f"structured output failed twice: {last_error}")

    def vision_describe(self, *, image_path: str, prompt: str, model: str) -> str:
        key = llm_cache.cache_key("vision", model, prompt, image_path)
        cached = llm_cache.read_json(self._cache_dir, key)
        if cached is not None and isinstance(cached.get("text"), str):
            text = cached["text"]
            assert isinstance(text, str)
            return text
        with open(image_path, "rb") as handle:
            raw = handle.read()
        mime, _ = mimetypes.guess_type(image_path)
        data_url = f"data:{mime or 'image/png'};base64,{base64.b64encode(raw).decode()}"
        response = self._call_with_backoff(
            "vision_describe",
            self._client.chat.completions.create,
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0,
            stream=False,
        )
        text_out = (response.choices[0].message.content or "").strip()
        if not text_out:
            # Reasoning-first models (e.g. muse-glimmer) may put the whole
            # analysis in reasoning_content with content=null; fall back to it.
            reasoning = getattr(response.choices[0].message, "reasoning_content", None)
            if isinstance(reasoning, str) and reasoning.strip():
                text_out = reasoning.strip()
        llm_cache.write_json(self._cache_dir, key, {"text": text_out})
        return text_out

    def embed(self, *, texts: list[str], model: str) -> list[list[float]]:
        if not texts:
            return []
        key = llm_cache.cache_key("embed", model, *texts)
        cached = llm_cache.read_json(self._cache_dir, key)
        if cached is not None and isinstance(cached.get("vectors"), list):
            vectors = cached["vectors"]
            assert isinstance(vectors, list)
            return vectors
        response = self._call_with_backoff(
            "embed",
            self._client.embeddings.create,
            model=model,
            input=texts,
            extra_body={"input_type": "passage", "encoding_format": "float", "truncate": "END"},
        )
        vectors_out = [list(item.embedding) for item in response.data]
        llm_cache.write_json(self._cache_dir, key, {"vectors": vectors_out})
        return vectors_out
