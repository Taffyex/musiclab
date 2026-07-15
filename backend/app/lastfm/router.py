"""FastAPI router for Last.fm endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.lastfm.schemas import LastfmProfile

router = APIRouter(prefix="/lastfm", tags=["lastfm"])

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.config import settings
from app.lastfm.client import LastfmClient
from app.cache.service import CacheService
from app.lastfm.service import LastfmService
import aiosqlite

async def get_lastfm_service(db: aiosqlite.Connection = Depends(get_db)) -> LastfmService:
    client = LastfmClient(api_key=settings.lastfm_api_key)
    cache = CacheService(db=db)
    return LastfmService(client=client, cache=cache, db=db)

@router.get("/profile", response_model=LastfmProfile)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    service: LastfmService = Depends(get_lastfm_service)
) -> LastfmProfile:
    """Return the current user's Last.fm profile.

    Serves cached data when available; fetches from the API on first load.
    """
    lastfm_username = current_user.get("lastfm_username") or settings.lastfm_username
    if not lastfm_username:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Last.fm username not configured")
    return await service.get_full_profile(lastfm_username)


@router.post("/refresh", response_model=LastfmProfile)
async def refresh_profile(
    current_user: dict = Depends(get_current_user),
    service: LastfmService = Depends(get_lastfm_service)
) -> LastfmProfile:
    """Force-refresh the user's Last.fm profile from the API."""
    lastfm_username = current_user.get("lastfm_username") or settings.lastfm_username
    if not lastfm_username:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Last.fm username not configured")
    return await service.refresh_profile(lastfm_username)
