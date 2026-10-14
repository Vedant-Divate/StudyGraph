"""Shared fixtures for integration tests that require local PostgreSQL."""

import os
from collections.abc import Iterator
from urllib.parse import urlsplit

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

SYNC_URL = os.environ.get("DATABASE_URL_SYNC")
if SYNC_URL is None:
    SYNC_URL = URL.create(
        "postgresql+psycopg",
        username=os.environ.get("PGUSER", "studygraph"),
        password=os.environ.get("PGPASSWORD", "studygraph"),
        host=os.environ.get("PGHOST", "127.0.0.1"),
        port=int(os.environ.get("PGPORT", "15432")),
        database=os.environ.get("PGDATABASE", "studygraph"),
    ).render_as_string(hide_password=False)
    os.environ["DATABASE_URL_SYNC"] = SYNC_URL


@pytest.fixture(scope="session")
def local_postgres_engine() -> Iterator[Engine]:
    hostname = (urlsplit(SYNC_URL).hostname or "").lower()
    if hostname.endswith(".neon.tech"):
        raise pytest.UsageError(
            "Database integration tests require local PostgreSQL; Neon is refused."
        )

    engine = create_engine(SYNC_URL, connect_args={"connect_timeout": 3})
    try:
        with engine.connect():
            pass
    except OperationalError as exc:
        message = str(exc.orig).lower()
        unreachable = (
            "connection refused",
            "connection timeout expired",
            "could not connect to server",
            "network is unreachable",
            "no route to host",
            "server closed the connection unexpectedly",
        )
        engine.dispose()
        if any(marker in message for marker in unreachable):
            pytest.skip(
                "Local PostgreSQL is unreachable (connection refused or timed out); "
                "these integration tests never use Neon."
            )
        raise RuntimeError(
            f"Local PostgreSQL preflight failed ({type(exc.orig).__name__}); "
            "connection details are suppressed."
        ) from None

    try:
        yield engine
    finally:
        engine.dispose()
