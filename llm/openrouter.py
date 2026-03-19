import httpx
from typing import List, Dict, Optional
from llm.base import LLMClient
import config
import logging

logger = logging.getLogger(__name__)


class OpenRouterClient(LLMClient):
    """OpenRouter LLM Client supporting multiple models via single API"""
    
    def __init__(self, model: Optional[str] = None):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = model or config.PRIMARY_MODEL
        self.fallback_model = config.FALLBACK_MODEL
        self.base_url = f"{config.OPENROUTER_BASE_URL}/chat/completions"
        self.timeout = config.OPENROUTER_TIMEOUT
        self.retry_attempts = config.REQUEST_RETRY_ATTEMPTS
        self.retry_delay = config.REQUEST_RETRY_DELAY

    async def generate(
        self, 
        system_prompt: str, 
        messages: List[Dict[str, str]], 
        user_context: Dict
    ) -> str:
        """
        Generate response from OpenRouter API
        
        Args:
            system_prompt: System-level instructions
            messages: List of message dicts with role and content
            user_context: User context including personality, mood, etc.
            
        Returns:
            Generated response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/bot",
            "X-Title": "AI-Assistant-Bot"
        }

        # Convert to OpenRouter message format
        formatted_messages = [{"role": "system", "content": system_prompt}]
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": user_context.get("temperature", config.TEMPERATURE),
            "top_p": config.TOP_P,
            "max_tokens": config.MAX_RESPONSE_TOKENS,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"Unexpected OpenRouter response format: {data}")
                    return "I encountered an issue processing your request. Please try again."

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else 'Unknown'
            error_text = e.response.text if hasattr(e, 'response') else str(e)
            logger.error(f"OpenRouter API error {status_code}: {error_text}")
            
            # Fallback to alternative model if primary fails
            if self.model != self.fallback_model:
                logger.info(f"Falling back to {self.fallback_model}")
                self.model = self.fallback_model
                return await self.generate(system_prompt, messages, user_context)
            
            return f"⚠️ Service temporarily unavailable. Status: {e.status_code}"
        except httpx.TimeoutException:
            logger.error("OpenRouter request timeout")
            return "⏱️ Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error in OpenRouter generation: {str(e)}", exc_info=True)
            return f"❌ Error: {str(e)}"

    async def generate_with_retry(
        self, 
        system_prompt: str, 
        messages: List[Dict[str, str]], 
        user_context: Dict
    ) -> str:
        """Generate with automatic retry logic"""
        import asyncio
        
        for attempt in range(self.retry_attempts):
            try:
                return await self.generate(system_prompt, messages, user_context)
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"All {self.retry_attempts} attempts failed")
                    raise

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "OpenRouter"

    async def list_available_models(self) -> List[Dict]:
        """List available models from OpenRouter"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.OPENROUTER_BASE_URL}/models",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch available models: {str(e)}")
            return []

    async def get_model_stats(self) -> Dict:
        """Get API usage statistics"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.OPENROUTER_BASE_URL}/auth/key",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch API stats: {str(e)}")
            return {}
