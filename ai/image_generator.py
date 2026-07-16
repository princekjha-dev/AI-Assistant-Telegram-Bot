"""
Image Generation Module
Supports multiple providers: Hugging Face, Replicate, DALL-E
"""

import httpx
import asyncio
import logging
from typing import Optional, Tuple
from pathlib import Path
import base64
import config
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generate images using various AI providers"""
    
    def __init__(self):
        self.hf_token = config.HF_API_TOKEN
        self.replicate_token = config.REPLICATE_API_TOKEN
        self.storage_path = Path(config.GENERATED_IMAGES_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def generate_image(
        self, 
        prompt: str, 
        style: str = "realistic",
        size: str = "768x768",
        provider: str = "huggingface"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate an image from text prompt
        
        Args:
            prompt: Text description of the image to generate
            style: Image style (realistic, anime, painting, etc.)
            size: Image dimensions (512x512, 768x768, 1024x1024)
            provider: Which provider to use (huggingface, replicate, openrouter)
            
        Returns:
            Tuple of (image_path, error_message)
        """
        if not config.ENABLE_IMAGE_GENERATION:
            return None, "❌ Image generation is not enabled"
        
        # Enhance prompt with style
        enhanced_prompt = f"{prompt}, {style} style, high quality, detailed"
        
        try:
            if provider == "huggingface" and self.hf_token:
                return await self._generate_hf(enhanced_prompt, size)
            elif provider == "replicate" and self.replicate_token:
                return await self._generate_replicate(enhanced_prompt, size)
            elif provider == "openrouter":
                return await self._generate_openrouter(enhanced_prompt, size)
            else:
                return None, f"❌ Provider '{provider}' not configured"
                
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}", exc_info=True)
            return None, f"❌ Image generation failed: {str(e)}"

    async def _generate_hf(self, prompt: str, size: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate using Hugging Face Inference API"""
        try:
            width, height = map(int, size.split('x'))
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "height": height,
                    "width": width,
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5
                }
            }
            
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                # Save image
                image_path = await self._save_image(response.content, "png", prompt)
                return image_path, None
                
        except Exception as e:
            logger.error(f"HuggingFace generation error: {str(e)}")
            return None, str(e)

    async def _generate_replicate(self, prompt: str, size: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate using Replicate API"""
        try:
            width, height = map(int, size.split('x'))
            
            headers = {"Authorization": f"Token {self.replicate_token}"}
            
            # Create prediction
            payload = {
                "version": "f1769f2f9e0042f1c8ca7f89e1d6d5e5f8f0f9f0",  # Stable Diffusion v2
                "input": {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "num_outputs": 1,
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Create prediction
                pred_response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers=headers,
                    json=payload
                )
                pred_response.raise_for_status()
                prediction = pred_response.json()
                
                # Poll for completion
                max_retries = 30
                for _ in range(max_retries):
                    if prediction["status"] == "succeeded":
                        image_url = prediction["output"][0]
                        
                        # Download image
                        img_response = await client.get(image_url)
                        img_response.raise_for_status()
                        
                        image_path = await self._save_image(img_response.content, "png", prompt)
                        return image_path, None
                    elif prediction["status"] == "failed":
                        return None, f"Prediction failed: {prediction.get('error', 'Unknown error')}"
                    
                    await asyncio.sleep(2)
                
                return None, "Generation timeout"
                
        except Exception as e:
            logger.error(f"Replicate generation error: {str(e)}")
            return None, str(e)

    async def _generate_openrouter(self, prompt: str, size: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate using OpenRouter image API"""
        try:
            headers = {
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "openrouter/auto",
                "prompt": prompt,
                "width": int(size.split('x')[0]),
                "height": int(size.split('x')[1]),
                "steps": 50,
                "guidance_scale": 7.5
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{config.OPENROUTER_BASE_URL}/images/generations",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0].get("url") or data["data"][0].get("b64_json")
                    
                    # If base64, decode and save
                    if image_url.startswith("data:"):
                        image_data = base64.b64decode(image_url.split(",")[1])
                    else:
                        img_response = await client.get(image_url)
                        img_response.raise_for_status()
                        image_data = img_response.content
                    
                    image_path = await self._save_image(image_data, "png", prompt)
                    return image_path, None
                else:
                    return None, "No image generated"
                    
        except Exception as e:
            logger.error(f"OpenRouter image generation error: {str(e)}")
            return None, str(e)

    async def _save_image(self, image_data: bytes, format: str, prompt: str) -> str:
        """Save image to storage"""
        try:
            # Create unique filename based on timestamp and prompt hash
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
            filename = f"gen_{timestamp}_{prompt_hash}.{format}"
            
            filepath = self.storage_path / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Image saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            return ""

    async def enhance_prompt(self, basic_prompt: str) -> str:
        """Enhance prompt for better results using Claude/OpenRouter"""
        from llm.openrouter import OpenRouterClient
        
        client = OpenRouterClient()
        
        system = "You are an expert at writing detailed, creative image generation prompts. Enhance the given prompt with vivid details, style, lighting, and quality descriptors. Return only the enhanced prompt, nothing else."
        messages = [{"role": "user", "content": f"Enhance this prompt: {basic_prompt}"}]
        
        try:
            enhanced = await client.generate(system, messages, {"temperature": 0.8})
            return enhanced.strip()
        except:
            return basic_prompt

    def get_storage_usage(self) -> Tuple[int, int]:
        """Get storage usage statistics
        
        Returns:
            Tuple of (file_count, total_size_bytes)
        """
        try:
            files = list(self.storage_path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            return len(files), total_size
        except:
            return 0, 0

    async def cleanup_old_images(self, max_age_days: int = 30):
        """Remove images older than specified days"""
        from datetime import datetime, timedelta
        
        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            for filepath in self.storage_path.glob("*"):
                if filepath.stat().st_mtime < cutoff_timestamp:
                    filepath.unlink()
                    logger.info(f"Deleted old image: {filepath}")
                    
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
