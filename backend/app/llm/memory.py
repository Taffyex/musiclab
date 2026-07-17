"""Memory service for persisting and evolving user preferences."""

from __future__ import annotations

import aiosqlite
import logging

logger = logging.getLogger(__name__)

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
        import json
        async with self.db.execute("SELECT memory FROM memory_blocks WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        
        if not row:
            return {}
            
        return json.loads(row["memory"])

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
        from app.llm.prompts import MEMORY_EXTRACTION_PROMPT
        import json
        
        conv_str = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation])
        user_msg = f"Conversation:\n{conv_str}"
        response = await self.llm.generate(system_prompt=MEMORY_EXTRACTION_PROMPT, user_message=user_msg)
        try:
            update_data = json.loads(response.content)
            update = MemoryUpdate(**update_data)
        except Exception:
            logger.exception("Failed to parse LLM response")
            return
            
        existing = await self.get_memory(user_id)
        merged = await self.merge_memory(existing, update)
        
        merged_json = json.dumps(merged)
        await self.db.execute(
            "INSERT OR REPLACE INTO memory_blocks (user_id, memory) VALUES (?, ?)",
            (user_id, merged_json)
        )
        await self.db.commit()

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
        def merge_list(key: str, new_items: list[str]) -> list[str]:
            current = existing.get(key, [])
            # Deduplicate while preserving order
            seen = set()
            merged_list = []
            for item in current + new_items:
                if item not in seen:
                    seen.add(item)
                    merged_list.append(item)
            return merged_list

        return {
            "core_preferences": merge_list("core_preferences", new.core_preferences),
            "liked_recommendations": merge_list("liked_recommendations", new.liked_recommendations),
            "disliked_recommendations": merge_list("disliked_recommendations", new.disliked_recommendations),
            "noted_patterns": merge_list("noted_patterns", new.noted_patterns),
        }
