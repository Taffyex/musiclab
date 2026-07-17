from __future__ import annotations
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import settings
from app.database import init_db
from app.auth import service

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    
    # create test user
    import aiosqlite
    from app.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users")
        await db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("testuser", service.get_password_hash("testpass"))
        )
        await db.commit()
    yield

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert response.json() == {"message": "Logged in successfully"}
    assert "session" in response.cookies

@pytest.mark.asyncio
async def test_login_failure():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "testuser", "password": "wrongpass"})
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_rate_limiting():
    from app.common.middleware import _rate_limit_store
    _rate_limit_store.clear()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for _ in range(5):
            res = await ac.post("/api/auth/login", data={"username": "testuser", "password": "wrongpass"})
            assert res.status_code == 401
            
        # 6th request should be rate limited
        res = await ac.post("/api/auth/login", data={"username": "testuser", "password": "wrongpass"})
        assert res.status_code == 429
        assert "Too many login attempts" in res.json()["detail"]
