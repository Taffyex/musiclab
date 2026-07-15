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
        try:
            response = await self._http.get("/api/v1/artist")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(f"Lidarr API error: {str(e)}") from e

    async def get_artist(self, artist_id: int) -> dict:
        """Get a single artist by Lidarr ID.

        Endpoint: ``GET /api/v1/artist/{artist_id}``
        """
        try:
            response = await self._http.get(f"/api/v1/artist/{artist_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(f"Lidarr API error: {str(e)}") from e

    async def add_artist(self, data: dict) -> dict:
        """Add an artist to the Lidarr library.

        Endpoint: ``POST /api/v1/artist``
        """
        try:
            response = await self._http.post("/api/v1/artist", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(f"Lidarr API error: {str(e)}") from e

    async def search_artist(self, term: str) -> list[dict]:
        """Search for an artist in the Lidarr lookup.

        Endpoint: ``GET /api/v1/artist/lookup?term={term}``
        """
        try:
            response = await self._http.get("/api/v1/artist/lookup", params={"term": term})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(f"Lidarr API error: {str(e)}") from e

    async def get_quality_profiles(self) -> list[dict]:
        """List available quality profiles.

        Endpoint: ``GET /api/v1/qualityprofile``
        """
        try:
            response = await self._http.get("/api/v1/qualityprofile")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(f"Lidarr API error: {str(e)}") from e

    async def get_root_folders(self) -> list[dict]:
        """List configured root folders.

        Endpoint: ``GET /api/v1/rootfolder``
        """
        try:
            response = await self._http.get("/api/v1/rootfolder")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(f"Lidarr API error: {str(e)}") from e

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
