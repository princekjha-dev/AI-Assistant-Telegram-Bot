"""
Tests for the Nexus main entrypoint.
"""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_main_module_importable():
    main = importlib.import_module("main")
    assert hasattr(main, "main")
    assert callable(main.main)


def test_settings_have_defaults():
    from app.config.settings import Settings
    # Create with required fields only
    s = Settings(TELEGRAM_BOT_TOKEN="tok", OPENROUTER_API_KEY="key")
    assert s.OPENROUTER_MODEL == "anthropic/claude-3.5-sonnet"
    assert s.MODE == "polling"
    assert s.MAX_TOKENS == 2048
    assert s.TEMPERATURE == 0.7


def test_settings_sqlite_url_fixed():
    from app.config.settings import Settings
    s = Settings(
        TELEGRAM_BOT_TOKEN="tok",
        OPENROUTER_API_KEY="key",
        DATABASE_URL="sqlite:///data/test.db",
    )
    assert "aiosqlite" in s.DATABASE_URL
