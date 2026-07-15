"""
MusicLab — Authentication router.

Endpoints for login, logout, and retrieving the current user.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

import aiosqlite

from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """
    Authenticate a user with username and password (form data).

    Sets an HTTP-only session cookie on success.
    """
    from fastapi import HTTPException, status
    from app.auth import service
    from app.config import settings

    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password required")

    async with db.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,)) as cursor:
        user = await cursor.fetchone()

    if not user or not service.verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = await service.create_session(db, user["id"])
    response.set_cookie(key="session", value=token, httponly=True, secure=settings.environment == 'production', samesite="lax", max_age=7*24*60*60)
    return {"message": "Logged in successfully"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """
    Invalidate the current session and clear the session cookie.
    """
    from app.auth import service
    
    token = request.cookies.get("session")
    if token:
        await service.invalidate_session(db, token)
    response.delete_cookie("session")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Return info about the currently authenticated user.
    """
    # The user dict is already sanitized by get_current_user
    return {"user": current_user}
