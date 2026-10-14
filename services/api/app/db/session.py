"""Engine + session factory. Only repositories touch SQL."""

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)


def _database_url() -> str:
    return get_settings().database_url


def make_session_factory(url: str | None = None) -> sessionmaker[Session]:
    engine = create_engine(
        url or _database_url(),
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
        connect_args={"connect_timeout": 15},
    )
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(url: str | None = None) -> Iterator[Session]:
    """Yield a session; retry the initial connect once (Neon idle resume)."""
    factory = make_session_factory(url)
    session = factory()
    try:
        session.connection()
    except (OperationalError, DBAPIError):
        logger.warning("db connect failed, retrying once")
        session.close()
        time.sleep(1.0)
        session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
