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
        # TODO: Search for artist via client.search_artist
        # TODO: Pick best match (highest score)
        # TODO: Fetch full artist details with includes
        # TODO: Map to MBArtist schema
        raise NotImplementedError

    async def get_related_artists(
        self, artist_name: str
    ) -> list[MBArtist]:
        """Return artists related to the given artist via MusicBrainz relations.

        Args:
            artist_name: The artist name to look up.

        Returns:
            A list of related :class:`MBArtist` objects.
        """
        # TODO: Resolve artist MBID via search
        # TODO: Fetch artist with artist-rels include
        # TODO: Extract related artist MBIDs from relations
        # TODO: Fetch each related artist and map to MBArtist
        raise NotImplementedError
