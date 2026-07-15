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
        # TODO: Load user Last.fm profile
        # TODO: Load user memory block
        # TODO: Get Lidarr library names for exclusion
        # TODO: Build system prompt with discovery mode
        # TODO: Call LLM to generate recommendations
        # TODO: Parse LLM output into artist names
        # TODO: Enrich each artist via self.enrich_artist(name)
        # TODO: Build DiscoveryCard objects
        # TODO: Persist batch to history table
        raise NotImplementedError

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
        # TODO: Build system prompt with explore mode
        # TODO: Ask LLM for similar artists
        # TODO: Enrich each and build cards
        raise NotImplementedError

    async def enrich_artist(self, artist_name: str) -> dict:
        """Fetch metadata for an artist from all available sources.

        Queries Last.fm, Discogs, and MusicBrainz in parallel and merges
        the results.

        Args:
            artist_name: The artist name to look up.

        Returns:
            A dict with keys ``"lastfm"``, ``"discogs"``, ``"musicbrainz"``.
        """
        # TODO: Gather data from all three services concurrently
        # TODO: Return merged dict
        raise NotImplementedError

    async def get_history(self, user_id: int) -> list[DiscoveryBatch]:
        """Return past discovery batches for a user.

        Args:
            user_id: Internal user ID.

        Returns:
            A list of :class:`DiscoveryBatch` objects, newest first.
        """
        # TODO: Query discovery_history table
        # TODO: Deserialize and return batches
        raise NotImplementedError
