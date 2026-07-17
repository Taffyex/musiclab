"""Last.fm Pydantic schemas for API data models."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Any

class LastfmArtist(BaseModel):
    """A Last.fm artist with play statistics."""

    name: str
    playcount: int = 0
    url: str = ""
    image_url: str = ""

    @model_validator(mode="before")
    @classmethod
    def parse_artist(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "image" in data and isinstance(data["image"], list):
                images = [img.get("#text") for img in data["image"] if img.get("#text")]
                if images:
                    data["image_url"] = images[-1]
            if "name" not in data and "#text" in data:
                data["name"] = data["#text"]
        return data


class LastfmAlbum(BaseModel):
    """A Last.fm album with play statistics."""

    name: str
    artist: str
    playcount: int = 0
    url: str = ""
    image_url: str = ""

    @model_validator(mode="before")
    @classmethod
    def parse_album(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "artist" in data and isinstance(data["artist"], dict):
                data["artist"] = data["artist"].get("name") or data["artist"].get("#text") or ""
            if "image" in data and isinstance(data["image"], list):
                images = [img.get("#text") for img in data["image"] if img.get("#text")]
                if images:
                    data["image_url"] = images[-1]
        return data


class LastfmTrack(BaseModel):
    """A Last.fm track, typically from recent/loved tracks."""

    name: str
    artist: str
    album: str = ""
    timestamp: int | None = None
    url: str = ""
    
    @model_validator(mode="before")
    @classmethod
    def parse_track(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "artist" in data and isinstance(data["artist"], dict):
                data["artist"] = data["artist"].get("name") or data["artist"].get("#text") or ""
            if "album" in data and isinstance(data["album"], dict):
                data["album"] = data["album"].get("title") or data["album"].get("#text") or ""
            if "date" in data and isinstance(data["date"], dict):
                data["timestamp"] = int(data["date"].get("uts", 0))
        return data


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
