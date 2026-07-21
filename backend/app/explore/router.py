"""Router for the explore module."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, Query
from typing import Any

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.discogs.client import DiscogsClient
from app.explore.schemas import (
    ArtistDetail, ArtistSummary, Credit, CreditEntity, ExploreFilters,
    GenreTree, ReleaseDetail, FavoriteRequest, UserFavorites
)
from app.explore.service import ExploreService
from app.lastfm.client import LastfmClient
from app.musicbrainz.client import MusicBrainzClient

router = APIRouter()

from collections.abc import AsyncGenerator

async def get_explore_service(db: aiosqlite.Connection = Depends(get_db)) -> AsyncGenerator[ExploreService, None]:
    """Dependency for ExploreService."""
    discogs = DiscogsClient(token=settings.discogs_token)
    lastfm = LastfmClient(api_key=settings.lastfm_api_key)
    mb = MusicBrainzClient()
    
    service = ExploreService(db, discogs, lastfm, mb)
    try:
        yield service
    finally:
        await discogs.close()
        await lastfm.close()
        await mb.close()


@router.get("/genres")
async def list_genres(
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> list[GenreTree]:
    """List all genres with style counts."""
    return await service.get_genre_tree()


@router.get("/genres/{slug}/artists")
async def list_genre_artists(
    slug: str,
    decade: str | None = Query(None),
    sort_by: str = Query("listeners"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> dict[str, Any]:
    """List artists in a genre."""
    filters = ExploreFilters(
        genre=slug, decade=decade, sort_by=sort_by,
        sort_order=sort_order, page=page, per_page=per_page
    )
    artists, total = await service.get_artists_by_genre(slug, filters)
    return {"artists": artists, "total": total}


@router.get("/styles/{slug}/artists")
async def list_style_artists(
    slug: str,
    decade: str | None = Query(None),
    sort_by: str = Query("listeners"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> dict[str, Any]:
    """List artists in a style."""
    filters = ExploreFilters(
        style=slug, decade=decade, sort_by=sort_by,
        sort_order=sort_order, page=page, per_page=per_page
    )
    artists, total = await service.get_artists_by_style(slug, filters)
    return {"artists": artists, "total": total}


@router.get("/artists/{slug}")
async def get_artist(
    slug: str,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> ArtistDetail:
    """Get full artist detail."""
    return await service.get_artist_detail(slug)


@router.get("/artists/{slug}/similar")
async def get_similar_artists(
    slug: str,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> list[ArtistSummary]:
    """Get similar artists."""
    return await service.get_similar_artists(slug)


@router.get("/artists/{slug}/releases")
async def get_artist_releases(
    slug: str,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> list[ReleaseDetail]:
    """Get artist discography."""
    return await service.get_artist_releases(slug)


@router.get("/releases/{id}/credits")
async def get_release_credits(
    id: int,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> list[Credit]:
    """Get credits for a release."""
    return await service.get_release_credits(id)


@router.get("/credits/{slug}")
async def get_credit_entity(
    slug: str,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> CreditEntity:
    """Get credit entity page."""
    return await service.get_credit_entity(slug)


@router.get("/search")
async def search_artists(
    q: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> list[ArtistSummary]:
    """Search artists by name."""
    return await service.search_artists(q)


@router.get("/favorites")
async def get_favorites(
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> UserFavorites:
    """Get all user favorites grouped by type."""
    return await service.get_user_favorites(current_user["id"])


@router.post("/favorites")
async def add_favorite(
    request: FavoriteRequest,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> dict[str, str]:
    """Add a favorite."""
    await service.add_favorite(current_user["id"], request.entity_type, request.entity_id)
    return {"status": "success"}


@router.delete("/favorites/{entity_type}/{entity_id}")
async def remove_favorite(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    service: ExploreService = Depends(get_explore_service),
) -> dict[str, str]:
    """Remove a favorite."""
    await service.remove_favorite(current_user["id"], entity_type, entity_id)
    return {"status": "success"}
