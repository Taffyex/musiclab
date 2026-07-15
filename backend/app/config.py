"""
MusicLab — Application configuration via environment variables.

Uses pydantic-settings to load and validate all config from .env file
or environment variables at startup.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ─── Application ───
    app_secret_key: str = "change-me-to-a-random-string"

    # ─── Last.fm ───
    lastfm_api_key: str = ""
    lastfm_username: str = ""

    # ─── Lidarr ───
    lidarr_url: str = ""
    lidarr_api_key: str = ""

    # ─── LLM Provider ───
    llm_provider: str = "anthropic"  # anthropic | openai | ollama

    anthropic_api_key: str = ""
    openai_api_key: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""

    # ─── Discogs ───
    discogs_token: str = ""

    # ─── Auth Defaults ───
    auth_username: str = "admin"
    auth_password_hash: str = ""


# Singleton instance — import this wherever config is needed
settings = Settings()
