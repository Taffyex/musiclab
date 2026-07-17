"""Async HTTP client for the Lidarr API."""

from __future__ import annotations

import httpx

from app.common.exceptions import ExternalAPIError
from app.common.http import BaseHttpClient


class LidarrClient(BaseHttpClient):
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
            headers={"X-Api-Key": self.api_key, "Accept": "application/json"},
        )

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        """Send a request to the Lidarr API."""
        try:
            response = await self._http.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ExternalAPIError(service="Lidarr", message=str(e)) from e

    async def get_artists(self) -> list[dict]:
        return await self._request("GET", "/api/v1/artist")

    async def get_artist(self, artist_id: int) -> dict:
        return await self._request("GET", f"/api/v1/artist/{artist_id}")

    async def add_artist(self, data: dict) -> dict:
        return await self._request("POST", "/api/v1/artist", json=data)

    async def search_artist(self, term: str) -> list[dict]:
        return await self._request("GET", "/api/v1/artist/lookup", params={"term": term})

    async def get_quality_profiles(self) -> list[dict]:
        return await self._request("GET", "/api/v1/qualityprofile")

    async def get_root_folders(self) -> list[dict]:
        return await self._request("GET", "/api/v1/rootfolder")
