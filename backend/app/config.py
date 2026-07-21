"""
MusicLab — Application configuration via environment variables.

Uses pydantic-settings to load and validate all config from .env file
or environment variables at startup.
"""

from __future__ import annotations

import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Central configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ─── Application ───
    environment: str = "development"
    app_secret_key: str = "change-me-to-a-random-string"
    cors_origins: str = "http://localhost:5173"
    
    @field_validator("app_secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "change-me-to-a-random-string":
            warnings.warn("Using default app_secret_key. Must change app_secret_key from default for production.")
        return v

    # ─── Last.fm ───
    lastfm_api_key: str = ""
    lastfm_username: str = ""

    # ─── Lidarr ───
    lidarr_url: str = ""
    lidarr_api_key: str = ""

    # LLM Settings
    llm_provider: str = "openai"  # openai, deepseek
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # ─── Discogs ───
    discogs_token: str = ""

    # ─── Auth Defaults ───
    auth_username: str = "admin"
    auth_password_hash: str = ""


# Singleton instance — import this wherever config is needed
settings = Settings()
