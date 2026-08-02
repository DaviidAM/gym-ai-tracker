"""Shared fixtures for all tests."""
import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient, ASGITransport
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.main import app
from app.database import Base, get_db


# In-memory synchronous engine for test setup
_test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

# In-memory async engine for the app
_async_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
)


class TestBase(DeclarativeBase):
    pass


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh async database session for each test."""
    async with async_session_maker() as session:
        yield session


_test_session_factory = None

def get_test_session_factory():
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = async_sessionmaker(
            _async_test_engine, class_=AsyncSession, expire_on_commit=False
        )
    return _test_session_factory


@pytest.fixture(scope="function")
async def db_session_for_app() -> AsyncGenerator[AsyncSession, None]:
    """Create tables and provide a session for app dependency injection."""
    # Import here to avoid circular imports
    async with _async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_test_session_factory()
    async with factory() as session:
        yield session

    # Cleanup after test
    async with _async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session_for_app: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client that talks to the app with a test DB."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session_for_app

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
