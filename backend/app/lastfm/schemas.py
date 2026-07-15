"""Last.fm Pydantic schemas for API data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LastfmArtist(BaseModel):
    """A Last.fm artist with play statistics."""

    name: str
    playcount: int = 0
    url: str = ""
    image_url: str = ""


class LastfmAlbum(BaseModel):
    """A Last.fm album with play statistics."""

    name: str
    artist: str
    playcount: int = 0
    url: str = ""
    image_url: str = ""


class LastfmTrack(BaseModel):
    """A Last.fm track, typically from recent/loved tracks."""

    name: str
    artist: str
    album: str = ""
    timestamp: int | None = None
    url: str = ""


class LastfmTag(BaseModel):
    """A Last.fm tag with usage count."""

    name: str
    count: int = 0


class LastfmProfile(BaseModel):
    """Aggregated Last.fm profile data for a user."""

    top_artists: list[LastfmArtist] = Field(default_factory=list)
    top_albums: list[LastfmAlbum] = Field(default_factory=list)
    top_tags: list[LastfmTag] = Field(default_factory=list)
    recent_tracks: list[LastfmTrack] = Field(default_factory=list)
    loved_tracks: list[LastfmTrack] = Field(default_factory=list)
    weekly_artists: list[LastfmArtist] = Field(default_factory=list)
