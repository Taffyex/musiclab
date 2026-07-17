"""Base class for async HTTP API clients."""

from __future__ import annotations

import httpx


class BaseHttpClient:
    """Mixin providing httpx lifecycle management for API clients.

    Subclasses must set ``self._http`` to an ``httpx.AsyncClient`` in ``__init__``.
    """

    _http: httpx.AsyncClient

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "BaseHttpClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
