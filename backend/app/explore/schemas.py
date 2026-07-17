"""Schemas for the explore module."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class Genre(BaseModel):
    id: int
    name: str
    slug: str
    source: str
    style_count: int = 0


class Style(BaseModel):
    id: int
    name: str
    slug: str
    genre_id: int
    genre_name: str = ""


class ArtistSummary(BaseModel):
    """Lightweight artist card for grid views."""
    id: int
    name: str
    slug: str
    image_url: str = ""
    lastfm_listeners: int | None = None
    lastfm_playcount: int | None = None
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    already_in_lidarr: bool = False


class Credit(BaseModel):
    """A single credit entry."""
    id: int
    entity_name: str
    entity_slug: str
    role: str
    entity_type: str    # 'person' | 'studio'


class ReleaseDetail(BaseModel):
    """A release with optional credits."""
    id: int
    title: str
    year: int | None = None
    release_type: str = ""
    label: str = ""
    format: str = ""
    cover_url: str = ""
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    credits: list[Credit] = Field(default_factory=list)


class ArtistDetail(BaseModel):
    """Full artist profile for detail page."""
    id: int
    name: str
    slug: str
    bio: str = ""
    discogs_profile: str = ""
    country: str = ""
    begin_date: str = ""
    end_date: str = ""
    artist_type: str = ""
    image_url: str = ""
    lastfm_listeners: int | None = None
    lastfm_playcount: int | None = None
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    mb_tags: list[str] = Field(default_factory=list)
    mb_relations: list[dict] = Field(default_factory=list)
    releases: list[ReleaseDetail] = Field(default_factory=list)
    similar_artists: list[ArtistSummary] = Field(default_factory=list)
    already_in_lidarr: bool = False
    lidarr_artist: dict | None = None


class ReleaseWithArtist(BaseModel):
    """A release shown in a credit entity context."""
    release_id: int
    title: str
    year: int | None = None
    artist_name: str
    artist_slug: str
    role: str
    cover_url: str = ""


class CreditEntity(BaseModel):
    """A producer/engineer/studio with their associated releases."""
    name: str
    slug: str
    entity_type: str
    roles: list[str] = Field(default_factory=list)
    release_count: int = 0
    releases: list[ReleaseWithArtist] = Field(default_factory=list)


class GenreTree(BaseModel):
    """Full genre with nested styles for hierarchy view."""
    genre: Genre
    styles: list[Style] = Field(default_factory=list)


class ExploreFilters(BaseModel):
    """Query parameters for filtering artists."""
    genre: str | None = None
    style: str | None = None
    decade: str | None = None          # e.g., "1970s"
    sort_by: str = "listeners"         # 'listeners' | 'scrobbles' | 'name'
    sort_order: str = "desc"           # 'asc' | 'desc'
    page: int = 1
    per_page: int = 20


class FavoriteItem(BaseModel):
    """A single favorited entity with resolved name/slug."""
    entity_type: Literal["artist", "genre", "style"]
    entity_id: int
    name: str
    slug: str
    image_url: str = ""  # populated only for artists


class UserFavorites(BaseModel):
    """All favorites for a user, grouped by entity type."""
    artists: list[FavoriteItem] = Field(default_factory=list)
    genres: list[FavoriteItem] = Field(default_factory=list)
    styles: list[FavoriteItem] = Field(default_factory=list)


class FavoriteRequest(BaseModel):
    """Request body for adding a favorite."""
    entity_type: Literal["artist", "genre", "style"]
    entity_id: int
