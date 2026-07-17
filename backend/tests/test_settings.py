from __future__ import annotations
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import settings
from app.database import init_db
from app.auth import service
from app.settings.router import mask_key, is_masked

def test_mask_key_unit():
    assert mask_key(None) == ""
    assert mask_key("") == ""
    assert mask_key("short") == "********"
    assert mask_key("abcdefghij") == "abcd****ghij"
    assert mask_key("123456789012345") == "1234****2345"

def test_is_masked_unit():
    assert is_masked("abcd****ghij") is True
    assert is_masked("1234****2345") is True
    assert is_masked("abcdefghij") is False
    assert is_masked("short") is False
    assert is_masked("") is False

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    
    import aiosqlite
    from app.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users")
        await db.execute(
            "INSERT INTO users (id, username, password_hash, lastfm_username, llm_provider) VALUES (?, ?, ?, ?, ?)",
            (1, "admin", service.get_password_hash("adminpass"), "admin_lastfm", "openai")
        )
        await db.commit()
    yield

async def get_auth_cookies(ac: AsyncClient):
    response = await ac.post("/api/auth/login", data={"username": "admin", "password": "adminpass"})
    return response.cookies

@pytest.mark.asyncio
async def test_get_settings_masks_keys():
    settings.lastfm_api_key = "abcdef1234567890abcdef"
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        cookies = await get_auth_cookies(ac)
        response = await ac.get("/api/settings", cookies=cookies)
        
    assert response.status_code == 200
    data = response.json()
    assert data["lastfm_username"] == "admin_lastfm"
    assert "****" in data["lastfm_api_key"]
    assert data["lastfm_api_key"] == "abcd****cdef"

@pytest.mark.asyncio
async def test_put_settings_ignores_masked_keys():
    settings.lastfm_api_key = "original_key_123456"
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        cookies = await get_auth_cookies(ac)
        
        # Test updating with masked key (should be ignored)
        update_data = {
            "lastfm_api_key": "orig****3456"
        }
        response = await ac.put("/api/settings", json=update_data, cookies=cookies)
        assert response.status_code == 200
        
        # The key in settings should not have changed to the masked one
        assert settings.lastfm_api_key == "original_key_123456"
        
        # Test updating with real key
        update_data2 = {
            "lastfm_api_key": "new_real_key_654321"
        }
        response = await ac.put("/api/settings", json=update_data2, cookies=cookies)
        assert response.status_code == 200
        assert settings.lastfm_api_key == "new_real_key_654321"
