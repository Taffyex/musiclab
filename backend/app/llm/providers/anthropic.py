"""Anthropic (Claude) LLM provider implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import anthropic

from app.llm.base import LLMProvider
from app.llm.schemas import LLMResponse


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic Messages API.

    Uses the official ``anthropic`` Python SDK.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a non-streaming response via the Anthropic API.

        TODO:
            - Build messages list from system_prompt and user_message
            - Call self._client.messages.create(...)
            - Map response to LLMResponse
            - Extract usage stats
        """
        raise NotImplementedError

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the Anthropic API.

        TODO:
            - Use self._client.messages.stream(...)
            - Yield text deltas as they arrive
        """
        raise NotImplementedError
        # Make this a proper async generator:
        yield ""  # pragma: no cover

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        """Generate a response with tool-use via the Anthropic API.

        TODO:
            - Convert tools to Anthropic tool format
            - Call self._client.messages.create(..., tools=tools)
            - Extract tool_use blocks from response
            - Map to LLMResponse with tool_calls populated
        """
        raise NotImplementedError
