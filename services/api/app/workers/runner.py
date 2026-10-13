"""DB-backed job runner. Polls `jobs`, dispatches by kind (Phase 1-2: ingest_pdf)."""

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.repositories import library
from app.db.session import session_scope
from app.ingestion import pdf as pdf_ingestion
from app.llm.factory import get_llm

logger = logging.getLogger(__name__)

POLL_INTERVAL_S = 5


def process_one_job(session: Session, settings: Settings) -> bool:
    """Claim and run a single queued job. Returns True if a job was processed."""
    job = library.claim_next_job(session)
    if job is None:
        return False
    session.commit()
    try:
        if job.kind == "ingest_pdf":
            _run_ingest_pdf(session, settings, job.payload_json)
        else:
            raise ValueError(f"unknown job kind: {job.kind}")
    except Exception as exc:  # noqa: BLE001 - recorded on the job row
        session.rollback()
        job = library.get_job(session, job.id)
        assert job is not None
        library.finish_job(session, job, error=str(exc)[:500])
        session.commit()
        logger.exception("job %s failed", job.id)
        return True
    job = library.get_job(session, job.id)
    assert job is not None
    library.finish_job(session, job)
    session.commit()
    return True


def _run_ingest_pdf(session: Session, settings: Settings, payload: dict[str, Any]) -> None:
    source_id = payload["source_id"]
    source = library.get_source(session, source_id)
    if source is None:
        raise ValueError(f"source {source_id} not found")
    library.set_source_status(session, source, "processing")
    session.commit()

    llm = get_llm(settings)
    work_dir = f"{settings.data_dir}/work/{source.id}"
    units, quality = pdf_ingestion.ingest_pdf(
        source_id=source.id,
        pdf_path=source.path,
        work_dir=work_dir,
        settings=settings,
        vision_call=llm.vision_describe,
    )
    pdf_ingestion.embed_and_attach(units, settings=settings)
    library.replace_source_units(session, source_id=source.id, units=units)
    library.set_source_status(
        session,
        source,
        "ready",
        page_count=int(quality["page_count"]),
        quality_json={k: v for k, v in quality.items()},
    )
    session.commit()


def main() -> None:
    settings = get_settings()
    logger.info("worker started (poll %ss)", POLL_INTERVAL_S)
    while True:
        with session_scope() as session:
            try:
                worked = process_one_job(session, settings)
            except Exception:  # noqa: BLE001 - keep the loop alive
                logger.exception("worker iteration failed")
                worked = False
        if not worked:
            time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
