"""Shared test fixtures — provides FastAPI test client with DB and mocked LLM."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.ai.llm.base import LLMClient, LLMResponse, ToolCallResult
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.tenant import TenantModel

import app.models  # noqa: F401


# ── Test DB engine (lazily created) ──────────────────────────────────

_test_engine = None
_TestSession = None


def _get_test_engine():
    """Lazily create the test DB engine on first use."""
    global _test_engine, _TestSession
    if _test_engine is None:
        _settings = get_settings()
        _test_engine = create_engine(_settings.DATABASE_URL, pool_pre_ping=True)
        _TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)
    return _test_engine


def _get_test_session():
    """Return the test session factory, creating engine if needed."""
    _get_test_engine()
    return _TestSession


@pytest.fixture(scope="session", autouse=False)
def create_tables() -> Generator[None, None, None]:
    engine = _get_test_engine()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(create_tables) -> Generator[Session, None, None]:
    """Yield a DB session wrapped in a SAVEPOINT that is rolled back after use.

    This ensures every test (including those that call db.commit()) is
    fully isolated without data leaking between tests.
    """
    engine = _get_test_engine()
    TestSession = _get_test_session()

    connection = engine.connect()
    transaction = connection.begin()
    session = TestSession(bind=connection)

    # Start a SAVEPOINT so that session.commit() inside tests only
    # releases the savepoint, not the outer transaction.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, trans: Any) -> None:
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def tenant(db: Session) -> TenantModel:
    t = TenantModel(
        id=uuid.uuid4(),
        name="Test Corp",
        api_key="test-api-key-123",
        is_active=True,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def other_tenant(db: Session) -> TenantModel:
    t = TenantModel(
        id=uuid.uuid4(),
        name="Other Corp",
        api_key="other-api-key-456",
        is_active=True,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


class MockLLMClient(LLMClient):
    """Deterministic mock LLM — returns a preconfigured response."""

    def __init__(self, response: LLMResponse) -> None:
        self._response = response

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        return self._response


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override_db() -> Generator[Session, None, None]:
        yield db

    fastapi_app.dependency_overrides[get_db] = _override_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
