"""Base class for async HTTP API clients."""

from __future__ import annotations

import httpx

from app.common.exceptions import ExternalAPIError


class BaseHttpClient:
    """Mixin providing httpx lifecycle management for API clients.

    Subclasses must set ``self._http`` to an ``httpx.AsyncClient`` and
    ``self.service_name`` to a human-readable API name in ``__init__``.
    """

    _http: httpx.AsyncClient
    service_name: str = "Unknown"

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        """Send an HTTP request and return parsed JSON.

        Raises:
            ExternalAPIError: On any HTTP or network error.
        """
        try:
            response = await self._http.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ExternalAPIError(service=self.service_name, message=str(e)) from e

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "BaseHttpClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
