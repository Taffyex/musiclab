"""LLM Pydantic schemas for chat, discovery, and memory models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Wrapper for a response from any LLM provider."""

    content: str
    tool_calls: list | None = None
    usage: dict | None = None


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: str  # "system", "user", or "assistant"
    content: str


class DiscoveryRecommendation(BaseModel):
    """A single artist recommendation produced by the LLM."""

    artist_name: str
    genre: str = ""
    era: str = ""
    why_it_matches: str = ""
    listener_count_hint: int | None = None
    tags: list[str] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    """Extracted preference signals from a conversation, to merge into memory."""

    core_preferences: list[str] = Field(default_factory=list)
    liked_recommendations: list[str] = Field(default_factory=list)
    disliked_recommendations: list[str] = Field(default_factory=list)
    noted_patterns: list[str] = Field(default_factory=list)
