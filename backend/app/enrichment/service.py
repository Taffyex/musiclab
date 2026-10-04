"""Background enrichment service for Last.fm data."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import aiosqlite

from app.cache.service import CacheService
from app.config import settings
from app.lastfm.client import LastfmClient
from app.lastfm.service import LastfmService

logger = logging.getLogger(__name__)

# Rate limit: max requests per second to Last.fm
RATE_LIMIT_RPS = 5


class EnrichmentService:
    """Background service for enriching artists/tracks with Last.fm data."""

    def __init__(self, db: aiosqlite.Connection, lastfm: LastfmService) -> None:
        self._db = db
        self._lastfm = lastfm
        self._running = False

    async def enqueue_artist(self, artist_id: int, priority: int = 1) -> None:
        """Add an artist to the enrichment queue."""
        await self._db.execute(
            """INSERT INTO enrichment_queue (entity_type, entity_id, priority)
               VALUES ('artist', ?, ?)
               ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                   priority = MAX(enrichment_queue.priority, excluded.priority),
                   updated_at = CURRENT_TIMESTAMP""",
            (artist_id, priority)
        )
        await self._db.commit()

    async def enqueue_user_interests(self, user_id: int) -> None:
        """Bulk-enqueue artists in the user's favorite genres/styles at higher priority."""
        await self._db.execute(
            """INSERT INTO enrichment_queue (entity_type, entity_id, priority)
               SELECT 'artist', a.id, 3
               FROM artists a
               JOIN artist_genres ag ON a.id = ag.artist_id
               JOIN favorites f ON f.entity_id = ag.genre_id AND f.entity_type = 'genre'
               WHERE f.user_id = ? AND a.lastfm_listeners IS NULL
               ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                   priority = MAX(enrichment_queue.priority, excluded.priority)""",
            (user_id,)
        )
        await self._db.execute(
            """INSERT INTO enrichment_queue (entity_type, entity_id, priority)
               SELECT 'artist', a.id, 3
               FROM artists a
               JOIN artist_styles ast ON a.id = ast.artist_id
               JOIN favorites f ON f.entity_id = ast.style_id AND f.entity_type = 'style'
               WHERE f.user_id = ? AND a.lastfm_listeners IS NULL
               ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                   priority = MAX(enrichment_queue.priority, excluded.priority)""",
            (user_id,)
        )
        await self._db.commit()

    async def enrich_artist_now(self, artist_id: int) -> None:
        """Immediate enrichment for a single artist (lazy mode)."""
        async with self._db.execute(
            "SELECT name FROM artists WHERE id = ?", (artist_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return
            artist_name = row[0]

        try:
            info = await self._lastfm.client.get_artist_info(artist_name)
            listeners = int(info.get("stats", {}).get("listeners", 0))
            playcount = int(info.get("stats", {}).get("playcount", 0))
            bio = info.get("bio", {}).get("summary", "")

            await self._db.execute(
                """UPDATE artists SET lastfm_listeners = ?, lastfm_playcount = ?,
                       bio = CASE WHEN bio = '' OR bio IS NULL THEN ? ELSE bio END,
                       fetched_at = ?
                   WHERE id = ?""",
                (listeners, playcount, bio, datetime.now(timezone.utc).isoformat(), artist_id)
            )
            await self._db.commit()
            logger.info("Enriched artist %s (id=%d): %d listeners", artist_name, artist_id, listeners)
        except Exception:
            logger.exception("Failed to enrich artist %s (id=%d)", artist_name, artist_id)

    async def process_queue(self, batch_size: int = 10) -> int:
        """Process the next batch from the enrichment queue. Returns count processed."""
        async with self._db.execute(
            """SELECT eq.id, eq.entity_type, eq.entity_id
               FROM enrichment_queue eq
               WHERE eq.status = 'pending'
               ORDER BY eq.priority DESC, eq.created_at ASC
               LIMIT ?""",
            (batch_size,)
        ) as cursor:
            items = await cursor.fetchall()

        if not items:
            return 0

        ids = [item[0] for item in items]
        placeholders = ",".join("?" * len(ids))
        await self._db.execute(
            f"UPDATE enrichment_queue SET status = 'processing' WHERE id IN ({placeholders})",
            ids
        )
        await self._db.commit()

        processed = 0
        for queue_id, entity_type, entity_id in items:
            try:
                if entity_type == "artist":
                    await self.enrich_artist_now(entity_id)
                status = "done"
                processed += 1
            except Exception:
                logger.exception("Enrichment failed for %s %d", entity_type, entity_id)
                # Check attempts to set failed_permanently if retries exceeded
                async with self._db.execute("SELECT attempts FROM enrichment_queue WHERE id = ?", (queue_id,)) as c:
                    row = await c.fetchone()
                    attempts = row[0] if row else 0
                status = "failed_permanently" if attempts >= 2 else "failed"

            await self._db.execute(
                """UPDATE enrichment_queue SET status = ?, attempts = attempts + 1,
                       updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (status, queue_id)
            )
            await self._db.commit()

            # Rate limiting
            await asyncio.sleep(1.0 / RATE_LIMIT_RPS)

        return processed


async def run_enrichment_worker(db_path: str) -> None:
    """Long-running background worker that processes the enrichment queue."""
    logger.info("Enrichment worker started")
    
    # On startup, recover any orphaned items stuck in 'processing' state
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE enrichment_queue SET status = 'pending' WHERE status = 'processing'")
            await db.commit()
    except Exception:
        logger.exception("Failed to recover orphaned processing items in enrichment queue")

    while True:
        try:
            if not settings.lastfm_api_key:
                logger.warning("Last.fm API key not configured. Enrichment worker sleeping 60s.")
                await asyncio.sleep(60)
                continue

            async with aiosqlite.connect(db_path) as db:
                db.row_factory = aiosqlite.Row
                client = LastfmClient(api_key=settings.lastfm_api_key)
                cache = CacheService(db=db)
                lastfm = LastfmService(client=client, cache=cache, db=db)
                service = EnrichmentService(db=db, lastfm=lastfm)
                try:
                    processed = await service.process_queue(batch_size=10)
                    if processed == 0:
                        await asyncio.sleep(60)  # No work, wait 1 minute
                    else:
                        logger.info("Enrichment worker processed %d items", processed)
                finally:
                    await client.close()
        except asyncio.CancelledError:
            logger.info("Enrichment worker cancelled")
            return
        except Exception:
            logger.exception("Enrichment worker error, restarting in 30s")
            await asyncio.sleep(30)

