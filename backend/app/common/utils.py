"""General-purpose utility functions for MusicLab."""

from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


def slugify(text: str) -> str:
    """Convert *text* to a URL-friendly slug.

    Args:
        text: The input string.

    Returns:
        A lowercased, hyphen-separated ASCII string.

    Example::

        >>> slugify("Godspeed You! Black Emperor")
        'godspeed-you-black-emperor'
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def truncate(text: str, max_length: int) -> str:
    """Truncate *text* to *max_length* characters, appending '…' if shortened.

    Args:
        text: The input string.
        max_length: Maximum allowed length (must be ≥ 1).

    Returns:
        The (possibly truncated) string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args: object,
    max_retries: int = 3,
    delay: float = 1.0,
    **kwargs: object,
) -> T:
    """Retry an async callable with exponential back-off.

    Args:
        func: The async function to call.
        *args: Positional arguments forwarded to *func*.
        max_retries: Maximum number of retry attempts.
        delay: Initial delay in seconds (doubled each retry).
        **kwargs: Keyword arguments forwarded to *func*.

    Returns:
        The return value of *func* on success.

    Raises:
        Exception: Re-raises the last exception after all retries are exhausted.
    """
    last_exc: Exception | None = None
    current_delay = delay
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < max_retries:
                await asyncio.sleep(current_delay)
                current_delay *= 2
    # Should never be None at this point, but satisfy the type checker.
    assert last_exc is not None  # noqa: S101
    raise last_exc


def parse_llm_json(content: str) -> list[dict[str, Any]]:
    """Parse JSON from an LLM response, stripping markdown fences if present.

    Args:
        content: Raw LLM response text, possibly wrapped in ```json fences.

    Returns:
        Parsed list of dicts, or an empty list on failure.
    """
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, ValueError):
        return []
