"""Discogs business-logic service layer."""

from __future__ import annotations

from app.discogs.client import DiscogsClient
from app.discogs.schemas import DiscogsArtist, DiscogsRelease


class DiscogsService:
    """High-level service for enriching artist data via Discogs."""

    def __init__(self, client: DiscogsClient) -> None:
        self.client = client

    async def enrich_artist(self, artist_name: str) -> DiscogsArtist | None:
        """Search Discogs for an artist and return structured data.

        Args:
            artist_name: The artist name to search for.

        Returns:
            A :class:`DiscogsArtist` if found, else ``None``.
        """
        search_results = await self.client.search_artist(artist_name)
        results = search_results.get("results", [])
        if not results:
            return None
        
        # Pick the exact match or first result
        best_match = next((r for r in results if r.get("title", "").lower() == artist_name.lower()), results[0])
        
        details = await self.client.get_artist(best_match["id"])
        
        return DiscogsArtist(
            name=details.get("name", ""),
            profile=details.get("profile", "")
        )

    async def get_key_releases(
        self, artist_name: str
    ) -> list[DiscogsRelease]:
        """Return notable releases for an artist.

        Args:
            artist_name: The artist name to look up.

        Returns:
            A list of :class:`DiscogsRelease` objects.
        """
        search_results = await self.client.search_artist(artist_name)
        results = search_results.get("results", [])
        if not results:
            return []
            
        best_match = next((r for r in results if r.get("title", "").lower() == artist_name.lower()), results[0])
        releases_data = await self.client.get_artist_releases(best_match["id"])
        
        releases = []
        for r in releases_data:
            releases.append(DiscogsRelease(
                title=r.get("title", ""),
                year=r.get("year", 0),
                format=r.get("type", "")
            ))
        return releases
