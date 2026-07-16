"""
Nexus — Entry Point
"""
from __future__ import annotations

import asyncio
import sys

from app.config import settings
from app.config.logging_config import setup_logging

setup_logging()

import logging
logger = logging.getLogger("nexus")


def main() -> None:
    logger.info("=" * 60)
    logger.info("  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗")
    logger.info("  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝")
    logger.info("  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗")
    logger.info("  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║")
    logger.info("  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║")
    logger.info("  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝")
    logger.info("=" * 60)
    logger.info("  Nexus AI Assistant v%s", settings.BOT_VERSION)
    logger.info("  Mode: %s | Model: %s", settings.MODE.upper(), settings.OPENROUTER_MODEL)
    logger.info("=" * 60)

    from app.bot.app import run_polling, run_webhook

    if settings.MODE.lower() == "webhook":
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
