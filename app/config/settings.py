"""
Nexus Bot — Application Settings
Loaded from environment variables / .env file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Core Credentials ──────────────────────────────────
    TELEGRAM_BOT_TOKEN: str
    OPENROUTER_API_KEY: str

    # ── AI ────────────────────────────────────────────────
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    CONTEXT_WINDOW: int = 20  # number of recent messages kept in context

    # ── Image Generation ──────────────────────────────────
    IMAGE_PROVIDER: str = "openrouter"
    IMAGE_MODEL: str = "black-forest-labs/flux-schnell"
    IMAGE_GENERATION_ENABLED: bool = True

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///data/nexus.db"

    # ── Bot Mode ─────────────────────────────────────────
    MODE: str = "polling"
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PORT: int = 8443
    WEBHOOK_SECRET: Optional[str] = None

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    MAX_REQUESTS_PER_MINUTE: int = 20
    MAX_REQUESTS_PER_DAY: int = 500

    # ── Logging ───────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/nexus.log"

    # ── Features ──────────────────────────────────────────
    VOICE_ENABLED: bool = True
    GAMIFICATION_ENABLED: bool = True
    GROUP_MODE_ENABLED: bool = True

    # ── Admin ─────────────────────────────────────────────
    ADMIN_USER_IDS: str = ""  # comma-separated

    # ── App Meta ──────────────────────────────────────────
    BOT_NAME: str = "Nexus"
    BOT_VERSION: str = "1.0.0"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_sqlite_url(cls, v: str) -> str:
        """Ensure SQLite async driver is used."""
        if v.startswith("sqlite:///") and "aiosqlite" not in v:
            return v.replace("sqlite:///", "sqlite+aiosqlite:///")
        return v

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_USER_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_USER_IDS.split(",") if x.strip()]

    @property
    def db_path(self) -> Path:
        """Return the file path for SQLite databases."""
        if "sqlite" in self.DATABASE_URL:
            raw = self.DATABASE_URL.split("///")[-1]
            return Path(raw)
        return Path("data/nexus.db")


settings = Settings()

# Ensure required directories exist
settings.db_path.parent.mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)
