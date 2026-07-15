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
        # TODO: Search for artist via client
        # TODO: Pick best match from search results
        # TODO: Fetch full artist details
        # TODO: Map to DiscogsArtist schema
        raise NotImplementedError

    async def get_key_releases(
        self, artist_name: str
    ) -> list[DiscogsRelease]:
        """Return notable releases for an artist.

        Args:
            artist_name: The artist name to look up.

        Returns:
            A list of :class:`DiscogsRelease` objects.
        """
        # TODO: Resolve artist ID via search
        # TODO: Fetch releases via client
        # TODO: Map to DiscogsRelease schemas
        raise NotImplementedError
