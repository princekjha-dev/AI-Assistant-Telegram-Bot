"""
Configuration file for the AI Bot
Supports environment variables and defaults
"""

import os
from pathlib import Path

# Custom .env parser (more reliable than python-dotenv on Windows)
def load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# ============================================================================
# API KEYS & CREDENTIALS
# ============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-token-here")

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Image generation
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
# Available providers: openrouter, openai, gemini, anthropic
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# Primary model configuration (provider-agnostic names)
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-4-turbo")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "claude-3-sonnet")

# Image generation model
IMAGE_GENERATION_MODEL = os.getenv("IMAGE_GENERATION_MODEL", "stabilityai/stable-diffusion-3")

# Model parameters
MAX_RESPONSE_TOKENS = int(os.getenv("MAX_RESPONSE_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("TOP_P", "1.0"))
CONTEXT_WINDOW_SIZE = int(os.getenv("CONTEXT_WINDOW_SIZE", "10"))

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/bot_database.db")
DATABASE_BACKUP_PATH = os.getenv("DATABASE_BACKUP_PATH", "./data/backups")

# ============================================================================
# RATE LIMITING & SECURITY
# ============================================================================
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_MAX_REQUESTS = RATE_LIMIT_REQUESTS  # Alias for compatibility
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
ALLOWED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "gif"]

# ============================================================================
# PERSONALITY & MOOD
# ============================================================================
AVAILABLE_PERSONALITIES = ["friendly", "professional", "motivational", "sarcastic", "creative"]
AVAILABLE_MOODS = ["happy", "sad", "stressed", "angry", "neutral", "excited", "thoughtful"]
DEFAULT_PERSONALITY = "friendly"
DEFAULT_MOOD = "neutral"

# ============================================================================
# GAMIFICATION
# ============================================================================
STREAK_RESET_HOURS = int(os.getenv("STREAK_RESET_HOURS", "24"))
POINTS_PER_MESSAGE = int(os.getenv("POINTS_PER_MESSAGE", "10"))
POINTS_PER_IMAGE = int(os.getenv("POINTS_PER_IMAGE", "25"))
POINTS_MULTIPLIER_STREAK = float(os.getenv("POINTS_MULTIPLIER_STREAK", "1.2"))

# ============================================================================
# FEATURE FLAGS
# ============================================================================
ENABLE_IMAGE_GENERATION = os.getenv("ENABLE_IMAGE_GENERATION", "true").lower() == "true"
ENABLE_VOICE = os.getenv("ENABLE_VOICE", "true").lower() == "true"
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_PREMIUM_FEATURES = os.getenv("ENABLE_PREMIUM_FEATURES", "false").lower() == "true"

# ============================================================================
# LOGGING & DEBUG
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "./logs/bot.log")
SAVE_CONVERSATIONS = os.getenv("SAVE_CONVERSATIONS", "true").lower() == "true"

# ============================================================================
# PERFORMANCE & CACHING
# ============================================================================
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds
USE_ASYNC = os.getenv("USE_ASYNC", "true").lower() == "true"

# ============================================================================
# DEPLOYMENT
# ============================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # For production webhook mode
POLLING_MODE = os.getenv("POLLING_MODE", "true").lower() == "true"

# ============================================================================
# STORAGE & MEDIA
# ============================================================================
MEDIA_STORAGE_PATH = os.getenv("MEDIA_STORAGE_PATH", "./data/media")
GENERATED_IMAGES_PATH = os.getenv("GENERATED_IMAGES_PATH", "./data/generated_images")
MAX_STORED_CONVERSATIONS = int(os.getenv("MAX_STORED_CONVERSATIONS", "100"))

# ============================================================================
# OPENROUTER SPECIFIC CONFIGURATION
# ============================================================================
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_TIMEOUT = int(os.getenv("OPENROUTER_TIMEOUT", "60"))
REQUEST_RETRY_ATTEMPTS = int(os.getenv("REQUEST_RETRY_ATTEMPTS", "3"))
REQUEST_RETRY_DELAY = int(os.getenv("REQUEST_RETRY_DELAY", "2"))

# ============================================================================
# API INTEGRATION SETTINGS
# ============================================================================
# Only OpenRouter is enabled as primary LLM provider
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
USE_FALLBACK_ON_ERROR = os.getenv("USE_FALLBACK_ON_ERROR", "true").lower() == "true"

# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate critical configuration settings"""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your-telegram-token-here":
        errors.append("TELEGRAM_BOT_TOKEN is not configured")
    
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your-openrouter-key-here":
        errors.append("OPENROUTER_API_KEY is not configured")
    
    if ENABLE_IMAGE_GENERATION and not HF_API_TOKEN and not REPLICATE_API_TOKEN:
        errors.append("Image generation enabled but no image API key configured (set HF_API_TOKEN or REPLICATE_API_TOKEN)")
