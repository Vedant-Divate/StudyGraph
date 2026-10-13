"""Video ingestion: transcript units from SRT (demo) or whisper (uploads).

ASR path uses faster-whisper lazily (installed in Docker/VM; see ADR-0007).
Demo lectures use OCW's own timestamped subtitles — same origin as the videos.
"""

import logging
import math
import os
import re
import uuid

from app.config import Settings, get_settings
from app.db import models
from app.ingestion import chunking
from app.ingestion.figures import describe_figure
from app.kb.embeddings import embed_texts

logger = logging.getLogger(__name__)

MIN_WINDOW_S = 30.0
MAX_WINDOW_S = 60.0

_SRT_TS = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")


def srt_to_seconds(stamp: str) -> float:
    match = _SRT_TS.match(stamp.strip())
    if not match:
        raise ValueError(f"bad srt timestamp: {stamp!r}")
    h, m, s, ms = (int(g) for g in match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0


def parse_srt(path: str) -> list[tuple[float, float, str]]:
    """Parse SubRip into (start_s, end_s, text) segments, dropping markup/empties."""
    with open(path, encoding="utf-8-sig") as handle:
        content = handle.read()
    blocks = re.split(r"\n\s*\n", content.strip())
    segments: list[tuple[float, float, str]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        timing = lines[1] if "-->" in lines[1] else (lines[0] if "-->" in lines[0] else "")
        if "-->" not in timing:
            continue
        start_raw, _, end_raw = timing.partition("-->")
        try:
            start, end = srt_to_seconds(start_raw), srt_to_seconds(end_raw)
        except ValueError:
            continue
        text_lines = [line for line in lines if "-->" not in line and not line.isdigit()]
        text = re.sub(r"<[^>]+>", "", " ".join(text_lines)).strip()
        if not text or end <= start:
            continue
        segments.append((start, end, text))
    return segments


def merge_windows(
    segments: list[tuple[float, float, str]],
    *,
    min_window: float = MIN_WINDOW_S,
    max_window: float = MAX_WINDOW_S,
) -> list[tuple[float, float, str]]:
    """Merge cues into 30–60 s sentence-friendly windows."""
    windows: list[tuple[float, float, str]] = []
    start, end = 0.0, 0.0
    parts: list[str] = []
    for seg_start, seg_end, text in segments:
        if not parts:
            start = seg_start
        parts.append(text)
        end = seg_end
        if end - start >= min_window and (
            text.rstrip().endswith((".", "?", "!")) or end - start >= max_window
        ):
            windows.append((start, end, " ".join(parts)))
            parts = []
    if parts:
        if windows and end - start < min_window / 2:
            prev_start, _, prev_text = windows.pop()
            windows.append((prev_start, end, prev_text + " " + " ".join(parts)))
        else:
            windows.append((start, end, " ".join(parts)))
    return windows


def transcribe_with_whisper(
    video_path: str, *, model_size: str
) -> list[tuple[float, float, str, float]]:
    """ASR for user uploads (Docker/VM). Returns (start, end, text, confidence)."""
    from faster_whisper import WhisperModel  # lazy: heavy dep, absent locally

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    raw_segments, _info = model.transcribe(video_path, word_timestamps=False)
    out: list[tuple[float, float, str, float]] = []
    for seg in raw_segments:
        text = seg.text.strip()
        if not text:
            continue
        avg_logprob = getattr(seg, "avg_logprob", None)
        confidence = float(math.exp(avg_logprob)) if avg_logprob else 0.0
        out.append((float(seg.start), float(seg.end), text, confidence))
    return out


def transcript_units(
    source_id: uuid.UUID,
    segments: list[tuple[float, float, str]],
    *,
    confidences: list[float] | None = None,
) -> list[models.ContentUnit]:
    units: list[models.ContentUnit] = []
    for i, (start, end, text) in enumerate(merge_windows(segments)):
        units.append(
            models.ContentUnit(
                source_id=source_id,
                kind="transcript",
                text=text,
                t_start_s=start,
                t_end_s=end,
                token_count=chunking.estimate_tokens(text),
                confidence=(confidences[i] if confidences and i < len(confidences) else None),
            )
        )
    return units


def describe_frames(
    frames: list[tuple[float, str]],
    *,
    source_id: uuid.UUID,
    settings: Settings | None = None,
    vision_call: object = None,
) -> list[models.ContentUnit]:
    """Keyframe figure units at their timestamps (capped by the caller)."""
    settings = settings or get_settings()
    units: list[models.ContentUnit] = []
    for timestamp_s, image_path in frames:
        description = ""
        if vision_call is not None:
            description = describe_figure(
                image_path,
                vision_model=settings.vision_model,
                vision_call=vision_call,
                cache_dir=os.path.join(settings.llm_cache_dir, "figures"),
            )
        units.append(
            models.ContentUnit(
                source_id=source_id,
                kind="figure",
                text=f"Video frame at {timestamp_s:.0f}s.",
                figure_description=description or None,
                t_start_s=timestamp_s,
                t_end_s=timestamp_s,
                image_path=image_path,
                token_count=chunking.estimate_tokens(description),
            )
        )
    return units


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
