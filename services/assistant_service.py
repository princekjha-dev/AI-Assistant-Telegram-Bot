import logging
from typing import Dict, List, Optional

import config
from ai.memory_manager import MemoryManager
from ai.mood_detector import MoodDetector
from ai.prompt_builder import PromptBuilder
from llm.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, db):
        self.db = db
        self.memory_manager = MemoryManager(db)
        self.mood_detector = MoodDetector()
        self.prompt_builder = PromptBuilder()
        self.llm_client = OpenRouterClient()

    async def generate_response(
        self,
        user_id: int,
        user_message: str,
        user_context: Dict,
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        detected_mood = self.mood_detector.detect_mood(user_message)
        user_context = dict(user_context)
        user_context["detected_mood"] = detected_mood

        durable_memories = await self._load_durable_memories(user_id)
        system_prompt = self.prompt_builder.build_system_prompt(
            personality=user_context.get("personality", config.DEFAULT_PERSONALITY),
            mood=detected_mood,
            user_context=user_context,
            durable_memories=durable_memories,
        )

        if conversation_history is None:
            conversation_history = []

        messages = list(conversation_history)
        messages.append({"role": "user", "content": user_message})
        return await self.llm_client.generate(system_prompt, messages, user_context)

    async def _load_durable_memories(self, user_id: int) -> List[str]:
        try:
            memories = await self.db.get_user_memories(user_id)
            return [memory["fact"] for memory in memories]
        except Exception:
            return []
