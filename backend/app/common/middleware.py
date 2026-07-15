"""FastAPI middleware for error handling and rate limiting."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.exceptions import (
    AuthenticationError,
    ExternalAPIError,
    MusicLabError,
    NotFoundError,
    RateLimitError,
)


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI application.

    Call this during app startup::

        register_error_handlers(app)
    """

    @app.exception_handler(NotFoundError)
    async def _not_found_handler(
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message},
        )

    @app.exception_handler(AuthenticationError)
    async def _auth_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": exc.message},
        )

    @app.exception_handler(RateLimitError)
    async def _rate_limit_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        headers = {}
        if exc.retry_after is not None:
            headers["Retry-After"] = str(int(exc.retry_after))
        return JSONResponse(
            status_code=429,
            content={"detail": exc.message},
            headers=headers,
        )

    @app.exception_handler(ExternalAPIError)
    async def _external_api_handler(
        request: Request, exc: ExternalAPIError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": exc.message},
        )

    @app.exception_handler(MusicLabError)
    async def _generic_handler(
        request: Request, exc: MusicLabError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message},
        )


# ---------------------------------------------------------------------------
# Rate-limit middleware placeholder
# ---------------------------------------------------------------------------


async def rate_limit_middleware(request: Request, call_next):  # noqa: ANN001
    """Placeholder rate-limiting middleware.

    TODO:
        - Track request counts per client IP / API key
        - Use a sliding-window or token-bucket algorithm
        - Raise RateLimitError when threshold exceeded
    """
    response = await call_next(request)
    return response
