"""Dedup: exact stem hash + embedding cosine similarity."""

import math

from app.assess.generate import stem_hash


def cosine(a: list[float], b: list[float]) -> float:
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / denom


def is_duplicate(
    stem: str,
    stem_vector: list[float] | None,
    existing_hashes: set[str],
    existing_vectors: list[list[float]],
    *,
    threshold: float = 0.88,
) -> bool:
    if stem_hash(stem) in existing_hashes:
        return True
    if stem_vector:
        for vec in existing_vectors:
            if len(vec) == len(stem_vector) and cosine(stem_vector, vec) >= threshold:
                return True
    return False
