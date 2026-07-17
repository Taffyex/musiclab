from __future__ import annotations
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import init_db
from app.auth import service

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    
    import aiosqlite
    from app.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_favorites")
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
async def test_favorites_crud():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        cookies = await get_auth_cookies(ac)
        
        # 1. Get empty favorites
        response = await ac.get("/api/explore/favorites", cookies=cookies)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
        
        # 2. Add a favorite
        fav_payload = {
            "entity_type": "artist",
            "entity_id": 100,
            "name": "Test Artist",
            "slug": "test-artist"
        }
        response = await ac.post("/api/explore/favorites", json=fav_payload, cookies=cookies)
        assert response.status_code == 200
        
        # 3. Get favorites and verify
        response = await ac.get("/api/explore/favorites", cookies=cookies)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entity_type"] == "artist"
        assert data[0]["entity_id"] == 100
        assert data[0]["name"] == "Test Artist"
        
        # 4. Delete favorite
        response = await ac.delete("/api/explore/favorites/artist/100", cookies=cookies)
        assert response.status_code == 200
        
        # 5. Get empty favorites again
        response = await ac.get("/api/explore/favorites", cookies=cookies)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
