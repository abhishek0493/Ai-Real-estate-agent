"""Database session and engine setup."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def _build_engine(settings: Settings) -> sessionmaker[Session]:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


_session_factory: sessionmaker[Session] | None = None


def _get_session_factory(settings: Settings) -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = _build_engine(settings)
    return _session_factory


def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session and closes it after use."""
    factory = _get_session_factory(settings)
    session = factory()
    try:
        yield session
    finally:
        session.close()
