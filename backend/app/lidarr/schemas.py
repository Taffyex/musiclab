"""Lidarr Pydantic schemas for API data models."""

from __future__ import annotations

from pydantic import BaseModel


class LidarrArtist(BaseModel):
    """An artist entry in the Lidarr library."""

    id: int
    name: str
    foreign_artist_id: str
    monitored: bool = True
    quality_profile_id: int = 0
    path: str = ""


class AddArtistRequest(BaseModel):
    """Request payload for adding an artist to Lidarr."""

    name: str
    foreign_artist_id: str
    quality_profile_id: int
    root_folder_path: str
    monitored: bool = True
