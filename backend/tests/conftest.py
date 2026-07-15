from __future__ import annotations

"""
MusicLab — Shared pytest fixtures.

Provides a test client backed by an in-memory SQLite database so that
tests run fast and don't touch the real data directory.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import aiosqlite

# TODO: adjust imports once app structure is finalized
from app.main import app
from app.database import get_db, _SCHEMA_PATH


# ──────────────────────────────────────────────
# In-memory database override
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Yield an in-memory aiosqlite connection with the full schema applied.
    """
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row

    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    await db.executescript(schema_sql)
    await db.commit()

    try:
        yield db
    finally:
        await db.close()


# ──────────────────────────────────────────────
# Async test client
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(test_db: aiosqlite.Connection) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP test client with the database dependency overridden
    to use the in-memory test database.
    """

    async def _override_get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
