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
from app.common.middleware import register_error_handlers


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
