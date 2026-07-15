"""
MusicLab — Authentication router.

Endpoints for login, logout, and retrieving the current user.
"""

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
    # TODO: parse username & password from form data (python-multipart)
    # TODO: query users table for matching username
    # TODO: verify password with auth.service.verify_password()
    # TODO: create session via auth.service.create_session()
    # TODO: set session cookie on response
    return {"message": "TODO: implement login"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """
    Invalidate the current session and clear the session cookie.
    """
    # TODO: extract session token from cookie
    # TODO: invalidate session via auth.service.invalidate_session()
    # TODO: delete session cookie from response
    return {"message": "TODO: implement logout"}


@router.get("/me")
async def me(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Return info about the currently authenticated user.
    """
    # TODO: return sanitized user dict (exclude password_hash)
    return {"user": current_user}
