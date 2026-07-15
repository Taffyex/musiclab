"""FastAPI router for Last.fm endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.lastfm.schemas import LastfmProfile

router = APIRouter(prefix="/lastfm", tags=["lastfm"])


@router.get("/profile", response_model=LastfmProfile)
async def get_profile() -> LastfmProfile:
    """Return the current user's Last.fm profile.

    Serves cached data when available; fetches from the API on first load.
    """
    # TODO: Resolve current user (from auth / dependency)
    # TODO: Inject LastfmService via Depends
    # TODO: Call service.get_full_profile(username)
    raise NotImplementedError


@router.post("/refresh", response_model=LastfmProfile)
async def refresh_profile() -> LastfmProfile:
    """Force-refresh the user's Last.fm profile from the API."""
    # TODO: Resolve current user
    # TODO: Inject LastfmService via Depends
    # TODO: Call service.refresh_profile(username)
    raise NotImplementedError
