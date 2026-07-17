"""FastAPI router for LLM chat and memory endpoints."""

from __future__ import annotations

import aiosqlite

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.llm.base import LLMProvider
from app.llm.memory import MemoryService
from app.llm.prompts import build_system_prompt
from app.llm.schemas import ChatMessage

router = APIRouter()

def get_llm_provider(current_user: dict = Depends(get_current_user)) -> LLMProvider:
    from app.llm.providers.openai import OpenAIProvider

    provider = (current_user.get("llm_provider") or settings.llm_provider).lower()
    if provider in ("openai", "deepseek"):
        api_key = settings.deepseek_api_key if provider == "deepseek" else settings.openai_api_key
        base_url = "https://api.deepseek.com/v1" if provider == "deepseek" else None
        model = "deepseek-chat" if provider == "deepseek" else "gpt-4o"
        return OpenAIProvider(api_key=api_key, base_url=base_url, model=model)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Unsupported LLM provider: {provider}")

def get_memory_service(
    db: aiosqlite.Connection = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider)
) -> MemoryService:
    return MemoryService(db=db, llm_provider=llm)


@router.post("/chat/message")
async def send_chat_message(
    message: ChatMessage,
    provider: LLMProvider = Depends(get_llm_provider),
    memory_service: MemoryService = Depends(get_memory_service),
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Accept a chat message and return a streaming SSE response.

    The response is streamed as Server-Sent Events so the frontend can
    render tokens as they arrive.
    """
    user_id = current_user["id"]
    memory = await memory_service.get_memory(user_id)
    system_prompt = build_system_prompt(memory=memory, mode="chat")
    
    stream = provider.stream(system_prompt, message.content)
    
    async def sse_generator():
        async for chunk in stream:
            # Yield as Server-Sent Event
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.get("/chat/memory")
async def get_memory(
    current_user: dict = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> dict:
    """Return the current user's memory block."""
    return await memory_service.get_memory(current_user["id"])
