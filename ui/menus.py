from database.models import User
from ai.prompt_builder import PromptBuilder
from ai.mood_detector import MoodDetector


class MenuMessages:
    @staticmethod
    def get_welcome_message(user: User) -> str:
        """Welcome message with current status"""
        mood_emoji = MoodDetector.get_mood_emoji(user.mood_state)

        return f"""👋 **Welcome, {user.username}!**

**Current Status:**
🎭 Personality: {user.personality_mode.title()}
🤖 AI Model: {user.llm_provider.title()}
{mood_emoji} Mood: {user.mood_state.title()}
🔥 Streak: {user.streak_count} days
⭐ Points: {user.interaction_score}

Select an option from the menu below:"""

    @staticmethod
    def get_memory_summary(history_summary: str, message_count: int) -> str:
        """Memory summary message"""
        return f"""🧠 **Conversation Memory**

Total Messages: {message_count}

{history_summary}

This is what I remember from our recent conversations."""

    @staticmethod
    def get_stats_message(user: User) -> str:
        """User statistics message"""
        return f"""📊 **Your Statistics**

**Engagement:**
⭐ Total Points: {user.interaction_score}
🔥 Current Streak: {user.streak_count} days
📅 Last Active: {user.last_active.strftime('%Y-%m-%d %H:%M') if user.last_active else 'Never'}

**Preferences:**
🎭 Personality: {user.personality_mode.title()}
🤖 AI Model: {user.llm_provider.title()}
{MoodDetector.get_mood_emoji(user.mood_state)} Mood: {user.mood_state.title()}

Keep chatting to earn more points and unlock achievements!"""

    @staticmethod
    def get_personality_changed_message(personality: str) -> str:
        """Confirmation message for personality change"""
        descriptions = {
            "friendly": "I'll be warm, supportive, and casual in our chats! 😊",
            "professional": "I'll maintain a formal, precise, and business-like tone. 💼",
            "motivational": "I'll be energetic and inspiring to help you achieve your goals! 💪",
            "sarcastic": "Oh great, now I get to be witty and sarcastic. This should be fun. 😏"
        }

        return f"""🎭 **Personality Updated!**

New Mode: **{personality.title()}**

{descriptions.get(personality, "Personality updated successfully.")}"""

    @staticmethod
    def get_llm_changed_message(provider: str) -> str:
        """Confirmation message for LLM change"""
        descriptions = {
            "openai": "Now using OpenAI (ChatGPT) - versatile and powerful for all tasks. 🤖",
            "claude": "Now using Claude by Anthropic - thoughtful and nuanced responses. 🧠",
            "gemini": "Now using Gemini by Google - fast and capable across many tasks. ✨",
            "local": "Now using your local LLM - privacy-focused and customizable. 💻"
        }

        return f"""🤖 **AI Model Changed!**

New Provider: **{provider.title()}**

{descriptions.get(provider, "AI model updated successfully.")}"""

    @staticmethod
    def get_about_message() -> str:
        """About message"""
        return """ℹ️ **About This Bot**

AI-Powered Telegram Virtual Assistant with:
• Multi-LLM support (Claude, Gemini, Local)
• Persistent memory and context
• Adaptive personality modes
• Mood detection
• Gamification (streaks, achievements)

Built with Python and python-telegram-bot

Version: 1.0.0"""

    @staticmethod
    def get_clear_history_warning() -> str:
        """Warning message for clearing history"""
        return """⚠️ **Clear Conversation History**

This will permanently delete all your conversation history.

Your points, streak, and achievements will be preserved.

Are you sure?"""

    @staticmethod
    def get_reset_streak_warning() -> str:
        """Warning message for resetting streak"""
        return """⚠️ **Reset Streak**

This will reset your current streak to 0.

Your points and achievements will be preserved.

Are you sure?"""