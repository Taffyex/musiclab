"""Simple key-value cache backed by an aiosqlite database."""

from __future__ import annotations

import json
import time

import aiosqlite


class CacheService:
    """TTL-aware key-value cache stored in an SQLite table.

    The cache table schema (created externally during DB init)::

        CREATE TABLE IF NOT EXISTS cache_entries (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        );
    """

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def get(self, key: str) -> dict | None:
        """Return the cached value for *key*, or ``None`` if missing/expired.

        Args:
            key: The cache key.

        Returns:
            The cached dict, or ``None``.
        """
        async with self.db.execute("SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            return None
            
        if row["expires_at"] < time.time():
            return None
            
        return json.loads(row["value"])

    async def set(
        self, key: str, value: dict, ttl_seconds: int = 3600
    ) -> None:
        """Store a value in the cache with a TTL.

        Args:
            key: The cache key.
            value: The dict to cache (will be JSON-serialized).
            ttl_seconds: Time-to-live in seconds (default 1 hour).
        """
        expires_at = time.time() + ttl_seconds
        val_json = json.dumps(value)
        await self.db.execute(
            "INSERT OR REPLACE INTO cache_entries (key, value, expires_at) VALUES (?, ?, ?)",
            (key, val_json, expires_at)
        )
        await self.db.commit()

    async def invalidate(self, pattern: str) -> None:
        """Delete all cache entries whose key matches *pattern*.

        Args:
            pattern: A SQL LIKE pattern (e.g. ``"lastfm:user123:%"``).
        """
        await self.db.execute("DELETE FROM cache_entries WHERE key LIKE ?", (pattern,))
        await self.db.commit()

    async def cleanup(self) -> None:
        """Remove all expired entries from the cache table."""
        await self.db.execute("DELETE FROM cache_entries WHERE expires_at <= ?", (time.time(),))
        await self.db.commit()
