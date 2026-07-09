"""Database engine and session factory."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from halflight.config import get_settings

engine = create_engine(get_settings().database_url, echo=False, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: yields a session, closes it after the request."""
    with Session(engine) as session:
        yield session
