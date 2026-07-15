"""Async HTTP client for the Discogs API."""

from __future__ import annotations

import httpx


class DiscogsClient:
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

    async def search_artist(self, name: str) -> dict:
        """Search for an artist by name.

        Endpoint: ``GET /database/search?q={name}&type=artist``
        """
        # TODO: Build query params and call self._http.get(...)
        # TODO: Return parsed JSON
        raise NotImplementedError

    async def get_artist(self, artist_id: int) -> dict:
        """Get full artist details by Discogs ID.

        Endpoint: ``GET /artists/{artist_id}``
        """
        # TODO: Call self._http.get(f"/artists/{artist_id}")
        # TODO: Return parsed JSON
        raise NotImplementedError

    async def get_artist_releases(
        self, artist_id: int, limit: int = 10
    ) -> list[dict]:
        """Get releases for an artist.

        Endpoint: ``GET /artists/{artist_id}/releases``
        """
        # TODO: Call self._http.get(...) with per_page=limit
        # TODO: Extract releases list from response
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "DiscogsClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
