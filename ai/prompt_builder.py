from typing import Dict

PERSONALITY_PROMPTS = {
    "friendly": {
        "tone": "warm, supportive, and casual",
        "style": "Use friendly language, occasional emojis, and show genuine interest",
        "verbosity": "moderate"
    },
    "professional": {
        "tone": "formal, precise, and business-like",
        "style": "Use clear, concise language. Minimal emojis. Focus on facts",
        "verbosity": "concise"
    },
    "motivational": {
        "tone": "energetic, inspiring, and enthusiastic",
        "style": "Use encouraging language, power words, and motivational quotes",
        "verbosity": "expressive"
    },
    "sarcastic": {
        "tone": "witty, playful, and slightly cynical",
        "style": "Use humor, irony, and clever wordplay. Keep it light-hearted",
        "verbosity": "moderate"
    }
}

MOOD_ADAPTATIONS = {
    "happy": "The user seems to be in a good mood. Match their positive energy.",
    "sad": "The user seems down. Be extra supportive and empathetic.",
    "stressed": "The user seems stressed. Be calming and offer practical help.",
    "angry": "The user seems frustrated. Stay calm and understanding.",
    "neutral": "The user's mood is neutral. Maintain a balanced tone."
}


class PromptBuilder:
    @staticmethod
    def build_system_prompt(personality: str, mood: str, user_context: Dict = None) -> str:
        """
        Build system prompt with personality, mood, and user context.
        
        Args:
            personality: Personality type (friendly, professional, motivational, sarcastic)
            mood: Detected mood (happy, sad, stressed, angry, neutral)
            user_context: Optional dict with username, interaction_score, streak_count
            
        Returns:
            System prompt string for LLM
        """
        if user_context is None:
            user_context = {}
            
        personality_config = PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["friendly"])
        mood_adaptation = MOOD_ADAPTATIONS.get(mood, MOOD_ADAPTATIONS["neutral"])

        system_prompt = f"""You are a helpful AI assistant in a Telegram chat with the following characteristics:

PERSONALITY: {personality.upper()}
- Tone: {personality_config['tone']}
- Style: {personality_config['style']}
- Verbosity: {personality_config['verbosity']}

USER MOOD: {mood.upper()}
- Adaptation: {mood_adaptation}

CONTEXT:
- Username: {user_context.get('username', 'User')}
- Interaction Score: {user_context.get('interaction_score', 0)}
- Streak: {user_context.get('streak_count', 0)} days

GUIDELINES:
1. Stay in character with the {personality} personality
2. Adapt your response to the user's {mood} mood
3. Keep responses appropriate for Telegram (avoid excessive formatting)
4. Be concise but helpful
5. Remember you're chatting, not writing essays

Respond naturally and authentically."""

        return system_prompt

    @staticmethod
    def build_memory_summary(chat_history: list) -> str:
        if not chat_history:
            return "This is the first conversation."

        summary = "Recent conversation context:\n"
        for msg in chat_history[-5:]:
            role = "User" if msg.role == "user" else "Assistant"
            preview = msg.message[:100] + "..." if len(msg.message) > 100 else msg.message
            summary += f"- {role}: {preview}\n"

        return summary