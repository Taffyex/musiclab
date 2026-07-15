"""LLM Pydantic schemas for chat, discovery, and memory models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class LLMResponse(BaseModel):
    """Wrapper for a response from any LLM provider."""

    content: str
    tool_calls: list | None = None
    usage: dict | None = None


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: Literal["user", "assistant"]
    content: str




class MemoryUpdate(BaseModel):
    """Extracted preference signals from a conversation, to merge into memory."""

    core_preferences: list[str] = Field(default_factory=list)
    liked_recommendations: list[str] = Field(default_factory=list)
    disliked_recommendations: list[str] = Field(default_factory=list)
    noted_patterns: list[str] = Field(default_factory=list)
