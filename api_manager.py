"""
Unified API Manager - Supports multiple LLM providers
"""

import logging
import asyncio
from typing import List, Dict, Optional
import httpx
from ai.image_generator import ImageGenerator
from ai.mood_detector import MoodDetector
from ai.prompt_builder import PromptBuilder
import config

logger = logging.getLogger(__name__)

# Provider endpoints
PROVIDERS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": config.OPENROUTER_API_KEY,
        "model_map": {"gpt-4-turbo": "openai/gpt-4-turbo", "claude-3-sonnet": "anthropic/claude-3-sonnet"}
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key": config.OPENAI_API_KEY,
        "model_map": {"gpt-4-turbo": "gpt-4-turbo-preview", "claude-3-sonnet": "gpt-3.5-turbo"}
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key": config.GEMINI_API_KEY,
        "model_map": {"gpt-4-turbo": "gemini-1.5-pro", "claude-3-sonnet": "gemini-1.5-pro"}
    },
}


class APIManager:
    """Unified API manager supporting multiple LLM providers"""
    
    def __init__(self, database=None):
        """Initialize API manager with configured provider"""
        self.provider = config.LLM_PROVIDER or "openrouter"
        self.image_generator = ImageGenerator() if config.ENABLE_IMAGE_GENERATION else None
        self.mood_detector = MoodDetector()
        self.prompt_builder = PromptBuilder()
        self.memory_manager = MemoryManager(database)
        
        # Verify provider is available
        if self.provider not in PROVIDERS:
            self.provider = "openrouter"
        
        logger.info(f"APIManager initialized with {self.provider} LLM provider")
    
    async def generate_response(
        self,
        user_message: str,
        user_context: Dict,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Generate AI response with integrated mood detection
        
        Args:
            user_message: User's input message
            user_context: Context dict with user preferences, personality, mood
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response text
        """
        try:
            # Detect mood from user message
            detected_mood = self.mood_detector.detect_mood(user_message)
            user_context['detected_mood'] = detected_mood
            
            # Build system prompt with context
            system_prompt = self.prompt_builder.build_system_prompt(
                personality=user_context.get('personality', config.DEFAULT_PERSONALITY),
                mood=detected_mood,
                user_context=user_context
            )
            
            # Format messages
            messages = conversation_history or []
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = await self._call_llm(system_prompt, messages)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "❌ Error generating response. Please try again."
    
    async def _call_llm(self, system_prompt: str, messages: List[Dict]) -> str:
        """Call configured LLM provider"""
        try:
            provider_config = PROVIDERS.get(self.provider)
            if not provider_config or not provider_config["key"]:
                return "❌ LLM provider not configured. Please set up API keys."
            
            headers = {
                "Authorization": f"Bearer {provider_config['key']}",
                "Content-Type": "application/json"
            }
            
            # Add provider-specific headers
            if self.provider == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/yourusername/bot"
                headers["X-Title"] = "AI-Assistant-Bot"
            
            payload = {
                "model": config.PRIMARY_MODEL,
                "messages": [{"role": "system", "content": system_prompt}] + messages,
                "temperature": 0.7,
                "max_tokens": config.MAX_RESPONSE_TOKENS
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    provider_config["url"],
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return "❌ No response from LLM"
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code}")
            if e.response.status_code == 402:
                return "⚠️ Payment required for this LLM provider. Please add billing."
            return f"⚠️ Service error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"LLM call error: {str(e)}")
            return "❌ Error calling LLM service"
    
    async def generate_image(
        self,
        prompt: str,
        user_id: int = None
    ) -> Optional[str]:
        """
        Generate image from text prompt
        
        Args:
            prompt: Image description
            user_id: Optional user ID for tracking
            
        Returns:
            Image URL or file path, None if failed
        """
        if not config.ENABLE_IMAGE_GENERATION or not self.image_generator:
            logger.warning("Image generation is disabled")
            return None
        
        try:
            logger.info(f"Generating image for prompt: {prompt[:50]}...")
            image_url = await self.image_generator.generate(prompt)
            
            if image_url and user_id:
                await self.memory_manager.save_image_generation(
                    user_id=user_id,
                    prompt=prompt,
                    image_url=image_url
                )
            
            return image_url
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            return None
    
    async def analyze_mood(self, text: str) -> str:
        """
        Analyze and detect mood from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected mood string
        """
        try:
            mood = self.mood_detector.detect_mood(text)
            return mood
        except Exception as e:
            logger.error(f"Error analyzing mood: {str(e)}")
            return config.DEFAULT_MOOD
    
    async def get_conversation_context(
        self,
        user_id: int,
        limit: int = None
    ) -> List[Dict]:
        """
        Retrieve conversation context/history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        try:
            limit = limit or config.CONTEXT_WINDOW_SIZE
            context = await self.memory_manager.get_context(user_id, limit=limit)
            return context
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    async def clear_user_memory(self, user_id: int) -> bool:
        """
        Clear conversation memory for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            await self.memory_manager.clear_history(user_id)
            logger.info(f"Cleared memory for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all integrated APIs
        
        Returns:
            Dictionary with health status of each component
        """
        health = {
            "llm": False,
            "image_generation": False,
            "memory": False,
            "mood_detection": True  # Local service, always available
        }
        
        try:
            # Check LLM
            test_response = await asyncio.wait_for(
                self._call_llm(
                    system_prompt="You are a helpful assistant.",
                    messages=[{"role": "user", "content": "Hi"}]
                ),
                timeout=5
            )
            health["llm"] = bool(test_response) and "error" not in test_response.lower()
        except Exception as e:
            logger.warning(f"LLM health check failed: {str(e)}")
        
        try:
            # Check image generation
            health["image_generation"] = self.image_generator is not None
        except Exception as e:
            logger.warning(f"Image generation health check failed: {str(e)}")
        
        try:
            # Check memory
            health["memory"] = self.memory_manager is not None
        except Exception as e:
            logger.warning(f"Memory health check failed: {str(e)}")
        
        return health


# Create singleton instance
_api_manager_instance = None


def get_api_manager(database=None) -> APIManager:
    """Get or create the APIManager singleton"""
    global _api_manager_instance
    if _api_manager_instance is None:
        _api_manager_instance = APIManager(database)
    return _api_manager_instance
