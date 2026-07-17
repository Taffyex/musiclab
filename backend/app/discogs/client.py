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
        try:
            response = await self._http.get("/database/search", params={"q": name, "type": "artist"})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Discogs", message=str(e)) from e

    async def get_artist(self, artist_id: int) -> dict:
        """Get full artist details by Discogs ID.

        Endpoint: ``GET /artists/{artist_id}``
        """
        try:
            response = await self._http.get(f"/artists/{artist_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Discogs", message=str(e)) from e

    async def get_artist_releases(
        self, artist_id: int, limit: int = 10
    ) -> list[dict]:
        """Get releases for an artist.

        Endpoint: ``GET /artists/{artist_id}/releases``
        """
        try:
            response = await self._http.get(f"/artists/{artist_id}/releases", params={"per_page": limit})
            response.raise_for_status()
            data = response.json()
            return data.get("releases", [])
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Discogs", message=str(e)) from e

    # ------------------------------------------------------------------

    async def get_release(self, release_id: int) -> dict:
        """Fetch full release details including extraartists (credits).
        
        Endpoint: ``GET /releases/{release_id}``
        """
        try:
            response = await self._http.get(f"/releases/{release_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Discogs", message=str(e)) from e

    async def search_by_style(self, style: str, page: int = 1, per_page: int = 20) -> dict:
        """Search releases/artists by Discogs style.
        
        Endpoint: ``GET /database/search?style={style}&type=artist``
        """
        try:
            response = await self._http.get(
                "/database/search", 
                params={"style": style, "type": "artist", "page": page, "per_page": per_page}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Discogs", message=str(e)) from e

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
