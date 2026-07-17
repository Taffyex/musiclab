from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.settings.service import SettingsService

router = APIRouter()


class SettingsUpdate(BaseModel):
    lastfm_username: str | None = None
    lastfm_api_key: str | None = None
    lidarr_url: str | None = None
    lidarr_api_key: str | None = None
    llm_provider: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None


@router.get("")
async def get_settings(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return SettingsService().get_settings(current_user)


@router.put("")
async def update_settings(
    update: SettingsUpdate,
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    new_lastfm_username = update.lastfm_username if update.lastfm_username is not None else current_user.get("lastfm_username")
    new_llm_provider = update.llm_provider if update.llm_provider is not None else current_user.get("llm_provider")

    await db.execute(
        "UPDATE users SET lastfm_username = ?, llm_provider = ? WHERE id = ?",
        (new_lastfm_username, new_llm_provider, current_user["id"]),
    )
    await db.commit()

    SettingsService().apply_updates(update.model_dump(exclude_none=True))
    return {"status": "ok"}
