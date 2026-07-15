"""FastAPI router for discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.discovery.schemas import DiscoveryBatch, DiscoveryCard, ExploreRequest

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/batch", response_model=DiscoveryBatch)
async def generate_batch() -> DiscoveryBatch:
    """Generate a new batch of discovery recommendation cards."""
    # TODO: Resolve current user
    # TODO: Inject DiscoveryService via Depends
    # TODO: Call service.generate_batch(user_id)
    raise NotImplementedError


@router.get("/explore/{artist_name}", response_model=list[DiscoveryCard])
async def explore_similar(artist_name: str) -> list[DiscoveryCard]:
    """Explore artists similar to the given artist."""
    # TODO: Resolve current user
    # TODO: Inject DiscoveryService via Depends
    # TODO: Call service.explore_similar(user_id, artist_name)
    raise NotImplementedError


@router.get("/history", response_model=list[DiscoveryBatch])
async def get_history() -> list[DiscoveryBatch]:
    """Return past discovery batches for the current user."""
    # TODO: Resolve current user
    # TODO: Inject DiscoveryService via Depends
    # TODO: Call service.get_history(user_id)
    raise NotImplementedError
