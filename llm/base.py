from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def generate(self, system_prompt: str, messages: List[Dict[str, str]], user_context: Dict) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: System-level instructions
            messages: List of {"role": "user/assistant", "content": "..."}
            user_context: Dictionary with personality, mood, etc.

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name"""
        pass
    
    async def generate_with_retry(
        self, 
        system_prompt: str, 
        messages: List[Dict[str, str]], 
        user_context: Dict
    ) -> str:
        """
        Generate with automatic retry logic (can be overridden)
        
        Returns:
            Generated response text
        """
        return await self.generate(system_prompt, messages, user_context)