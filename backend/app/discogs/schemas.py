"""Discogs Pydantic schemas for API data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiscogsArtist(BaseModel):
    """A Discogs artist profile."""

    name: str
    profile: str = ""
    urls: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)


class DiscogsRelease(BaseModel):
    """A Discogs release (album / single / EP)."""

    title: str
    year: int | None = None
    label: str = ""
    format: str = ""
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    cover_url: str = ""
