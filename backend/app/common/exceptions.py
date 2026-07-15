"""Custom exception hierarchy for MusicLab."""

from __future__ import annotations


class MusicLabError(Exception):
    """Base exception for all MusicLab application errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class ExternalAPIError(MusicLabError):
    """Raised when an external API call fails (Last.fm, Discogs, etc.)."""

    def __init__(
        self,
        service: str,
        message: str = "External API request failed",
        status_code: int | None = None,
    ) -> None:
        self.service = service
        self.status_code = status_code
        super().__init__(f"[{service}] {message} (status={status_code})")


class AuthenticationError(MusicLabError):
    """Raised when authentication or authorisation fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class NotFoundError(MusicLabError):
    """Raised when a requested resource cannot be found."""

    def __init__(self, resource: str = "Resource", identifier: str = "") -> None:
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__(msg)


class RateLimitError(MusicLabError):
    """Raised when an API rate limit is exceeded."""

    def __init__(
        self,
        service: str,
        retry_after: float | None = None,
    ) -> None:
        self.service = service
        self.retry_after = retry_after
        msg = f"[{service}] Rate limit exceeded"
        if retry_after is not None:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg)
