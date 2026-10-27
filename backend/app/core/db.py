"""SQLite engine and session."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

from app.core.config import get_settings


def _set_sqlite_pragmas(dbapi_connection: object, _connection_record: object) -> None:
    """Apply SQLite pragmas: journal mode, busy_timeout, foreign keys."""
    cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
    cursor.execute("PRAGMA journal_mode=DELETE")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@lru_cache
def get_engine() -> Engine:
    """Return the cached engine for the configured DB path."""
    engine = create_engine(
        f"sqlite:///{get_settings().db_path}",
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with Session(get_engine()) as session:
        yield session
