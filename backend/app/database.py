"""
MusicLab — Database helpers for aiosqlite.

Provides an async context manager for database connections and
an init function that runs the DDL schema on first startup.
"""

import os
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

DB_PATH = "data/musiclab.db"
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Async generator that yields an aiosqlite connection.

    Usage as a FastAPI dependency::

        @app.get("/example")
        async def example(db = Depends(get_db)):
            ...
    """
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    """
    Initialize the database.

    - Creates the ``data/`` directory if it doesn't exist.
    - Reads ``schema.sql`` and executes all CREATE TABLE statements.
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        await db.executescript(schema_sql)
        await db.commit()

    # seed default admin user from AUTH_USERNAME / AUTH_PASSWORD_HASH
    from app.config import settings
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if users table is empty
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            if row and row[0] == 0:
                if settings.auth_username and settings.auth_password_hash:
                    await db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (settings.auth_username, settings.auth_password_hash)
                    )
                    await db.commit()
