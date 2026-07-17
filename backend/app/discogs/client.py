"""Async HTTP client for the Discogs API."""

from __future__ import annotations

import httpx

from app.common.exceptions import ExternalAPIError
from app.common.http import BaseHttpClient


class DiscogsClient(BaseHttpClient):
    """Async client for the Discogs REST API.

    Usage::

        async with DiscogsClient(token="...") as client:
            results = await client.search_artist("Radiohead")
    """

    BASE_URL: str = "https://api.discogs.com"

    def __init__(self, token: str) -> None:
        self.token = token
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Discogs token={self.token}",
                "User-Agent": "MusicLab/0.1",
                "Accept": "application/json",
            },
        )

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        """Send a request to the Discogs API."""
        try:
            response = await self._http.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ExternalAPIError(service="Discogs", message=str(e)) from e

    async def search_artist(self, name: str) -> dict:
        return await self._request("GET", "/database/search", params={"q": name, "type": "artist"})

    async def get_artist(self, artist_id: int) -> dict:
        return await self._request("GET", f"/artists/{artist_id}")

    async def get_artist_releases(self, artist_id: int, limit: int = 10) -> list[dict]:
        data = await self._request("GET", f"/artists/{artist_id}/releases", params={"per_page": limit})
        return data.get("releases", [])

    async def get_release(self, release_id: int) -> dict:
        return await self._request("GET", f"/releases/{release_id}")

    async def search_by_style(self, style: str, page: int = 1, per_page: int = 20) -> dict:
        return await self._request(
            "GET", "/database/search",
            params={"style": style, "type": "artist", "page": page, "per_page": per_page},
        )
