"""Async HTTP client for the Lidarr API."""

from __future__ import annotations

import httpx


class LidarrClient:
    """Async client for the Lidarr v1 REST API.

    Usage::

        async with LidarrClient(base_url="http://localhost:8686", api_key="...") as client:
            artists = await client.get_artists()
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "X-Api-Key": self.api_key,
                "Accept": "application/json",
            },
        )

    async def get_artists(self) -> list[dict]:
        """List all artists in the Lidarr library.

        Endpoint: ``GET /api/v1/artist``
        """
        # TODO: GET /api/v1/artist
        # TODO: Return parsed JSON list
        raise NotImplementedError

    async def get_artist(self, artist_id: int) -> dict:
        """Get a single artist by Lidarr ID.

        Endpoint: ``GET /api/v1/artist/{artist_id}``
        """
        # TODO: GET /api/v1/artist/{artist_id}
        # TODO: Return parsed JSON
        raise NotImplementedError

    async def add_artist(self, data: dict) -> dict:
        """Add an artist to the Lidarr library.

        Endpoint: ``POST /api/v1/artist``
        """
        # TODO: POST /api/v1/artist with JSON body
        # TODO: Return parsed JSON response
        raise NotImplementedError

    async def search_artist(self, term: str) -> list[dict]:
        """Search for an artist in the Lidarr lookup.

        Endpoint: ``GET /api/v1/artist/lookup?term={term}``
        """
        # TODO: GET /api/v1/artist/lookup with term param
        # TODO: Return parsed JSON list
        raise NotImplementedError

    async def get_quality_profiles(self) -> list[dict]:
        """List available quality profiles.

        Endpoint: ``GET /api/v1/qualityprofile``
        """
        # TODO: GET /api/v1/qualityprofile
        # TODO: Return parsed JSON list
        raise NotImplementedError

    async def get_root_folders(self) -> list[dict]:
        """List configured root folders.

        Endpoint: ``GET /api/v1/rootfolder``
        """
        # TODO: GET /api/v1/rootfolder
        # TODO: Return parsed JSON list
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "LidarrClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
