"""Last.fm business-logic service layer."""

from __future__ import annotations

import asyncio

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

    async def _fetch_profile(self, username: str) -> LastfmProfile:
        """Fetch all profile data from Last.fm in parallel."""
        top_artists, top_albums, top_tags, recent_tracks, loved_tracks, weekly_artists = await asyncio.gather(
            self.client.get_top_artists(username),
            self.client.get_top_albums(username),
            self.client.get_top_tags(username),
            self.client.get_recent_tracks(username),
            self.client.get_loved_tracks(username),
            self.client.get_weekly_artist_chart(username),
        )
        return LastfmProfile(
            top_artists=top_artists,
            top_albums=top_albums,
            top_tags=top_tags,
            recent_tracks=recent_tracks,
            loved_tracks=loved_tracks,
            weekly_artists=weekly_artists,
        )

    async def get_full_profile(self, username: str) -> LastfmProfile:
        """Return the user's aggregated Last.fm profile, using cache if available."""
        cache_key = f"lastfm:profile:{username}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return LastfmProfile.model_validate(cached_data)

        profile = await self._fetch_profile(username)
        await self.cache.set(cache_key, profile.model_dump(), ttl_seconds=3600)
        return profile

    async def refresh_profile(self, username: str) -> LastfmProfile:
        """Force-refresh a user's Last.fm profile, bypassing the cache."""
        cache_key = f"lastfm:profile:{username}"
        await self.cache.invalidate(cache_key)
        profile = await self._fetch_profile(username)
        await self.cache.set(cache_key, profile.model_dump(), ttl_seconds=3600)
        return profile

    async def enrich_artist(self, artist_name: str) -> dict:
        """Fetch basic artist info for discovery enrichment."""
        return await self.client.get_artist_info(artist_name)
