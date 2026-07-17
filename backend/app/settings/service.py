"""Settings persistence service."""

from __future__ import annotations

from pathlib import Path

from dotenv import set_key

from app.config import settings as app_settings

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def mask_key(key: str | None) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * 8
    return f"{key[:4]}{'*' * 4}{key[-4:]}"


def is_masked(key: str | None) -> bool:
    return bool(key and "****" in key)


class SettingsService:
    """Handles reading and writing settings, masking secrets on read."""

    def get_settings(self, current_user: dict) -> dict:
        return {
            "lastfm_username": current_user.get("lastfm_username", "") or "",
            "lastfm_api_key": mask_key(app_settings.lastfm_api_key),
            "lidarr_url": app_settings.lidarr_url,
            "lidarr_api_key": mask_key(app_settings.lidarr_api_key),
            "llm_provider": current_user.get("llm_provider", app_settings.llm_provider),
            "anthropic_api_key": mask_key(app_settings.anthropic_api_key),
            "openai_api_key": mask_key(app_settings.openai_api_key),
            "deepseek_api_key": mask_key(app_settings.deepseek_api_key),
        }

    def apply_updates(self, updates: dict[str, str | None]) -> None:
        """Persist non-masked values to .env and update the runtime settings."""
        env_writes: dict[str, str] = {}

        for field, env_key in [
            ("lastfm_api_key", "LASTFM_API_KEY"),
            ("lidarr_url", "LIDARR_URL"),
            ("lidarr_api_key", "LIDARR_API_KEY"),
            ("anthropic_api_key", "ANTHROPIC_API_KEY"),
            ("openai_api_key", "OPENAI_API_KEY"),
            ("deepseek_api_key", "DEEPSEEK_API_KEY"),
        ]:
            value = updates.get(field)
            if value is not None and not is_masked(value):
                env_writes[env_key] = value

        for env_key, value in env_writes.items():
            set_key(str(_ENV_PATH), env_key, value)

        # Update runtime settings
        if "lastfm_api_key" in env_writes:
            app_settings.lastfm_api_key = env_writes["LASTFM_API_KEY"]
        if "lidarr_url" in env_writes:
            app_settings.lidarr_url = env_writes["LIDARR_URL"]
        if "lidarr_api_key" in env_writes:
            app_settings.lidarr_api_key = env_writes["LIDARR_API_KEY"]
        if "anthropic_api_key" in env_writes:
            app_settings.anthropic_api_key = env_writes["ANTHROPIC_API_KEY"]
        if "openai_api_key" in env_writes:
            app_settings.openai_api_key = env_writes["OPENAI_API_KEY"]
        if "deepseek_api_key" in env_writes:
            app_settings.deepseek_api_key = env_writes["DEEPSEEK_API_KEY"]
