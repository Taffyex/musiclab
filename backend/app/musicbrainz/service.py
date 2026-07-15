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
            aliases=aliases,
            tags=tags
        )

    async def get_related_artists(
        self, artist_name: str
    ) -> list[MBArtist]:
        """Return artists related to the given artist via MusicBrainz relations.

        Args:
            artist_name: The artist name to look up.

        Returns:
            A list of related :class:`MBArtist` objects.
        """
        artists = await self.client.search_artist(artist_name)
        if not artists:
            return []
            
        best_match = max(artists, key=lambda a: int(a.get("score", 0)))
        details = await self.client.get_artist(best_match["id"], includes=["artist-rels"])
        
        relations = details.get("relations", [])
        related_mbids = [rel.get("artist", {}).get("id") for rel in relations if rel.get("target-type") == "artist"]
        
        related_artists = []
        for mbid in related_mbids:
            if not mbid:
                continue
            import asyncio
            await asyncio.sleep(1) # Respect 1 req/sec limit
            try:
                rel_details = await self.client.get_artist(mbid, includes=["tags"])
                aliases = [alias.get("name", "") for alias in rel_details.get("aliases", [])]
                tags = [tag.get("name", "") for tag in rel_details.get("tags", [])]
                related_artists.append(MBArtist(
                    mbid=rel_details.get("id", ""),
                    name=rel_details.get("name", ""),
                    country=rel_details.get("country", ""),
                    aliases=aliases,
                    tags=tags
                ))
            except Exception:
                pass
        return related_artists
