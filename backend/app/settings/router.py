"""Router for user settings management."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.settings.schemas import SettingsUpdate
from app.settings.service import SettingsService

router = APIRouter()


def get_settings_service() -> SettingsService:
    return SettingsService()


@router.get("")
async def get_settings(
    current_user: dict = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> dict:
    return service.get_settings(current_user)


@router.put("")
async def update_settings(
    update: SettingsUpdate,
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
    service: SettingsService = Depends(get_settings_service),
) -> dict:
    await service.update_user_settings(
        db=db,
        user_id=current_user["id"],
        current_user=current_user,
        updates=update.model_dump(exclude_none=True),
    )
    return {"status": "ok"}

