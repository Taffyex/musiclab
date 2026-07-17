"""MusicBrainz Pydantic schemas for API data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MBArtist(BaseModel):
    """A MusicBrainz artist entity."""

    mbid: str
    name: str
    sort_name: str = ""
    type: str = ""
    country: str = ""
    begin_date: str = ""
    end_date: str = ""
    tags: list[str] = Field(default_factory=list)
    relations: list[MBRelation] = Field(default_factory=list)


class MBRelease(BaseModel):
    """A MusicBrainz release entity."""

    mbid: str
    title: str
    date: str = ""
    country: str = ""
    label: str = ""
    format: str = ""


class MBRelation(BaseModel):
    """A MusicBrainz artist relationship."""
    type: str          # 'member of band', 'collaboration', 'influenced by', etc.
    direction: str     # 'forward' | 'backward'
    target_name: str
    target_mbid: str = ""
    begin: str = ""
    end: str = ""
    attributes: list[str] = Field(default_factory=list)
