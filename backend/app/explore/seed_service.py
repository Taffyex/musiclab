"""Service for seeding the database with genres and styles."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone

import aiosqlite

from app.lastfm.client import LastfmClient

logger = logging.getLogger(__name__)

class SeedService:
    """Service to load the genre taxonomy into the DB."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db
        from app.config import settings
        self._lastfm = LastfmClient(api_key=settings.lastfm_api_key)

    async def seed_if_needed(self) -> None:
        """Seed genres and styles if the database is empty or data is old."""
        if await self._needs_refresh():
            logger.info("Seeding genre taxonomy...")
            await self.seed_genres()
            await self.supplement_with_lastfm_tags()
            logger.info("Genre taxonomy seeded successfully.")

    async def _needs_refresh(self) -> bool:
        """Check if taxonomy is older than 7 days."""
        async with self._db.execute(
            "SELECT created_at FROM genres ORDER BY created_at DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return True
            created_at = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - created_at > timedelta(days=7):
                return True
        return False

    def _slugify(self, text: str) -> str:
        """Convert a string to a URL-friendly slug."""
        return text.lower().replace(' ', '-').replace('/', '-').replace(',', '').replace('&', 'and')

    async def seed_genres(self) -> None:
        """Insert or update genres and styles from genre_seed.json."""
        seed_path = os.path.join(os.path.dirname(__file__), "genre_seed.json")
        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            logger.exception("Failed to load genre_seed.json")
            return

        for genre_data in data.get("genres", []):
            name = genre_data.get("name")
            slug = self._slugify(name)
            
            # Insert genre
            try:
                await self._db.execute(
                    """
                    INSERT INTO genres (name, slug, source, created_at)
                    VALUES (?, ?, 'discogs', ?)
                    ON CONFLICT(name) DO UPDATE SET created_at=excluded.created_at
                    """,
                    (name, slug, datetime.now(timezone.utc).isoformat())
                )
                await self._db.commit()
            except Exception:
                logger.exception("Failed to insert genre: %s", name)
                continue

            # Get genre_id
            async with self._db.execute("SELECT id FROM genres WHERE name = ?", (name,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    continue
                genre_id = row[0]

            # Insert styles
            for style_name in genre_data.get("styles", []):
                style_slug = self._slugify(style_name)
                try:
                    await self._db.execute(
                        """
                        INSERT INTO styles (name, slug, genre_id, source, created_at)
                        VALUES (?, ?, ?, 'discogs', ?)
                        ON CONFLICT(name, genre_id) DO UPDATE SET created_at=excluded.created_at
                        """,
                        (style_name, style_slug, genre_id, datetime.now(timezone.utc).isoformat())
                    )
                except Exception:
                    logger.exception("Failed to insert style: %s for genre: %s", style_name, name)
            
            await self._db.commit()

    async def supplement_with_lastfm_tags(self) -> None:
        """Fetch top tags from Last.fm and add missing ones as genres."""
        try:
            tags = await self._lastfm.get_global_top_tags(limit=50)
            for tag_info in tags:
                tag_name = tag_info.get("name", "").title()
                if not tag_name:
                    continue
                
                slug = self._slugify(tag_name)
                
                # Check if it already exists as genre or style
                async with self._db.execute("SELECT id FROM genres WHERE name = ?", (tag_name,)) as cursor:
                    if await cursor.fetchone():
                        continue
                async with self._db.execute("SELECT id FROM styles WHERE name = ?", (tag_name,)) as cursor:
                    if await cursor.fetchone():
                        continue
                
                # Insert as a supplementary genre
                await self._db.execute(
                    """
                    INSERT INTO genres (name, slug, source, created_at)
                    VALUES (?, ?, 'lastfm', ?)
                    ON CONFLICT(name) DO NOTHING
                    """,
                    (tag_name, slug, datetime.now(timezone.utc).isoformat())
                )
            await self._db.commit()
        except Exception:
            logger.exception("Failed to supplement with Last.fm tags")
