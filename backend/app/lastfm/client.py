"""Async HTTP client for the Last.fm API."""

from __future__ import annotations

import httpx


class LastfmClient:
    """Async client wrapping the Last.fm Web Services API (JSON).

    Usage::

        async with LastfmClient(api_key="...") as client:
            artists = await client.get_top_artists("username")
    """

    BASE_URL: str = "https://ws.audioscrobbler.com/2.0/"

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
        query = {"method": method, "api_key": self.api_key, "format": "json"}
        if params:
            query.update(params)
            
        try:
            response = await self._http.get("", params=query)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Last.fm", message=str(e.response.status_code)) from e
        except httpx.RequestError as e:
            from app.common.exceptions import ExternalAPIError
            raise ExternalAPIError(service="Last.fm", message=str(e)) from e

    # ------------------------------------------------------------------
    # User methods
    # ------------------------------------------------------------------

    async def get_top_artists(
        self, user: str, period: str = "overall", limit: int = 50
    ) -> list[dict]:
        """Fetch top artists for a user.

        Last.fm method: ``user.getTopArtists``
        """
        params = {"user": user, "period": period, "limit": limit}
        data = await self._request("user.getTopArtists", params)
        return data.get("topartists", {}).get("artist", [])

    async def get_top_albums(
        self, user: str, period: str = "overall", limit: int = 50
    ) -> list[dict]:
        """Fetch top albums for a user.

        Last.fm method: ``user.getTopAlbums``
        """
        params = {"user": user, "period": period, "limit": limit}
        data = await self._request("user.getTopAlbums", params)
        return data.get("topalbums", {}).get("album", [])

    async def get_top_tags(self, user: str) -> list[dict]:
        """Fetch top tags for a user.

        Last.fm method: ``user.getTopTags``
        """
        params = {"user": user}
        data = await self._request("user.getTopTags", params)
        return data.get("toptags", {}).get("tag", [])

    async def get_recent_tracks(self, user: str, limit: int = 50) -> list[dict]:
        """Fetch recently played tracks for a user.

        Last.fm method: ``user.getRecentTracks``
        """
        params = {"user": user, "limit": limit}
        data = await self._request("user.getRecentTracks", params)
        return data.get("recenttracks", {}).get("track", [])

    async def get_loved_tracks(self, user: str, limit: int = 50) -> list[dict]:
        """Fetch loved tracks for a user.

        Last.fm method: ``user.getLovedTracks``
        """
        params = {"user": user, "limit": limit}
        data = await self._request("user.getLovedTracks", params)
        return data.get("lovedtracks", {}).get("track", [])

    async def get_weekly_artist_chart(self, user: str) -> list[dict]:
        """Fetch current weekly artist chart for a user.

        Last.fm method: ``user.getWeeklyArtistChart``
        """
        params = {"user": user}
        data = await self._request("user.getWeeklyArtistChart", params)
        return data.get("weeklyartistchart", {}).get("artist", [])

    # ------------------------------------------------------------------
    # Artist methods
    # ------------------------------------------------------------------

    async def get_similar_artists(
        self, artist: str, limit: int = 20
    ) -> list[dict]:
        """Fetch artists similar to the given artist.

        Last.fm method: ``artist.getSimilar``
        """
        params = {"artist": artist, "limit": limit, "autocorrect": 1}
        data = await self._request("artist.getSimilar", params)
        return data.get("similarartists", {}).get("artist", [])

    async def get_artist_top_tags(self, artist: str) -> list[dict]:
        """Fetch top tags applied to an artist.

        Last.fm method: ``artist.getTopTags``
        """
        params = {"artist": artist, "autocorrect": 1}
        data = await self._request("artist.getTopTags", params)
        return data.get("toptags", {}).get("tag", [])

    # ------------------------------------------------------------------

    async def get_artist_info(self, artist: str) -> dict:
        """Fetch artist info including listeners, playcount, bio, and tags.

        Last.fm method: ``artist.getInfo``
        """
        params = {"artist": artist, "autocorrect": 1}
        data = await self._request("artist.getInfo", params)
        return data.get("artist", {})

    async def get_tag_top_artists(self, tag: str, page: int = 1, limit: int = 50) -> list[dict]:
        """Fetch top artists for a tag.

        Last.fm method: ``tag.getTopArtists``
        """
        params = {"tag": tag, "page": page, "limit": limit}
        data = await self._request("tag.getTopArtists", params)
        return data.get("topartists", {}).get("artist", [])

    async def get_global_top_tags(self, limit: int = 50) -> list[dict]:
        """Fetch global top tags.

        Last.fm method: ``tag.getTopTags``
        """
        params = {"limit": limit}
        data = await self._request("tag.getTopTags", params)
        return data.get("toptags", {}).get("tag", [])

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
