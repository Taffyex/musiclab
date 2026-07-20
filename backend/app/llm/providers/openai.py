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
        base_url: str | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("API key not configured for OpenAI provider")
        self.model = model
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a non-streaming response via the OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        msg = response.choices[0].message
        return LLMResponse(
            content=msg.content or "",
            usage=dict(response.usage) if response.usage else None,
        )

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        """Generate a response with function-calling via the OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        # Format tools for OpenAI
        openai_tools = [{"type": "function", "function": t} for t in tools]
        
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools,
        )
        msg = response.choices[0].message
        
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                })
                
        return LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls if tool_calls else None,
            usage=dict(response.usage) if response.usage else None,
        )
