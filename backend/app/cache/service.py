"""Simple key-value cache backed by an aiosqlite database."""

from __future__ import annotations

import json
import time

import aiosqlite


class CacheService:
    """TTL-aware key-value cache stored in an SQLite table.

    The cache table schema (created externally during DB init)::

        CREATE TABLE IF NOT EXISTS cache (
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
        # TODO: SELECT value, expires_at FROM cache WHERE key = ?
        # TODO: Check if expires_at > time.time()
        # TODO: If expired, DELETE and return None
        # TODO: Deserialize JSON and return
        raise NotImplementedError

    async def set(
        self, key: str, value: dict, ttl_seconds: int = 3600
    ) -> None:
        """Store a value in the cache with a TTL.

        Args:
            key: The cache key.
            value: The dict to cache (will be JSON-serialized).
            ttl_seconds: Time-to-live in seconds (default 1 hour).
        """
        # TODO: Compute expires_at = time.time() + ttl_seconds
        # TODO: INSERT OR REPLACE into cache table
        _ = json.dumps(value)  # validate serializable
        _ = time.time()  # timestamp reference
        raise NotImplementedError

    async def invalidate(self, pattern: str) -> None:
        """Delete all cache entries whose key matches *pattern*.

        Args:
            pattern: A SQL LIKE pattern (e.g. ``"lastfm:user123:%"``).
        """
        # TODO: DELETE FROM cache WHERE key LIKE ?
        raise NotImplementedError

    async def cleanup(self) -> None:
        """Remove all expired entries from the cache table."""
        # TODO: DELETE FROM cache WHERE expires_at <= time.time()
        raise NotImplementedError
