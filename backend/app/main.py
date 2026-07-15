"""
MusicLab — FastAPI application entry point.

Sets up the FastAPI app with lifespan management, router registration,
health check endpoint, and static file serving for the SvelteKit frontend.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import init_db


# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize resources on startup and clean up on shutdown."""
    await init_db()
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


# ──────────────────────────────────────────────
# Router registration
# ──────────────────────────────────────────────

try:
    from app.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
except ImportError:
    pass  # TODO: remove try/except once auth module is implemented

# TODO: uncomment as each router module is created
# from app.lastfm.router import router as lastfm_router
# app.include_router(lastfm_router, prefix="/api/lastfm", tags=["lastfm"])

# from app.lidarr.router import router as lidarr_router
# app.include_router(lidarr_router, prefix="/api/lidarr", tags=["lidarr"])

# from app.discover.router import router as discover_router
# app.include_router(discover_router, prefix="/api/discover", tags=["discover"])

# from app.chat.router import router as chat_router
# app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

# from app.settings.router import router as settings_router
# app.include_router(settings_router, prefix="/api/settings", tags=["settings"])


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

    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except Exception:
    # Static directory won't exist during local backend-only development
    pass
