"""Lidarr business-logic service layer."""

from __future__ import annotations

from app.lidarr.client import LidarrClient
from app.lidarr.schemas import AddArtistRequest, LidarrArtist


class LidarrService:
    """High-level service for interacting with the Lidarr library."""

    def __init__(self, client: LidarrClient) -> None:
        self.client = client

    async def get_library(self) -> list[LidarrArtist]:
        """Return all artists currently in the Lidarr library.

        Returns:
            A list of :class:`LidarrArtist` objects.
        """
        # TODO: Fetch artists via client.get_artists()
        # TODO: Map each dict to LidarrArtist
        raise NotImplementedError

    async def get_library_artist_names(self) -> set[str]:
        """Return a set of artist names in the library.

        Useful for excluding already-owned artists from discovery results.

        Returns:
            A set of lowercased artist name strings.
        """
        # TODO: Fetch library, extract and normalize names
        raise NotImplementedError

    async def add_artist_to_library(
        self, request: AddArtistRequest
    ) -> LidarrArtist:
        """Add an artist to the Lidarr library.

        Args:
            request: The add-artist payload.

        Returns:
            The newly created :class:`LidarrArtist`.
        """
        # TODO: Serialize request to dict
        # TODO: Call client.add_artist(data)
        # TODO: Map response to LidarrArtist
        raise NotImplementedError

    async def search_and_add(
        self,
        artist_name: str,
        quality_profile_id: int,
        root_folder: str,
    ) -> LidarrArtist:
        """Search for an artist in Lidarr's lookup and add the best match.

        Args:
            artist_name: Name to search for.
            quality_profile_id: The quality profile to apply.
            root_folder: Root folder path for the artist's files.

        Returns:
            The newly added :class:`LidarrArtist`.
        """
        # TODO: Search via client.search_artist(artist_name)
        # TODO: Pick best match from results
        # TODO: Build AddArtistRequest from match data
        # TODO: Call self.add_artist_to_library(request)
        raise NotImplementedError
