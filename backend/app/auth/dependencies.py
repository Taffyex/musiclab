"""
MusicLab — Auth dependencies for FastAPI dependency injection.

Provides ``get_current_user`` which extracts and validates the session
token from an HTTP-only cookie, returning the authenticated user dict.
"""

from fastapi import Cookie, Depends, HTTPException, status

import aiosqlite

from app.database import get_db


async def get_current_user(
    session_token: str | None = Cookie(default=None, alias="session"),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """
    FastAPI dependency that resolves the current authenticated user.

    Reads the ``session`` cookie, looks up the token in the sessions
    table, checks expiry, and returns the associated user row as a dict.

    Raises:
        HTTPException 401: if the cookie is missing, the session is
            expired, or the token is not found.
    """
    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # TODO: query sessions table joined with users to get user row
    #   SELECT u.id, u.username, u.lastfm_username, u.llm_provider, s.expires_at
    #   FROM sessions s JOIN users u ON s.user_id = u.id
    #   WHERE s.token = ?

    # TODO: check that session has not expired (expires_at > now)

    # TODO: return user dict (without password_hash)

    # Placeholder — always raises until implemented
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated (stub)",
    )
