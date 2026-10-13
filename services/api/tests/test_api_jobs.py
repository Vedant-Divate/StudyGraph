"""Upload + job + worker tests against real Postgres (local/docker only).

Uses dependency overrides so the API talks to the test database.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
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


def _override_session() -> Session:
    engine = create_engine(SYNC_URL)
    with Session(engine) as sess:
        yield sess


@pytest.fixture(autouse=True)
def _clean_db(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path_factory.mktemp("data")))
    engine = create_engine(SYNC_URL)
    with Session(engine) as sess:
        for table in ("content_units", "sources", "courses", "jobs"):
            sess.execute(text(f"DELETE FROM {table}"))
        sess.commit()


app.dependency_overrides[get_session] = _override_session
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


def test_worker_ingests_uploaded_pdf() -> None:
    settings = get_settings()
    assert settings.llm_provider == "mock" and settings.embed_backend == "hash"
    course = client.post("/api/courses", json={"title": "T2"}).json()
    with open(FIXTURE, "rb") as handle:
        body = client.post(
            f"/api/courses/{course['id']}/sources",
            files={"file": ("three_page.pdf", handle, "application/pdf")},
        ).json()
    engine = create_engine(SYNC_URL)
    with Session(engine) as session:
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
