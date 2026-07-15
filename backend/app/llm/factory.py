"""Factory function for creating LLM provider instances."""

from __future__ import annotations

from typing import Any

from app.llm.base import LLMProvider


def get_llm_provider(settings: Any) -> LLMProvider:
    """Instantiate the appropriate LLM provider based on application settings.

    Args:
        settings: Application settings object.  Must expose at least:
            - ``LLM_PROVIDER`` (``"anthropic"`` | ``"openai"`` | ``"ollama"``)
            - Provider-specific keys (``ANTHROPIC_API_KEY``, ``OPENAI_API_KEY``,
              ``OLLAMA_BASE_URL``, ``OLLAMA_MODEL``, etc.)

    Returns:
        A concrete :class:`LLMProvider` instance.

    Raises:
        ValueError: If ``settings.LLM_PROVIDER`` is not recognised.
    """
    match settings.LLM_PROVIDER:
        case "anthropic":
            from app.llm.providers.anthropic import AnthropicProvider

            return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        case "openai":
            from app.llm.providers.openai import OpenAIProvider

            return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        case "ollama":
            from app.llm.providers.ollama import OllamaProvider

            return OllamaProvider(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
            )
        case _:
            raise ValueError(
                f"Unknown LLM provider: {settings.LLM_PROVIDER!r}. "
                "Supported: 'anthropic', 'openai', 'ollama'."
            )
