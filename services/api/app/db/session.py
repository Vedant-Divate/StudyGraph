"""Engine + session factory. Only repositories touch SQL."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _database_url() -> str:
    return get_settings().database_url


def make_session_factory(url: str | None = None) -> sessionmaker[Session]:
    engine = create_engine(url or _database_url(), pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(url: str | None = None) -> Iterator[Session]:
    factory = make_session_factory(url)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
