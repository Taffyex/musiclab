"""OpenAI LLM provider implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import openai

from app.llm.base import LLMProvider
from app.llm.schemas import LLMResponse


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI Chat Completions API.

    Uses the official ``openai`` Python SDK.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
    ) -> None:
        self.model = model
        self._client = openai.AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a non-streaming response via the OpenAI API.

        TODO:
            - Build messages list with system and user roles
            - Call self._client.chat.completions.create(...)
            - Map response.choices[0].message to LLMResponse
            - Extract usage stats
        """
        raise NotImplementedError

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the OpenAI API.

        TODO:
            - Call self._client.chat.completions.create(..., stream=True)
            - Iterate async over chunks
            - Yield delta.content strings
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
        """Generate a response with function-calling via the OpenAI API.

        TODO:
            - Convert tools to OpenAI function-calling format
            - Call self._client.chat.completions.create(..., tools=tools)
            - Extract tool_calls from response
            - Map to LLMResponse with tool_calls populated
        """
        raise NotImplementedError
