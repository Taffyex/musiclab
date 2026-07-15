"""Discovery Pydantic schemas for recommendation cards and batches."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DiscoveryCard(BaseModel):
    """A single artist recommendation card with enriched metadata."""

    id: str
    artist_name: str
    genre_tags: list[str] = Field(default_factory=list)
    era: str = ""
    ai_blurb: str = ""
    why_it_matches: str = ""
    lastfm_listeners: int | None = None
    lastfm_playcount: int | None = None
    mb_data: dict | None = None
    discogs_data: dict | None = None
    already_in_lidarr: bool = False


class DiscoveryBatch(BaseModel):
    """A batch of discovery cards generated in one session."""

    id: str
    cards: list[DiscoveryCard] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExploreRequest(BaseModel):
    """Request payload for the explore-similar endpoint."""

    artist_name: str
    depth: int = 5
