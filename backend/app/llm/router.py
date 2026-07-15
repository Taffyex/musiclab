"""FastAPI router for LLM chat and memory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.llm.schemas import ChatMessage

router = APIRouter()

from app.config import settings
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.llm.base import LLMProvider
from app.llm.memory import MemoryService
from app.llm.prompts import build_system_prompt
import aiosqlite

def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        from app.llm.providers.openai import OpenAIProvider
        return OpenAIProvider(api_key=settings.openai_api_key)
    elif provider == "anthropic":
        from app.llm.providers.anthropic import AnthropicProvider
        return AnthropicProvider(api_key=settings.anthropic_api_key)
    else:
        from app.llm.providers.ollama import OllamaProvider
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

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
