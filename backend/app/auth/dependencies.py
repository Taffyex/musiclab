"""
MusicLab — Auth dependencies for FastAPI dependency injection.

Provides ``get_current_user`` which extracts and validates the session
token from an HTTP-only cookie, returning the authenticated user dict.
"""

from __future__ import annotations

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

    from datetime import datetime, timezone
    
    async with db.execute(
        "SELECT u.id, u.username, u.lastfm_username, u.llm_provider, s.expires_at "
        "FROM sessions s JOIN users u ON s.user_id = u.id "
        "WHERE s.token = ?", (session_token,)
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )

    # Convert expires_at string back to datetime if necessary, assuming it was stored as ISO string
    expires_at = datetime.fromisoformat(row["expires_at"]) if isinstance(row["expires_at"], str) else row["expires_at"]
    
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    return {
        "id": row["id"],
        "username": row["username"],
        "lastfm_username": row["lastfm_username"],
        "llm_provider": row["llm_provider"]
    }
