"""FastAPI router for LLM chat and memory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.llm.schemas import ChatMessage

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/chat/message")
async def send_chat_message(message: ChatMessage) -> StreamingResponse:
    """Accept a chat message and return a streaming SSE response.

    The response is streamed as Server-Sent Events so the frontend can
    render tokens as they arrive.
    """
    # TODO: Inject LLM provider and MemoryService via Depends
    # TODO: Build system prompt via build_system_prompt(...)
    # TODO: Call provider.stream(system_prompt, message.content)
    # TODO: Wrap async iterator in StreamingResponse(media_type="text/event-stream")
    raise NotImplementedError


@router.get("/chat/memory")
async def get_memory() -> dict:
    """Return the current user's memory block."""
    # TODO: Resolve current user
    # TODO: Inject MemoryService via Depends
    # TODO: Call memory_service.get_memory(user_id)
    raise NotImplementedError
