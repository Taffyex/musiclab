"""FastAPI router for Lidarr endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.lidarr.schemas import AddArtistRequest, LidarrArtist

router = APIRouter(prefix="/lidarr", tags=["lidarr"])


@router.get("/library", response_model=list[LidarrArtist])
async def list_library() -> list[LidarrArtist]:
    """List all artists in the Lidarr library."""
    # TODO: Inject LidarrService via Depends
    # TODO: Call service.get_library()
    raise NotImplementedError


@router.post("/add", response_model=LidarrArtist)
async def add_artist(request: AddArtistRequest) -> LidarrArtist:
    """Add an artist to the Lidarr library."""
    # TODO: Inject LidarrService via Depends
    # TODO: Call service.add_artist_to_library(request)
    raise NotImplementedError


@router.get("/profiles")
async def list_quality_profiles() -> list[dict]:
    """List available Lidarr quality profiles."""
    # TODO: Inject LidarrClient or LidarrService via Depends
    # TODO: Return quality profiles
    raise NotImplementedError


@router.get("/root-folders")
async def list_root_folders() -> list[dict]:
    """List configured Lidarr root folders."""
    # TODO: Inject LidarrClient or LidarrService via Depends
    # TODO: Return root folders
    raise NotImplementedError
