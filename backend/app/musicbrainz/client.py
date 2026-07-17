"""Async HTTP client for the MusicBrainz API.

.. important::

    MusicBrainz enforces a rate limit of **1 request per second**.
    All callers should respect this; consider using an async semaphore or
    ``asyncio.sleep(1)`` between consecutive calls.
"""

from __future__ import annotations

import httpx

from app.common.exceptions import ExternalAPIError
from app.common.http import BaseHttpClient


class MusicBrainzClient(BaseHttpClient):
    """Async client for the MusicBrainz Web Service v2 (JSON)."""

    BASE_URL: str = "https://musicbrainz.org/ws/2"

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "User-Agent": "MusicLab/0.1 (musiclab@example.com)",
                "Accept": "application/json",
            },
        )

    async def _request(self, path: str, params: dict | None = None) -> dict:
        """Send a GET request to the MusicBrainz API."""
        try:
            response = await self._http.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ExternalAPIError(service="MusicBrainz", message=str(e)) from e

    async def search_artist(self, name: str) -> list[dict]:
        data = await self._request("/artist", params={"query": name, "fmt": "json"})
        return data.get("artists", [])

    async def get_artist(self, mbid: str, includes: list[str] | None = None) -> dict:
        if includes is None:
            includes = ["tags", "artist-rels"]
        inc_param = "+".join(includes)
        return await self._request(f"/artist/{mbid}", params={"inc": inc_param, "fmt": "json"})

    async def get_artist_releases(self, mbid: str, limit: int = 10) -> list[dict]:
        data = await self._request("/release", params={"artist": mbid, "limit": limit, "fmt": "json"})
        return data.get("releases", [])

    async def get_artist_with_full_relations(self, mbid: str) -> dict:
        return await self.get_artist(mbid, includes=["tags", "artist-rels", "url-rels"])

    async def browse_artists_by_tag(self, tag: str, limit: int = 20, offset: int = 0) -> list[dict]:
        data = await self._request(
            "/artist",
            params={"query": f"tag:{tag}", "fmt": "json", "limit": limit, "offset": offset},
        )
        return data.get("artists", [])
