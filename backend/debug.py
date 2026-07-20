import asyncio
from httpx import AsyncClient
from app.main import app
from app.config import settings

async def main():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "admin", "password": "adminpass"})
        cookies = response.cookies
        
        settings.lastfm_api_key = "original_key_123456"
        print("Before update, lastfm_api_key =", settings.lastfm_api_key)
        
        update_data2 = {
            "lastfm_api_key": "new_real_key_654321"
        }
        res = await ac.put("/api/settings", json=update_data2, cookies=cookies)
        print("PUT response:", res.status_code, res.json())
        
        res2 = await ac.get("/api/settings", cookies=cookies)
        print("GET response:", res2.status_code, res2.json())
        print("After update, lastfm_api_key =", settings.lastfm_api_key)

asyncio.run(main())
