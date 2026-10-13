"""Chunk page text into ~200-400 token units, never crossing page boundaries."""

import re

MIN_TOKENS = 200
MAX_TOKENS = 400


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text.strip())]
    return [p for p in parts if p]


def chunk_page_text(text: str) -> list[str]:
    """Greedily pack paragraphs into MAX_TOKENS windows (min MIN_TOKENS)."""
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for para in split_paragraphs(text):
        tokens = estimate_tokens(para)
        if current and current_tokens + tokens > MAX_TOKENS:
            chunks.append("\n\n".join(current))
            current, current_tokens = [], 0
        current.append(para)
        current_tokens += tokens
    if current:
        chunks.append("\n\n".join(current))
    if len(chunks) > 1 and estimate_tokens(chunks[-1]) < MIN_TOKENS // 2:
        chunks[-2] = chunks[-2] + "\n\n" + chunks[-1]
        chunks.pop()
    return [c for c in chunks if c.strip()]
