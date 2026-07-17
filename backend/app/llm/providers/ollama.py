"""Ollama (local) LLM provider implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.common.http import BaseHttpClient
from app.llm.base import LLMProvider
from app.llm.schemas import LLMResponse


class OllamaProvider(LLMProvider, BaseHttpClient):
    """LLM provider backed by a local Ollama instance (stub — not yet implemented)."""

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
        raise NotImplementedError

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        raise NotImplementedError
        yield ""  # pragma: no cover

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        raise NotImplementedError

    async def list_models(self) -> list[str]:
        raise NotImplementedError
