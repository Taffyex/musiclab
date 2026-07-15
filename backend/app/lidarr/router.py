"""FastAPI router for Lidarr endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.lidarr.schemas import AddArtistRequest, LidarrArtist

router = APIRouter()

from app.auth.dependencies import get_current_user
from app.config import settings
from app.lidarr.client import LidarrClient
from app.lidarr.service import LidarrService

def get_lidarr_service() -> LidarrService:
    client = LidarrClient(base_url=settings.lidarr_url, api_key=settings.lidarr_api_key)
    return LidarrService(client=client)

@router.get("/library", response_model=list[LidarrArtist])
async def list_library(
    current_user: dict = Depends(get_current_user),
    service: LidarrService = Depends(get_lidarr_service)
) -> list[LidarrArtist]:
    """List all artists in the Lidarr library."""
    return await service.get_library()


@router.post("/add", response_model=LidarrArtist)
async def add_artist(
    request: AddArtistRequest,
    current_user: dict = Depends(get_current_user),
    service: LidarrService = Depends(get_lidarr_service)
) -> LidarrArtist:
    """Add an artist to the Lidarr library."""
    return await service.add_artist_to_library(request)


@router.get("/profiles")
async def list_quality_profiles(
    current_user: dict = Depends(get_current_user),
    service: LidarrService = Depends(get_lidarr_service)
) -> list[dict]:
    """List available Lidarr quality profiles."""
    return await service.client.get_quality_profiles()


@router.get("/root-folders")
async def list_root_folders(
    current_user: dict = Depends(get_current_user),
    service: LidarrService = Depends(get_lidarr_service)
) -> list[dict]:
    """List configured Lidarr root folders."""
    return await service.client.get_root_folders()
