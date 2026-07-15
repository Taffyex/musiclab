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
        artists_data = await self.client.get_artists()
        artists = []
        for a in artists_data:
            artists.append(LidarrArtist(
                id=a.get("id", 0),
                name=a.get("artistName", ""),
                foreign_artist_id=a.get("foreignArtistId", ""),
                monitored=a.get("monitored", True),
                quality_profile_id=a.get("qualityProfileId", 0),
                path=a.get("path", "")
            ))
        return artists

    async def get_library_artist_names(self) -> set[str]:
        """Return a set of artist names in the library.

        Useful for excluding already-owned artists from discovery results.

        Returns:
            A set of lowercased artist name strings.
        """
        artists = await self.get_library()
        return {a.name.lower() for a in artists}

    async def add_artist_to_library(
        self, request: AddArtistRequest
    ) -> LidarrArtist:
        """Add an artist to the Lidarr library.

        Args:
            request: The add-artist payload.

        Returns:
            The newly created :class:`LidarrArtist`.
        """
        data = {
            "artistName": request.name,
            "foreignArtistId": request.foreign_artist_id,
            "qualityProfileId": request.quality_profile_id,
            "rootFolderPath": request.root_folder_path,
            "monitored": request.monitored,
            "addOptions": {
                "searchForMissingAlbums": request.monitored
            }
        }
        res = await self.client.add_artist(data)
        return LidarrArtist(
            id=res.get("id", 0),
            name=res.get("artistName", ""),
            foreign_artist_id=res.get("foreignArtistId", ""),
            monitored=res.get("monitored", True),
            quality_profile_id=res.get("qualityProfileId", 0),
            path=res.get("path", "")
        )

