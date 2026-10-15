"""Upload + job + worker tests against real Postgres (local/docker only).

Uses dependency overrides so the API talks to the test database.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.config import get_settings
from app.db.repositories import library
from app.main import app
from app.workers import runner

SYNC_URL = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg://studygraph:studygraph@127.0.0.1:15432/studygraph",
)
FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "three_page.pdf")
_test_engine: Engine | None = None


def _override_session() -> Session:
    if _test_engine is None:
        raise RuntimeError("local PostgreSQL fixture was not initialized")
    with Session(_test_engine) as sess:
        yield sess


@pytest.fixture(autouse=True)
def _api_override():
    """Scope the dependency override to this module's tests only."""
    app.dependency_overrides[get_session] = _override_session
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture(autouse=True)
def _clean_db(
    local_postgres_engine: Engine,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global _test_engine
    _test_engine = local_postgres_engine
    monkeypatch.setenv("DATA_DIR", str(tmp_path_factory.mktemp("data")))
    with Session(local_postgres_engine) as sess:
        for table in ("content_units", "sources", "courses", "jobs"):
            sess.execute(text(f"DELETE FROM {table}"))
        sess.commit()


client = TestClient(app)


def test_upload_creates_source_and_job() -> None:
    course = client.post("/api/courses", json={"title": "T"}).json()
    with open(FIXTURE, "rb") as handle:
        response = client.post(
            f"/api/courses/{course['id']}/sources",
            files={"file": ("three_page.pdf", handle, "application/pdf")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "queued" and "job_id" in body
    job = client.get(f"/api/jobs/{body['job_id']}").json()
    assert job["status"] == "queued"


def test_worker_ingests_uploaded_pdf(local_postgres_engine: Engine) -> None:
    settings = get_settings()
    assert settings.llm_provider == "mock" and settings.embed_backend == "hash"
    course = client.post("/api/courses", json={"title": "T2"}).json()
    with open(FIXTURE, "rb") as handle:
        body = client.post(
            f"/api/courses/{course['id']}/sources",
            files={"file": ("three_page.pdf", handle, "application/pdf")},
        ).json()
    with Session(local_postgres_engine) as session:
        assert runner.process_one_job(session, settings) is True
        assert runner.process_one_job(session, settings) is False
        source = library.get_source(session, uuid.UUID(body["id"]))
        assert source is not None and source.status == "ready"
        units = library.list_source_units(session, source.id)
        assert len(units) >= 4
        assert any(u.kind == "figure" and u.figure_description for u in units)


def test_reject_non_pdf() -> None:
    course = client.post("/api/courses", json={"title": "T3"}).json()
    response = client.post(
        f"/api/courses/{course['id']}/sources",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
