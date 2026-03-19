from typing import List, Dict, Optional
from database.models import ChatMessage
import config
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self, database=None):
        """Initialize with optional database instance"""
        self.db = database

    async def get_context(self, user_id: int, limit: int = None) -> List[Dict[str, str]]:
        """
        Retrieve conversation context for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        if not self.db:
            return []
        
        try:
            limit = limit or config.CONTEXT_WINDOW_SIZE
            chat_history = await self.db.get_chat_history(user_id, limit=limit)
            return self.prepare_context_messages(chat_history)
        except Exception as e:
            logger.error(f"Error retrieving context for user {user_id}: {str(e)}")
            return []

    async def save_image_generation(self, user_id: int, prompt: str, image_url: str) -> bool:
        """Save image generation record"""
        if not self.db:
            return False
        try:
            # Could be extended to store image generation history
            return True
        except Exception as e:
            logger.error(f"Error saving image generation: {str(e)}")
            return False

    async def clear_history(self, user_id: int) -> bool:
        """Clear conversation history for a user"""
        if not self.db:
            return False
        try:
            await self.db.clear_chat_history(user_id)
            return True
        except Exception as e:
            logger.error(f"Error clearing history for user {user_id}: {str(e)}")
            return False

    @staticmethod
    def prepare_context_messages(chat_history: List[ChatMessage]) -> List[Dict[str, str]]:
        """
        Convert chat history to LLM message format.
        Returns most recent messages within context window.
        """
        messages = []

        # Take only the most recent messages
        recent_history = chat_history[-config.CONTEXT_WINDOW_SIZE:]

        for msg in recent_history:
            messages.append({
                "role": msg.role,
                "content": msg.message
            })

        return messages

    @staticmethod
    def summarize_old_history(chat_history: List[ChatMessage]) -> str:
        """
        Create a summary of older messages beyond context window.
        """
        if len(chat_history) <= config.CONTEXT_WINDOW_SIZE:
            return ""

        old_messages = chat_history[:-config.CONTEXT_WINDOW_SIZE]

        # Simple summarization: count messages and extract key topics
        user_msg_count = sum(1 for msg in old_messages if msg.role == "user")
        assistant_msg_count = sum(1 for msg in old_messages if msg.role == "assistant")

        summary = f"Previous conversation history: {user_msg_count} user messages, {assistant_msg_count} assistant responses."

        # Extract some key words from old messages
        all_text = " ".join([msg.message for msg in old_messages])
        words = all_text.lower().split()

        # Find most common non-trivial words (basic approach)
        word_freq = {}
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was',
                      'are', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                      'should', 'can', 'may', 'might', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his',
                      'her', 'its', 'our', 'their'}

        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        if word_freq:
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            topics = ", ".join([word for word, _ in top_words])
            summary += f" Topics discussed: {topics}."

        return summary