"""Last.fm business-logic service layer."""

from __future__ import annotations

import aiosqlite

from app.cache.service import CacheService
from app.lastfm.client import LastfmClient
from app.lastfm.schemas import LastfmProfile


class LastfmService:
    """Orchestrates Last.fm API calls, caching, and persistence."""

    def __init__(
        self,
        client: LastfmClient,
        cache: CacheService,
        db: aiosqlite.Connection,
    ) -> None:
        self.client = client
        self.cache = cache
        self.db = db

    async def get_full_profile(self, username: str) -> LastfmProfile:
        """Return the user's aggregated Last.fm profile.

        Checks the cache first; on miss, fetches from the API and caches the
        result before returning.

        Args:
            username: The Last.fm username.

        Returns:
            A fully populated :class:`LastfmProfile`.
        """
        # TODO: Build cache key from username
        # TODO: Check cache via self.cache.get(key)
        # TODO: On miss, call client methods (top_artists, top_albums, etc.)
        # TODO: Assemble LastfmProfile from responses
        # TODO: Cache the assembled profile
        raise NotImplementedError

    async def refresh_profile(self, username: str) -> LastfmProfile:
        """Force-refresh a user's Last.fm profile, bypassing the cache.

        Args:
            username: The Last.fm username.

        Returns:
            A freshly fetched :class:`LastfmProfile`.
        """
        # TODO: Invalidate existing cache entries for this user
        # TODO: Fetch fresh data via self.client
        # TODO: Cache and return new profile
        raise NotImplementedError

    async def save_profile(self, user_id: int, profile: LastfmProfile) -> None:
        """Persist the Last.fm profile to the ``lastfm_profiles`` table.

        Args:
            user_id: Internal user ID.
            profile: The profile data to persist.
        """
        # TODO: Serialize profile to JSON
        # TODO: INSERT OR REPLACE into lastfm_profiles table
        raise NotImplementedError
