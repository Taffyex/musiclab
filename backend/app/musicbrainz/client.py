"""Async HTTP client for the MusicBrainz API.

.. important::

    MusicBrainz enforces a rate limit of **1 request per second**.
    All callers should respect this; consider using an async semaphore or
    ``asyncio.sleep(1)`` between consecutive calls.
"""

from __future__ import annotations

import httpx


class MusicBrainzClient:
    """Async client for the MusicBrainz Web Service v2 (JSON).

    No authentication is required, but a descriptive ``User-Agent`` header
    **must** be set per MusicBrainz policy.

    Usage::

        async with MusicBrainzClient() as client:
            results = await client.search_artist("Radiohead")

    .. warning::
        Rate limit: max 1 request/second.  Implement throttling before
        making multiple calls in a loop.
    """

    BASE_URL: str = "https://musicbrainz.org/ws/2"

    def __init__(self) -> None:
        # NOTE: MusicBrainz requires a meaningful User-Agent with contact info.
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "User-Agent": "MusicLab/0.1 (musiclab@example.com)",
                "Accept": "application/json",
            },
        )

    async def search_artist(self, name: str) -> list[dict]:
        """Search for artists matching *name*.

        Endpoint: ``GET /artist?query={name}&fmt=json``

        Rate limit: 1 req/sec — caller must throttle.
        """
        try:
            response = await self._http.get("/artist", params={"query": name, "fmt": "json"})
            response.raise_for_status()
            data = response.json()
            return data.get("artists", [])
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="MusicBrainz", message=str(e)) from e

    async def get_artist(
        self,
        mbid: str,
        includes: list[str] | None = None,
    ) -> dict:
        """Fetch a single artist by MBID with optional includes.

        Endpoint: ``GET /artist/{mbid}?inc=tags+artist-rels&fmt=json``

        Args:
            mbid: The MusicBrainz artist ID.
            includes: Sub-queries to include, e.g. ``["tags", "artist-rels"]``.
                      Defaults to ``["tags", "artist-rels"]``.
        """
        if includes is None:
            includes = ["tags", "artist-rels"]
        inc_param = "+".join(includes)
        try:
            response = await self._http.get(f"/artist/{mbid}", params={"inc": inc_param, "fmt": "json"})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="MusicBrainz", message=str(e)) from e

    async def get_artist_releases(
        self, mbid: str, limit: int = 10
    ) -> list[dict]:
        """Fetch releases for an artist.

        Endpoint: ``GET /release?artist={mbid}&limit={limit}&fmt=json``

        Rate limit: 1 req/sec — caller must throttle.
        """
        try:
            response = await self._http.get("/release", params={"artist": mbid, "limit": limit, "fmt": "json"})
            response.raise_for_status()
            data = response.json()
            return data.get("releases", [])
        except httpx.HTTPError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="MusicBrainz", message=str(e)) from e

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "MusicBrainzClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
