"""PDF ingestion tests on the tiny fixture (mock VLM + hash embeddings)."""

import os
import uuid
from pathlib import Path

from app.config import get_settings
from app.ingestion import chunking
from app.ingestion import pdf as pdf_ingestion

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "three_page.pdf")

CANNED_FIGURE = (
    '{"caption": "Venn", "what_it_shows": "sets", "labels": [], '
    '"relationships": [], "quantities": []}'
)


def _stub_vision(*, image_path: str, prompt: str, model: str) -> str:
    assert os.path.exists(image_path)
    assert "JSON" in prompt
    return CANNED_FIGURE


def test_chunking_stays_within_page() -> None:
    long_text = "\n\n".join(f"paragraph {i} " + "word " * 120 for i in range(6))
    chunks = chunking.chunk_page_text(long_text)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunking.estimate_tokens(chunk) <= chunking.MAX_TOKENS


def test_ingest_units_have_exactly_one_location(tmp_path: Path) -> None:
    settings = get_settings()
    settings.llm_cache_dir = str(tmp_path / "cache")  # isolate from other tests
    units, quality = pdf_ingestion.ingest_pdf(
        source_id=uuid.uuid4(),
        pdf_path=FIXTURE,
        work_dir=str(tmp_path),
        settings=settings,
        vision_call=_stub_vision,
    )
    assert quality["page_count"] == 3
    assert len([u for u in units if u.kind == "text"]) >= 3
    figures = [u for u in units if u.kind == "figure"]
    assert len(figures) == 1
    assert figures[0].figure_description == CANNED_FIGURE
    assert figures[0].image_path is not None and os.path.exists(figures[0].image_path)
    for unit in units:
        forms = [unit.page is not None, unit.slide is not None, unit.t_start_s is not None]
        assert sum(forms) == 1, f"unit has {sum(forms)} location forms"
        assert unit.page is not None  # pdf pipeline => page locations


def test_embed_and_attach(tmp_path: Path) -> None:
    settings = get_settings()
    assert settings.embed_backend == "hash"
    units, _ = pdf_ingestion.ingest_pdf(
        source_id=uuid.uuid4(),
        pdf_path=FIXTURE,
        work_dir=str(tmp_path),
        settings=settings,
        vision_call=_stub_vision,
    )
    pdf_ingestion.embed_and_attach(units, settings=settings)
    for unit in units:
        assert unit.embedding is not None and len(unit.embedding) == 2048
