"""PDF ingestion: per-page text units, page renders, figure units.

Pure pipeline returning unsaved `ContentUnit` models; the caller embeds and
stores them. Chunking never crosses page boundaries so every unit has exactly
one location.
"""

import logging
import os
import uuid
from typing import Any

import pymupdf

from app.config import Settings, get_settings
from app.db import models
from app.ingestion import chunking
from app.ingestion.figures import describe_figure
from app.kb.embeddings import embed_texts

logger = logging.getLogger(__name__)

RENDER_DPI = 110
VECTOR_DRAWING_THRESHOLD = 20


def _render_page(doc: Any, page_no: int, out_dir: str, stem: str) -> str:
    pix: Any = doc[page_no].get_pixmap(dpi=RENDER_DPI)
    path = os.path.join(out_dir, f"{stem}-p{page_no + 1}.png")
    pix.save(path)
    return path


def ingest_pdf(
    *,
    source_id: uuid.UUID,
    pdf_path: str,
    work_dir: str,
    settings: Settings | None = None,
    vision_call: object = None,
) -> tuple[list[models.ContentUnit], dict[str, Any]]:
    """Extract units from a PDF. `vision_call` overrides the VLM (tests pass a stub)."""
    settings = settings or get_settings()
    os.makedirs(work_dir, exist_ok=True)
    doc: Any = pymupdf.open(pdf_path)  # type: ignore[no-untyped-call]
    units: list[models.ContentUnit] = []
    figure_count = 0
    empty_pages = 0

    for page_no in range(len(doc)):
        page: Any = doc[page_no]
        text = page.get_text("text").strip()
        if not text:
            empty_pages += 1
        else:
            for chunk in chunking.chunk_page_text(text):
                units.append(
                    models.ContentUnit(
                        source_id=source_id,
                        kind="text",
                        text=chunk,
                        page=page_no + 1,
                        token_count=chunking.estimate_tokens(chunk),
                    )
                )
        images = page.get_images(full=True)
        drawings = page.get_drawings()
        figure_boxes: list[tuple[float, float, float, float]] = []
        for img in images:
            try:
                bboxes = page.get_image_bbox(img)
                boxes = bboxes if isinstance(bboxes, list) else [bboxes]
                figure_boxes.extend(
                    (b.x0, b.y0, b.x1, b.y1) for b in boxes if b.width > 20 and b.height > 20
                )
            except ValueError:
                continue
        if not figure_boxes and len(drawings) >= VECTOR_DRAWING_THRESHOLD:
            rect = page.rect
            figure_boxes.append((rect.x0, rect.y0, rect.x1, rect.y1))

        for i, (x0, y0, x1, y1) in enumerate(figure_boxes):
            if figure_count >= settings.max_figures_per_source:
                logger.info("figure cap reached for source %s", source_id)
                break
            clip: Any = pymupdf.Rect(x0, y0, x1, y1)  # type: ignore[no-untyped-call]
            pix: Any = page.get_pixmap(dpi=RENDER_DPI, clip=clip)
            fig_path = os.path.join(work_dir, f"fig-p{page_no + 1}-{i}.png")
            pix.save(fig_path)
            description = ""
            if vision_call is not None:
                description = describe_figure(
                    fig_path,
                    vision_model=settings.vision_model,
                    vision_call=vision_call,
                    cache_dir=os.path.join(settings.llm_cache_dir, "figures"),
                )
            units.append(
                models.ContentUnit(
                    source_id=source_id,
                    kind="figure",
                    text=f"Figure on page {page_no + 1}.",
                    figure_description=description or None,
                    page=page_no + 1,
                    image_path=fig_path,
                    token_count=chunking.estimate_tokens(description),
                )
            )
            figure_count += 1

    page_count = len(doc)
    doc.close()
    quality: dict[str, Any] = {
        "page_count": page_count,
        "empty_pages": empty_pages,
        "figure_units": figure_count,
    }
    return units, quality


def embed_and_attach(
    units: list[models.ContentUnit], *, settings: Settings | None = None
) -> list[models.ContentUnit]:
    settings = settings or get_settings()
    texts = [
        u.text + ("\n" + (u.figure_description or "") if u.figure_description else "")
        for u in units
    ]
    vectors = embed_texts(texts, settings=settings)
    for unit, vector in zip(units, vectors, strict=True):
        unit.embedding = vector
    return units
