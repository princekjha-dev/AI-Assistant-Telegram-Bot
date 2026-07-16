"""
Root-level conftest — ensures environment variables are set
BEFORE any application module is imported.
This file is discovered by pytest first due to its root location.
"""
import os

# Must be set before any app module imports
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token_12345")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_12345")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///data/test_nexus.db")
