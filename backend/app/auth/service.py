"""
MusicLab — Authentication service layer.

Pure functions for password hashing, verification, and session
token management. No FastAPI or HTTP concerns — just business logic.
"""

import secrets
from datetime import datetime, timedelta, timezone

import aiosqlite
import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Returns:
        The bcrypt hash as a UTF-8 string.
    """
    # TODO: implement — use bcrypt.hashpw with bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    # TODO: implement — use bcrypt.checkpw
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


async def create_session(db: aiosqlite.Connection, user_id: int) -> str:
    """
    Create a new session for the given user.

    Generates a cryptographically secure token, inserts it into the
    sessions table with a 7-day expiry, and returns the token.
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # TODO: INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)
    await db.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at.isoformat()),
    )
    await db.commit()

    return token


async def invalidate_session(db: aiosqlite.Connection, token: str) -> None:
    """
    Delete a session token from the sessions table (logout).
    """
    # TODO: DELETE FROM sessions WHERE token = ?
    await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()
