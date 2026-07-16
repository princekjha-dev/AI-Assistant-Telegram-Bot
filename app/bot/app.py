"""
Nexus — Main Bot Application
Wires all handlers together and starts the bot.
"""
from __future__ import annotations

import asyncio
import logging

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.database import init_db
from app.gamification import ensure_achievements_seeded
from app.database import get_session
from app.services import reminder_loop

# ── Handlers ────────────────────────────────────────────────────────────
from app.bot.handlers.start import start_handler, help_handler, about_handler
from app.bot.handlers.chat import message_handler, chat_command_handler
from app.bot.handlers.personality import personality_handler, set_personality_handler
from app.bot.handlers.memory import memory_handler, memory_add_handler, memory_clear_handler
from app.bot.handlers.image import image_handler
from app.bot.handlers.voice import voice_handler
from app.bot.handlers.files import document_handler, photo_handler
from app.bot.handlers.reminders import remind_handler, reminders_handler, del_reminder_handler
from app.bot.handlers.profile import profile_handler, stats_handler, achievements_handler, leaderboard_handler
from app.bot.handlers.conversations import new_conversation_handler, history_handler, export_handler, branch_handler
from app.bot.handlers.settings import settings_handler, model_handler
from app.bot.handlers.callbacks import callback_handler

logger = logging.getLogger("nexus.app")

BOT_COMMANDS = [
    BotCommand("start", "Welcome & main menu"),
    BotCommand("help", "Command reference"),
    BotCommand("about", "About Nexus"),
    BotCommand("chat", "Chat with AI"),
    BotCommand("new", "Start new conversation"),
    BotCommand("history", "Browse conversations"),
    BotCommand("export", "Export conversation"),
    BotCommand("branch", "Fork conversation"),
    BotCommand("personality", "Change AI personality"),
    BotCommand("setpersonality", "Set personality directly"),
    BotCommand("model", "View/change AI model"),
    BotCommand("settings", "Bot settings"),
    BotCommand("memory", "View your memories"),
    BotCommand("memoryadd", "Add a memory fact"),
    BotCommand("memoryclear", "Clear all memories"),
    BotCommand("image", "Generate an image"),
    BotCommand("remind", "Set a reminder"),
    BotCommand("reminders", "List reminders"),
    BotCommand("delreminder", "Delete a reminder"),
    BotCommand("profile", "Your profile & XP"),
    BotCommand("stats", "Detailed statistics"),
    BotCommand("achievements", "View achievements"),
    BotCommand("leaderboard", "Global leaderboard"),
]


def build_application() -> Application:
    """Build and configure the Telegram Application."""
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # ── Command Handlers ──────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("about", about_handler))

    app.add_handler(CommandHandler("chat", chat_command_handler))
    app.add_handler(CommandHandler("new", new_conversation_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("export", export_handler))
    app.add_handler(CommandHandler("branch", branch_handler))

    app.add_handler(CommandHandler("personality", personality_handler))
    app.add_handler(CommandHandler("setpersonality", set_personality_handler))
    app.add_handler(CommandHandler("model", model_handler))
    app.add_handler(CommandHandler("settings", settings_handler))

    app.add_handler(CommandHandler("memory", memory_handler))
    app.add_handler(CommandHandler("memoryadd", memory_add_handler))
    app.add_handler(CommandHandler("memoryclear", memory_clear_handler))

    app.add_handler(CommandHandler("image", image_handler))

    app.add_handler(CommandHandler("remind", remind_handler))
    app.add_handler(CommandHandler("reminders", reminders_handler))
    app.add_handler(CommandHandler("delreminder", del_reminder_handler))

    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("achievements", achievements_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))

    # ── Callback Queries (inline buttons) ─────────────────
    app.add_handler(CallbackQueryHandler(callback_handler))

    # ── Media Handlers ────────────────────────────────────
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # ── General Message Handler (must be last) ────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    return app


async def post_init(app: Application) -> None:
    """Called after application initialisation."""
    await init_db()
    async with get_session() as session:
        await ensure_achievements_seeded(session)
    await app.bot.set_my_commands(BOT_COMMANDS)
    logger.info("Nexus v%s initialised ✓", settings.BOT_VERSION)

    # Start reminder loop as background task
    asyncio.create_task(reminder_loop(app))


async def run_polling() -> None:
    """Run the bot in polling mode."""
    app = build_application()
    app.post_init = post_init  # type: ignore

    logger.info("Starting Nexus in POLLING mode...")
    await app.initialize()
    await post_init(app)
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    logger.info("Nexus is running! Press Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def run_webhook() -> None:
    """Run the bot in webhook mode."""
    if not settings.WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL must be set when MODE=webhook")

    app = build_application()

    logger.info("Starting Nexus in WEBHOOK mode on port %s...", settings.WEBHOOK_PORT)
    await app.initialize()
    await post_init(app)
    await app.start()

    webhook_url = f"{settings.WEBHOOK_URL.rstrip('/')}/webhook"
    await app.bot.set_webhook(
        url=webhook_url,
        secret_token=settings.WEBHOOK_SECRET,
        drop_pending_updates=True,
    )

    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=settings.WEBHOOK_PORT,
        secret_token=settings.WEBHOOK_SECRET,
        webhook_url=webhook_url,
    )

    logger.info("Webhook listening at %s", webhook_url)
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
