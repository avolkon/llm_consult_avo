from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db.base import Base
from app.main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///./test_auth.db"
TEST_DB_FILE = Path("test_auth.db")


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncIterator:
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()
    engine = create_async_engine(TEST_DB_URL, echo=False)
    try:
        yield engine
    finally:
        await engine.dispose()
        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()


@pytest_asyncio.fixture(scope="session")
async def test_session_maker(test_engine) -> async_sessionmaker[AsyncSession]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def client(test_session_maker: async_sessionmaker[AsyncSession]):
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with test_session_maker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
