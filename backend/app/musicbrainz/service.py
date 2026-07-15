"""MusicBrainz business-logic service layer."""

from __future__ import annotations

from app.musicbrainz.client import MusicBrainzClient
from app.musicbrainz.schemas import MBArtist


class MusicBrainzService:
    """High-level service for enriching artist data via MusicBrainz."""

    def __init__(self, client: MusicBrainzClient) -> None:
        self.client = client

    async def enrich_artist(self, artist_name: str) -> MBArtist | None:
        """Search MusicBrainz for an artist and return structured data.

        Args:
            artist_name: The artist name to search for.

        Returns:
            A :class:`MBArtist` if found, else ``None``.
        """
        artists = await self.client.search_artist(artist_name)
        if not artists:
            return None
        
        # Pick the best match (artists from search have a 'score' attribute, sort descending)
        best_match = max(artists, key=lambda a: int(a.get("score", 0)))
        
        details = await self.client.get_artist(best_match["id"], includes=["tags", "artist-rels"])
        
        aliases = [alias.get("name", "") for alias in details.get("aliases", [])]
        tags = [tag.get("name", "") for tag in details.get("tags", [])]
        
        return MBArtist(
            mbid=details.get("id", ""),
            name=details.get("name", ""),
            country=details.get("country", ""),
            tags=tags
        )

