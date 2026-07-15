"""FastAPI router for discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.discovery.schemas import DiscoveryBatch, DiscoveryCard, ExploreRequest

router = APIRouter(prefix="/discovery", tags=["discovery"])

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.config import settings
from app.discovery.service import DiscoveryService
from app.lastfm.client import LastfmClient
from app.lastfm.service import LastfmService
from app.discogs.client import DiscogsClient
from app.discogs.service import DiscogsService
from app.musicbrainz.client import MusicBrainzClient
from app.musicbrainz.service import MusicBrainzService
from app.lidarr.client import LidarrClient
from app.lidarr.service import LidarrService
from app.llm.router import get_llm_provider
from app.cache.service import CacheService
import aiosqlite

def get_discovery_service(
    db: aiosqlite.Connection = Depends(get_db),
    llm = Depends(get_llm_provider)
) -> DiscoveryService:
    cache = CacheService(db=db)
    
    lastfm_client = LastfmClient(api_key=settings.lastfm_api_key)
    lastfm = LastfmService(client=lastfm_client, cache=cache, db=db)
    
    discogs_client = DiscogsClient(token=settings.discogs_token)
    discogs = DiscogsService(client=discogs_client)
    
    mb_client = MusicBrainzClient()
    mb = MusicBrainzService(client=mb_client)
    
    lidarr_client = LidarrClient(base_url=settings.lidarr_url, api_key=settings.lidarr_api_key)
    lidarr = LidarrService(client=lidarr_client)
    
    return DiscoveryService(
        lastfm=lastfm,
        discogs=discogs,
        musicbrainz=mb,
        lidarr=lidarr,
        llm=llm,
        cache=cache,
        db=db
    )

@router.post("/generate", response_model=DiscoveryBatch)
async def generate_discovery(
    count: int = 8,
    current_user: dict = Depends(get_current_user),
    service: DiscoveryService = Depends(get_discovery_service)
) -> DiscoveryBatch:
    """Generate a new batch of music discovery recommendations."""
    return await service.generate_batch(user_id=current_user["id"], count=count)


@router.get("/explore/{artist_name}", response_model=list[DiscoveryCard])
async def explore_artist(
    artist_name: str, count: int = 5,
    current_user: dict = Depends(get_current_user),
    service: DiscoveryService = Depends(get_discovery_service)
) -> list[DiscoveryCard]:
    """Explore artists similar to the given seed artist."""
    return await service.explore_similar(user_id=current_user["id"], artist_name=artist_name, count=count)


@router.get("/history", response_model=list[DiscoveryBatch])
async def get_history(
    current_user: dict = Depends(get_current_user),
    service: DiscoveryService = Depends(get_discovery_service)
) -> list[DiscoveryBatch]:
    """Return past discovery batches for the user."""
    return await service.get_history(user_id=current_user["id"])
