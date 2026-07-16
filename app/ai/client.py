"""
Nexus — OpenRouter AI Client
"""
from __future__ import annotations

import logging
import time
from typing import Any, AsyncGenerator, Optional

import httpx

from app.config import settings

logger = logging.getLogger("nexus.ai.client")


class OpenRouterClient:
    """Async client wrapping OpenRouter's OpenAI-compatible API."""

    def __init__(self) -> None:
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/nexus-bot",
            "X-Title": "Nexus AI Assistant",
        }

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = settings.MAX_TOKENS,
        temperature: float = settings.TEMPERATURE,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Send a chat completion request."""
        payload = {
            "model": model or settings.OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        elapsed = time.monotonic() - start
        logger.debug(
            "OpenRouter response | model=%s | tokens=%s | latency=%.2fs",
            model or settings.OPENROUTER_MODEL,
            data.get("usage", {}).get("total_tokens", "?"),
            elapsed,
        )
        return data

    async def chat_text(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> tuple[str, int]:
        """Return (text_response, tokens_used)."""
        data = await self.chat(messages, model=model, **kwargs)
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return text, tokens

    async def generate_image(self, prompt: str) -> Optional[str]:
        """
        Generate an image via OpenRouter's image generation endpoint.
        Returns a URL or base64 string, or None on failure.
        """
        payload = {
            "model": settings.IMAGE_MODEL,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0].get("url") or data["data"][0].get("b64_json")
        except Exception as exc:
            logger.error("Image generation failed: %s", exc)
            return None

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "voice.ogg") -> Optional[str]:
        """
        Transcribe audio via a Whisper-compatible endpoint.
        Returns transcript text or None.
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (filename, audio_bytes, "audio/ogg")},
                    data={"model": "openai/whisper-1"},
                )
                response.raise_for_status()
                return response.json().get("text")
        except Exception as exc:
            logger.warning("Audio transcription failed: %s", exc)
            return None

    async def list_models(self) -> list[dict]:
        """Fetch available models from OpenRouter."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json().get("data", [])
        except Exception as exc:
            logger.warning("Could not fetch model list: %s", exc)
            return []


# Module-level singleton
openrouter = OpenRouterClient()
