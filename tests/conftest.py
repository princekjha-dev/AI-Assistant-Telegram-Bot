"""
Pytest conftest — Set required env vars before any imports.
"""
import os

# Set dummy values so Settings() can be instantiated in tests
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token_placeholder")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_placeholder")
