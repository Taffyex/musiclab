"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.llm.schemas import LLMResponse


class LLMProvider(ABC):
    """Abstract interface that all LLM providers must implement.

    Concrete subclasses live in :mod:`app.llm.providers`.
    """

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a single response (non-streaming).

        Args:
            system_prompt: The system-level instruction.
            user_message: The user's message.
            tools: Optional tool/function definitions for function-calling.

        Returns:
            An :class:`LLMResponse` with the model output.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Stream response tokens as an async iterator.

        Args:
            system_prompt: The system-level instruction.
            user_message: The user's message.

        Yields:
            Chunks of text as they arrive from the model.
        """
        ...

    @abstractmethod
    async def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        """Generate a response with tool/function-calling support.

        Args:
            system_prompt: The system-level instruction.
            user_message: The user's message.
            tools: Tool/function definitions the model may invoke.

        Returns:
            An :class:`LLMResponse` that may include ``tool_calls``.
        """
        ...
