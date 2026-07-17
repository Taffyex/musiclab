"""
MusicLab — FastAPI application entry point.

Sets up the FastAPI app with lifespan management, router registration,
health check endpoint, and static file serving for the SvelteKit frontend.
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.auth.router import router as auth_router
from app.lastfm.router import router as lastfm_router
from app.lidarr.router import router as lidarr_router
from app.discovery.router import router as discovery_router
from app.llm.router import router as llm_router
from app.settings.router import router as settings_router
from app.explore.router import router as explore_router
from app.common.middleware import register_error_handlers


# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize resources on startup and clean up on shutdown."""
    await init_db()
    
    import aiosqlite
    from app.database import DB_PATH
    from app.explore.seed_service import SeedService
    async with aiosqlite.connect(DB_PATH) as db:
        seed_service = SeedService(db)
        await seed_service.seed_if_needed()

    yield
    # TODO: add any shutdown cleanup here (close pools, flush caches, etc.)


# ──────────────────────────────────────────────
# App instance
# ──────────────────────────────────────────────

app = FastAPI(
    title="MusicLab",
    version="0.1.0",
    lifespan=lifespan,
)

register_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Router registration
# ──────────────────────────────────────────────

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(lastfm_router, prefix="/api/lastfm", tags=["lastfm"])
app.include_router(lidarr_router, prefix="/api/lidarr", tags=["lidarr"])
app.include_router(discovery_router, prefix="/api/discovery", tags=["discovery"])
app.include_router(llm_router, prefix="/api/llm", tags=["llm"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(explore_router, prefix="/api/explore", tags=["explore"])


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

@app.get("/api/health", tags=["system"])
async def health_check() -> dict:
    """Basic health check endpoint used by Docker healthcheck."""
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Static file serving (SvelteKit build)
# ──────────────────────────────────────────────

try:
    from fastapi.staticfiles import StaticFiles
    import os
    from fastapi.responses import FileResponse

    app.mount("/", StaticFiles(directory="static", html=True), name="static")

    @app.exception_handler(404)
    async def custom_404_handler(request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail if hasattr(exc, "detail") else "Not Found"}, status_code=404)
        index_file = "static/index.html"
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return JSONResponse({"detail": "Not Found"}, status_code=404)
except Exception:
    # Static directory won't exist during local backend-only development
    pass
