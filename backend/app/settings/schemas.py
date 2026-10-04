"""Schemas for settings module."""

from __future__ import annotations

from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    lastfm_username: str | None = None
    lastfm_api_key: str | None = None
    lidarr_url: str | None = None
    lidarr_api_key: str | None = None
    llm_provider: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None
