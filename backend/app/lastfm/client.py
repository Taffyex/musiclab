"""Async HTTP client for the Last.fm API."""

from __future__ import annotations

import httpx


class LastfmClient:
    """Async client wrapping the Last.fm Web Services API (JSON).

    Usage::

        async with LastfmClient(api_key="...") as client:
            artists = await client.get_top_artists("username")
    """

    BASE_URL: str = "http://ws.audioscrobbler.com/2.0/"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={"Accept": "application/json"},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request(self, method: str, params: dict | None = None) -> dict:
        """Send a request to the Last.fm API.

        Args:
            method: The Last.fm API method name (e.g. ``user.getTopArtists``).
            params: Extra query parameters beyond *method*, *api_key*, and *format*.

        Returns:
            Parsed JSON response as a dict.
        """
        # TODO: Build query params with api_key, method, format=json
        # TODO: Make GET request via self._http
        # TODO: Raise ExternalAPIError on non-2xx status
        # TODO: Parse and return JSON
        raise NotImplementedError

    # ------------------------------------------------------------------
    # User methods
    # ------------------------------------------------------------------

    async def get_top_artists(
        self, user: str, period: str = "overall", limit: int = 50
    ) -> list[dict]:
        """Fetch top artists for a user.

        Last.fm method: ``user.getTopArtists``
        """
        # TODO: Call self._request("user.getTopArtists", {...})
        # TODO: Extract artist list from response
        raise NotImplementedError

    async def get_top_albums(
        self, user: str, period: str = "overall", limit: int = 50
    ) -> list[dict]:
        """Fetch top albums for a user.

        Last.fm method: ``user.getTopAlbums``
        """
        # TODO: Call self._request("user.getTopAlbums", {...})
        # TODO: Extract album list from response
        raise NotImplementedError

    async def get_top_tags(self, user: str) -> list[dict]:
        """Fetch top tags for a user.

        Last.fm method: ``user.getTopTags``
        """
        # TODO: Call self._request("user.getTopTags", {...})
        # TODO: Extract tag list from response
        raise NotImplementedError

    async def get_recent_tracks(self, user: str, limit: int = 50) -> list[dict]:
        """Fetch recently played tracks for a user.

        Last.fm method: ``user.getRecentTracks``
        """
        # TODO: Call self._request("user.getRecentTracks", {...})
        # TODO: Extract track list from response
        raise NotImplementedError

    async def get_loved_tracks(self, user: str, limit: int = 50) -> list[dict]:
        """Fetch loved tracks for a user.

        Last.fm method: ``user.getLovedTracks``
        """
        # TODO: Call self._request("user.getLovedTracks", {...})
        # TODO: Extract track list from response
        raise NotImplementedError

    async def get_weekly_artist_chart(self, user: str) -> list[dict]:
        """Fetch current weekly artist chart for a user.

        Last.fm method: ``user.getWeeklyArtistChart``
        """
        # TODO: Call self._request("user.getWeeklyArtistChart", {...})
        # TODO: Extract artist list from response
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Artist methods
    # ------------------------------------------------------------------

    async def get_similar_artists(
        self, artist: str, limit: int = 20
    ) -> list[dict]:
        """Fetch artists similar to the given artist.

        Last.fm method: ``artist.getSimilar``
        """
        # TODO: Call self._request("artist.getSimilar", {...})
        # TODO: Extract similar-artist list from response
        raise NotImplementedError

    async def get_artist_top_tags(self, artist: str) -> list[dict]:
        """Fetch top tags applied to an artist.

        Last.fm method: ``artist.getTopTags``
        """
        # TODO: Call self._request("artist.getTopTags", {...})
        # TODO: Extract tag list from response
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "LastfmClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
