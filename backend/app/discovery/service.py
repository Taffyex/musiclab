"""Discovery orchestration service."""

from __future__ import annotations

import aiosqlite

from app.cache.service import CacheService
from app.discogs.service import DiscogsService
from app.discovery.schemas import DiscoveryBatch, DiscoveryCard
from app.lastfm.service import LastfmService
from app.lidarr.service import LidarrService
from app.llm.base import LLMProvider
from app.musicbrainz.service import MusicBrainzService


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
        from app.llm.prompts import build_system_prompt
        import json
        import time
        from uuid import uuid4
        
        # 1. Load user profile and memory
        profile = None
        user_row = await self.db.execute("SELECT lastfm_username FROM users WHERE id = ?", (user_id,))
        async with user_row as cursor:
            row = await cursor.fetchone()
            if row and row["lastfm_username"]:
                profile = await self.lastfm.get_full_profile(row["lastfm_username"])
                
        async with self.db.execute("SELECT data FROM memory_blocks WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        memory = json.loads(row["data"]) if row else {}
        
        # 2. Get library artist names
        library_names = await self.lidarr.get_library_artist_names()
        
        # 3. Build prompt and ask LLM
        system_prompt = build_system_prompt(profile=profile, memory=memory, library=library_names, mode="discovery")
        user_prompt = f"Please generate {count} artist recommendations."
        
        llm_response = await self.llm.generate(system_prompt, user_prompt)
        
        # Parse output - assuming the LLM returns a JSON array of DiscoveryRecommendation objects
        try:
            raw_recs = json.loads(llm_response.content)
            recs = [raw_rec.get("artist_name", "") for raw_rec in raw_recs if raw_rec.get("artist_name")]
        except Exception:
            recs = []
            
        # 4. Enrich each artist
        cards = []
        for name in recs:
            enriched = await self.enrich_artist(name)
            card = DiscoveryCard(
                artist_name=name,
                metadata=enriched
            )
            cards.append(card)
            
        # 5. Persist batch
        batch = DiscoveryBatch(
            id=str(uuid4()),
            created_at=int(time.time()),
            cards=cards
        )
        await self.db.execute(
            "INSERT INTO discovery_history (id, user_id, batch_data, created_at) VALUES (?, ?, ?, ?)",
            (batch.id, user_id, json.dumps(batch.model_dump()), batch.created_at)
        )
        await self.db.commit()
        return batch

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
        from app.llm.prompts import build_system_prompt
        import json
        
        system_prompt = build_system_prompt(mode="explore")
        user_prompt = f"Please explore {count} artists similar to {artist_name}."
        
        llm_response = await self.llm.generate(system_prompt, user_prompt)
        
        try:
            raw_recs = json.loads(llm_response.content)
            recs = [raw_rec.get("artist_name", "") for raw_rec in raw_recs if raw_rec.get("artist_name")]
        except Exception:
            recs = []
            
        cards = []
        for name in recs:
            enriched = await self.enrich_artist(name)
            card = DiscoveryCard(
                artist_name=name,
                metadata=enriched
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
            self.lastfm.get_full_profile(artist_name), # using profile for artist data temporarily or a custom call
            self.discogs.enrich_artist(artist_name),
            self.musicbrainz.enrich_artist(artist_name),
            return_exceptions=True
        )
        
        return {
            "lastfm": lastfm_data.model_dump() if not isinstance(lastfm_data, Exception) and lastfm_data else None,
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
        import json
        async with self.db.execute(
            "SELECT batch_data FROM discovery_history WHERE user_id = ? ORDER BY created_at DESC", 
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
        batches = []
        for row in rows:
            batches.append(DiscoveryBatch.model_validate(json.loads(row["batch_data"])))
            
        return batches
