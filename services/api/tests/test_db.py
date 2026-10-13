"""DB integration tests against real Postgres+pgvector (local/docker only, never CI).

Requires DATABASE_URL_SYNC pointing at a migrated database, e.g.
postgresql+psycopg://studygraph:studygraph@localhost:5432/studygraph
with `alembic upgrade head` applied.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db import models
from app.db.repositories import library

SYNC_URL = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg://studygraph:studygraph@127.0.0.1:15432/studygraph",
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine(SYNC_URL)
    with Session(engine) as sess:
        # Isolate per test: wipe library tables.
        for table in ("content_units", "sources", "courses", "jobs"):
            sess.execute(text(f"DELETE FROM {table}"))
        sess.commit()
        yield sess
        sess.rollback()


def test_pgvector_extension_present(session: Session) -> None:
    row = session.execute(
        text("SELECT extversion FROM pg_extension WHERE extname='vector'")
    ).first()
    assert row is not None


def test_course_source_unit_round_trip(session: Session) -> None:
    course = library.create_course(session, title="Demo", is_demo=True)
    source = library.create_source(
        session,
        course_id=course.id,
        kind="pdf",
        filename="L01.pdf",
        path="/tmp/L01.pdf",
        sha256="abc",
    )
    assert library.get_source(session, source.id) is not None
    library.set_source_status(session, source, "ready", page_count=10)
    assert source.status == "ready"

    units = [
        models.ContentUnit(source_id=source.id, kind="text", text="a", page=1),
        models.ContentUnit(source_id=source.id, kind="text", text="b", page=2),
    ]
    library.replace_source_units(session, source_id=source.id, units=units)
    assert len(library.list_source_units(session, source.id)) == 2

    # Re-ingest replaces, not appends.
    library.replace_source_units(
        session,
        source_id=source.id,
        units=[models.ContentUnit(source_id=source.id, kind="text", text="c", page=1)],
    )
    remaining = library.list_source_units(session, source.id)
    assert len(remaining) == 1 and remaining[0].text == "c"


def test_job_claim_finish_cycle(session: Session) -> None:
    job = library.create_job(session, kind="ingest_pdf", payload={"source_id": str(uuid.uuid4())})
    claimed = library.claim_next_job(session)
    assert claimed is not None and claimed.id == job.id
    assert library.claim_next_job(session) is None  # already processing
    library.finish_job(session, claimed)
    assert library.get_job(session, job.id) is not None
    assert library.get_job(session, job.id).status == "done"  # type: ignore[union-attr]

    bad = library.create_job(session, kind="ingest_pdf")
    library.finish_job(session, bad, error="boom")
    assert library.get_job(session, bad.id).status == "failed"  # type: ignore[union-attr]
