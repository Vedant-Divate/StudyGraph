"""Grounded question generation (MCQ priority, numericals second). No short-answer."""

import hashlib
from typing import Any

from app.llm.provider import StructuredResult

MCQ_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "stem": {"type": "string"},
        "difficulty": {"type": "string"},
        "options": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "text": {"type": "string"},
                    "is_correct": {"type": "boolean"},
                    "misconception": {"type": "string"},
                    "why_wrong": {"type": "string"},
                },
                "required": ["key", "text", "is_correct"],
            },
        },
        "explanation": {"type": "string"},
    },
    "required": ["stem", "options", "explanation"],
}

NUMERICAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "stem": {"type": "string"},
        "difficulty": {"type": "string"},
        "variables": {"type": "object"},
        "solution_expression": {"type": "string"},
        "unit": {"type": ["string", "null"]},
        "tolerance_rel": {"type": "number"},
        "explanation": {"type": "string"},
    },
    "required": ["stem", "variables", "solution_expression", "explanation"],
}


def normalize_stem(stem: str) -> str:
    return " ".join(stem.strip().lower().split())


def stem_hash(stem: str) -> str:
    return hashlib.sha256(normalize_stem(stem).encode()).hexdigest()


def generate_mcq(
    *,
    concept_name: str,
    concept_summary: str,
    unit_context: str,
    misconceptions: list[str],
    difficulty: str,
    complete: Any,
    model: str,
) -> dict[str, Any]:
    prompt = (
        f"Write ONE {difficulty} multiple-choice question testing '{concept_name}' "
        f"({concept_summary[:300]}). Ground it ONLY in these course excerpts; a "
        "student must need them to answer.\n\nExcerpts:\n" + unit_context + "\n\n"
        "Exactly 4 options keys A-D with exactly one is_correct. Each wrong option "
        "must name a student misconception and explain why_wrong in one sentence. "
        f"Use these known misconceptions where fitting: {', '.join(misconceptions[:6]) or 'none'}."
    )
    result: StructuredResult = complete(prompt=prompt, schema=MCQ_SCHEMA, model=model)
    return result.data


def generate_numerical(
    *,
    concept_name: str,
    concept_summary: str,
    unit_context: str,
    difficulty: str,
    complete: Any,
    model: str,
) -> dict[str, Any]:
    prompt = (
        f"Write ONE {difficulty} numerical probability problem testing '{concept_name}' "
        f"({concept_summary[:300]}). Ground it ONLY in these course excerpts.\n\nExcerpts:\n"
        + unit_context
        + "\n\nGive concrete variables, a solution_expression using only "
        "numbers + - * / ** ( ) sqrt exp log sin cos tan pi e and the variables, a unit "
        "or null, and tolerance_rel (default 0.01). The expression evaluated with the "
        "variables must equal the correct answer."
    )
    result: StructuredResult = complete(prompt=prompt, schema=NUMERICAL_SCHEMA, model=model)
    return result.data
