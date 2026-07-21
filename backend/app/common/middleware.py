"""FastAPI middleware for error handling and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict

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


# Simple in-memory sliding window rate limiter
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # seconds
RATE_LIMIT_MAX_REQUESTS = 5

async def rate_limit_middleware(request: Request, call_next):  # noqa: ANN001
    """Rate-limiting middleware for login endpoint."""
    if request.url.path == "/api/auth/login" and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean up old timestamps for this IP
        timestamps = _rate_limit_store[client_ip]
        timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
        
        if not timestamps:
            _rate_limit_store.pop(client_ip, None)
        else:
            _rate_limit_store[client_ip] = timestamps
            
        if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many login attempts. Please try again later."},
                headers={"Retry-After": str(int(RATE_LIMIT_WINDOW))}
            )
            
        timestamps.append(now)
        _rate_limit_store[client_ip] = timestamps

    response = await call_next(request)
    return response
