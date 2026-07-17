from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import aiosqlite
from pathlib import Path
from dotenv import set_key
import os

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.config import settings

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
async def get_settings(current_user: dict = Depends(get_current_user)) -> dict:
    return {
        "lastfm_username": current_user.get("lastfm_username", "") or "",
        "lastfm_api_key": settings.lastfm_api_key,
        "lidarr_url": settings.lidarr_url,
        "lidarr_api_key": settings.lidarr_api_key,
        "llm_provider": current_user.get("llm_provider", settings.llm_provider),
        "anthropic_api_key": settings.anthropic_api_key,
        "openai_api_key": settings.openai_api_key,
        "deepseek_api_key": getattr(settings, "deepseek_api_key", ""),
    }

@router.put("")
async def update_settings(
    update: SettingsUpdate,
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
) -> dict:
    new_lastfm_username = update.lastfm_username if update.lastfm_username is not None else current_user.get("lastfm_username")
    new_llm_provider = update.llm_provider if update.llm_provider is not None else current_user.get("llm_provider")
    
    await db.execute(
        "UPDATE users SET lastfm_username = ?, llm_provider = ? WHERE id = ?",
        (new_lastfm_username, new_llm_provider, current_user["id"])
    )
    await db.commit()
    
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    
    if update.lastfm_api_key is not None:
        set_key(str(env_path), "LASTFM_API_KEY", update.lastfm_api_key)
        settings.lastfm_api_key = update.lastfm_api_key
        
    if update.lidarr_url is not None:
        set_key(str(env_path), "LIDARR_URL", update.lidarr_url)
        settings.lidarr_url = update.lidarr_url
        
    if update.lidarr_api_key is not None:
        set_key(str(env_path), "LIDARR_API_KEY", update.lidarr_api_key)
        settings.lidarr_api_key = update.lidarr_api_key
        
    if update.anthropic_api_key is not None:
        set_key(str(env_path), "ANTHROPIC_API_KEY", update.anthropic_api_key)
        settings.anthropic_api_key = update.anthropic_api_key
        
    if update.openai_api_key is not None:
        set_key(str(env_path), "OPENAI_API_KEY", update.openai_api_key)
        settings.openai_api_key = update.openai_api_key
        
    if update.deepseek_api_key is not None:
        set_key(str(env_path), "DEEPSEEK_API_KEY", update.deepseek_api_key)
        settings.deepseek_api_key = update.deepseek_api_key

    return {"status": "ok"}
