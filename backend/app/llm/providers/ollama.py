"""Ollama (local) LLM provider implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.llm.base import LLMProvider
from app.llm.schemas import LLMResponse


class OllamaProvider(LLMProvider):
    """LLM provider backed by a local Ollama instance.

    Communicates with Ollama's REST API directly via ``httpx``
    (no dedicated SDK needed).
    """

    def __init__(self, base_url: str, model: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=120.0,
            headers={"Accept": "application/json"},
        )

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a non-streaming response via the Ollama API.

        TODO:
            - POST /api/chat with model, messages, stream=False
            - Parse response JSON
            - Map to LLMResponse
        """
        raise NotImplementedError

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the Ollama API.

        TODO:
            - POST /api/chat with model, messages, stream=True
            - Read NDJSON lines from response
            - Yield message.content from each chunk
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
        """Generate a response with tool-calling via the Ollama API.

        TODO:
            - POST /api/chat with model, messages, tools, stream=False
            - Parse tool_calls from response
            - Map to LLMResponse with tool_calls populated
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Ollama-specific methods
    # ------------------------------------------------------------------

    async def list_models(self) -> list[str]:
        """List models installed on the local Ollama instance.

        Endpoint: ``GET /api/tags``

        Returns:
            A list of model name strings.
        """
        # TODO: GET /api/tags
        # TODO: Extract model names from response["models"]
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()
