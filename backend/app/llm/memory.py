"""Memory service for persisting and evolving user preferences."""

from __future__ import annotations

import aiosqlite

from app.llm.base import LLMProvider
from app.llm.schemas import ChatMessage, MemoryUpdate


class MemoryService:
    """Manages the per-user memory block that stores learned preferences.

    Memory is stored in the ``memory_blocks`` table and updated after
    conversations by asking the LLM to extract preference signals.
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        llm_provider: LLMProvider,
    ) -> None:
        self.db = db
        self.llm = llm_provider

    async def get_memory(self, user_id: int) -> dict:
        """Load the memory block for a user from the database.

        Args:
            user_id: Internal user ID.

        Returns:
            A dict representing the user's memory block, or an empty dict
            if no memory exists yet.
        """
        # TODO: SELECT from memory_blocks WHERE user_id = ?
        # TODO: Deserialize JSON column to dict
        # TODO: Return empty dict on miss
        raise NotImplementedError

    async def extract_and_update(
        self,
        user_id: int,
        conversation: list[ChatMessage],
    ) -> None:
        """Extract preference signals from a conversation and merge into memory.

        Calls the LLM with the ``MEMORY_EXTRACTION_PROMPT`` to identify new
        preferences, then merges them into the existing memory block.

        Args:
            user_id: Internal user ID.
            conversation: The list of chat messages to analyse.
        """
        # TODO: Format conversation into a single string
        # TODO: Call self.llm.generate with MEMORY_EXTRACTION_PROMPT
        # TODO: Parse LLM response as MemoryUpdate
        # TODO: Load existing memory via self.get_memory(user_id)
        # TODO: Merge via self.merge_memory(existing, update)
        # TODO: Persist updated memory to DB
        raise NotImplementedError

    async def merge_memory(
        self,
        existing: dict,
        new: MemoryUpdate,
    ) -> dict:
        """Merge new preference signals into the existing memory block.

        This is an additive merge — new items are appended, duplicates
        are deduplicated.

        Args:
            existing: The current memory dict.
            new: Newly extracted preference signals.

        Returns:
            The merged memory dict.
        """
        # TODO: Append new.core_preferences to existing["core_preferences"]
        # TODO: Append new.liked_recommendations
        # TODO: Append new.disliked_recommendations
        # TODO: Append new.noted_patterns
        # TODO: Deduplicate each list
        raise NotImplementedError
