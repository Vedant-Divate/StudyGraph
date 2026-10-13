"""DB session dependency for routers."""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.session import session_scope


def get_session() -> Iterator[Session]:
    with session_scope() as session:
        yield session
