"""Discovery orchestration service."""

from __future__ import annotations

import aiosqlite
import logging

logger = logging.getLogger(__name__)

from app.cache.service import CacheService
from app.common.utils import parse_llm_json
from app.discogs.service import DiscogsService
from app.discovery.schemas import DiscoveryBatch, DiscoveryCard
from app.lastfm.service import LastfmService
from app.lidarr.service import LidarrService
from app.llm.base import LLMProvider
from app.llm.prompts import build_system_prompt
from app.musicbrainz.service import MusicBrainzService

import json
from datetime import datetime, timezone
from uuid import uuid4


class DiscoveryService:
    """Main orchestrator for generating music discovery recommendations.

    Coordinates the LLM, Last.fm, Discogs, MusicBrainz, Lidarr, and cache
    services to produce enriched discovery cards.
    """

    def __init__(
        self,
        lastfm: LastfmService,
        discogs: DiscogsService,
        musicbrainz: MusicBrainzService,
        lidarr: LidarrService,
        llm: LLMProvider,
        cache: CacheService,
        db: aiosqlite.Connection,
    ) -> None:
        self.lastfm = lastfm
        self.discogs = discogs
        self.musicbrainz = musicbrainz
        self.lidarr = lidarr
        self.llm = llm
        self.cache = cache
        self.db = db

    async def generate_batch(
        self, user_id: int, count: int = 8
    ) -> DiscoveryBatch:
        """Generate a batch of discovery recommendation cards.

        This is the main entry point for the discovery pipeline:
        1. Load user profile and memory
        2. Get library artist names (for exclusion)
        3. Ask the LLM for recommendations
        4. Enrich each recommendation with metadata from all sources
        5. Persist the batch to history

        Args:
            user_id: Internal user ID.
            count: Number of cards to generate.

        Returns:
            A :class:`DiscoveryBatch` containing enriched cards.
        """
        # 1. Load user profile and memory
        profile = None
        user_row = await self.db.execute("SELECT lastfm_username FROM users WHERE id = ?", (user_id,))
        async with user_row as cursor:
            row = await cursor.fetchone()
            if row and row["lastfm_username"]:
                profile = await self.lastfm.get_full_profile(row["lastfm_username"])
                
        async with self.db.execute("SELECT memory FROM memory_blocks WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        memory = json.loads(row["memory"]) if row else {}
        
        # 2. Get library artist names
        library_names = await self.lidarr.get_library_artist_names()
        
        # 2.5. Fetch explicit favorites
        favorite_artists: list[str] = []
        favorite_genres: list[str] = []
        favorite_styles: list[str] = []

        async with self.db.execute(
            """SELECT a.name FROM favorites f
               JOIN artists a ON f.entity_id = a.id
               WHERE f.user_id = ? AND f.entity_type = 'artist'
               ORDER BY f.created_at DESC LIMIT 30""", (user_id,)
        ) as cursor:
            async for row in cursor:
                favorite_artists.append(row[0])

        async with self.db.execute(
            """SELECT g.name FROM favorites f
               JOIN genres g ON f.entity_id = g.id
               WHERE f.user_id = ? AND f.entity_type = 'genre'
               ORDER BY f.created_at DESC""", (user_id,)
        ) as cursor:
            async for row in cursor:
                favorite_genres.append(row[0])

        async with self.db.execute(
            """SELECT s.name FROM favorites f
               JOIN styles s ON f.entity_id = s.id
               WHERE f.user_id = ? AND f.entity_type = 'style'
               ORDER BY f.created_at DESC""", (user_id,)
        ) as cursor:
            async for row in cursor:
                favorite_styles.append(row[0])

        favorites = {
            "favorite_artists": ", ".join(favorite_artists) or "None",
            "favorite_genres": ", ".join(favorite_genres) or "None",
            "favorite_styles": ", ".join(favorite_styles) or "None",
        }
        
        # 3. Build prompt and ask LLM
        system_prompt = build_system_prompt(profile=profile, memory=memory, library=library_names, favorites=favorites, mode="discovery")
        user_prompt = f"Please generate {count} artist recommendations."
        
        llm_response = await self.llm.generate(system_prompt, user_prompt)
        
        # 3.5 Parse LLM output
        raw_recs = parse_llm_json(llm_response.content)
        if not raw_recs:
            logger.warning("LLM returned no parseable recommendations")
            
        # 4. Enrich each artist
        cards = []
        for raw_rec in raw_recs:
            name = raw_rec.get("artist_name")
            if not name:
                continue
            enriched = await self.enrich_artist(name)
            lastfm_data = enriched.get("lastfm") or {}
            
            card = DiscoveryCard(
                id=str(uuid4()),
                artist_name=name,
                genre_tags=raw_rec.get("genre_tags", []),
                era=raw_rec.get("era", ""),
                ai_blurb=raw_rec.get("ai_blurb", ""),
                why_it_matches=raw_rec.get("why_it_matches", ""),
                lastfm_listeners=lastfm_data.get("listeners"),
                lastfm_playcount=lastfm_data.get("playcount"),
                mb_data=enriched.get("musicbrainz"),
                discogs_data=enriched.get("discogs")
            )
            cards.append(card)
            
        # 5. Persist batch
        batch_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        
        # Insert batch
        cursor = await self.db.execute(
            "INSERT INTO discovery_batches (id, user_id, created_at) VALUES (?, ?, ?)",
            (batch_id, user_id, created_at)
        )
        await self.db.commit()
        
        # Insert cards individually
        for c in cards:
            await self.db.execute(
                """INSERT INTO discovery_cards (
                    id, batch_id, artist_name, genre_tags, era, ai_blurb, why_it_matches,
                    lastfm_listeners, lastfm_playcount, mb_data, discogs_data, already_in_lidarr
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    c.id, batch_id, c.artist_name, json.dumps(c.genre_tags), c.era, c.ai_blurb, c.why_it_matches,
                    c.lastfm_listeners, c.lastfm_playcount, 
                    json.dumps(c.mb_data) if c.mb_data else None, 
                    json.dumps(c.discogs_data) if c.discogs_data else None,
                    c.already_in_lidarr
                )
            )
        await self.db.commit()
        
        return DiscoveryBatch(
            id=batch_id,
            created_at=created_at,
            cards=cards
        )

    async def explore_similar(
        self, user_id: int, artist_name: str, count: int = 5
    ) -> list[DiscoveryCard]:
        """Explore artists similar to a given artist.

        Args:
            user_id: Internal user ID.
            artist_name: The seed artist name.
            count: Number of similar artists to return.

        Returns:
            A list of enriched :class:`DiscoveryCard` objects.
        """
        system_prompt = build_system_prompt(mode="explore")
        user_prompt = f"Please explore {count} artists similar to {artist_name}."
        
        llm_response = await self.llm.generate(system_prompt, user_prompt)
        
        raw_recs = parse_llm_json(llm_response.content)
            
        cards = []
        for raw_rec in raw_recs:
            name = raw_rec.get("artist_name")
            if not name:
                continue
            enriched = await self.enrich_artist(name)
            lastfm_data = enriched.get("lastfm") or {}
            
            card = DiscoveryCard(
                id=str(uuid4()),
                artist_name=name,
                genre_tags=raw_rec.get("genre_tags", []),
                era=raw_rec.get("era", ""),
                ai_blurb=raw_rec.get("ai_blurb", ""),
                why_it_matches=raw_rec.get("why_it_matches", ""),
                lastfm_listeners=lastfm_data.get("listeners"),
                lastfm_playcount=lastfm_data.get("playcount"),
                mb_data=enriched.get("musicbrainz"),
                discogs_data=enriched.get("discogs")
            )
            cards.append(card)
            
        return cards

    async def enrich_artist(self, artist_name: str) -> dict:
        """Fetch metadata for an artist from all available sources.

        Queries Last.fm, Discogs, and MusicBrainz in parallel and merges
        the results.

        Args:
            artist_name: The artist name to look up.

        Returns:
            A dict with keys ``"lastfm"``, ``"discogs"``, ``"musicbrainz"``.
        """
        import asyncio
        lastfm_data, discogs_data, mb_data = await asyncio.gather(
            self.lastfm.client.get_artist_info(artist_name),
            self.discogs.enrich_artist(artist_name),
            self.musicbrainz.enrich_artist(artist_name),
            return_exceptions=True
        )
        
        return {
            "lastfm": lastfm_data if not isinstance(lastfm_data, Exception) and lastfm_data else None,
            "discogs": discogs_data.model_dump() if not isinstance(discogs_data, Exception) and discogs_data else None,
            "musicbrainz": mb_data.model_dump() if not isinstance(mb_data, Exception) and mb_data else None
        }

    async def get_history(self, user_id: int) -> list[DiscoveryBatch]:
        """Return past discovery batches for a user.

        Args:
            user_id: Internal user ID.

        Returns:
            A list of :class:`DiscoveryBatch` objects, newest first.
        """
        async with self.db.execute(
            "SELECT id, created_at FROM discovery_batches WHERE user_id = ? ORDER BY created_at DESC", 
            (user_id,)
        ) as cursor:
            batch_rows = await cursor.fetchall()
            
        batches = []
        for row in batch_rows:
            batch_id = row["id"]
            created_at = row["created_at"]
            
            cards = []
            async with self.db.execute(
                """SELECT id, artist_name, genre_tags, era, ai_blurb, why_it_matches,
                          lastfm_listeners, lastfm_playcount, mb_data, discogs_data, already_in_lidarr
                   FROM discovery_cards WHERE batch_id = ?""",
                (batch_id,)
            ) as c_cursor:
                card_rows = await c_cursor.fetchall()
                for crow in card_rows:
                    cards.append(DiscoveryCard(
                        id=str(crow["id"]),
                        artist_name=crow["artist_name"],
                        genre_tags=json.loads(crow["genre_tags"]) if crow["genre_tags"] else [],
                        era=crow["era"],
                        ai_blurb=crow["ai_blurb"],
                        why_it_matches=crow["why_it_matches"],
                        lastfm_listeners=crow["lastfm_listeners"],
                        lastfm_playcount=crow["lastfm_playcount"],
                        mb_data=json.loads(crow["mb_data"]) if crow["mb_data"] else None,
                        discogs_data=json.loads(crow["discogs_data"]) if crow["discogs_data"] else None,
                        already_in_lidarr=bool(crow["already_in_lidarr"])
                    ))
                    
            if type(created_at) == str:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
            batches.append(DiscoveryBatch(id=str(batch_id), created_at=created_at, cards=cards))
            
        return batches
