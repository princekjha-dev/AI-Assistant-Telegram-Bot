"""
Nexus — /start, /help, /about handlers
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.helpers import HELP_TEXT, WELCOME_NEW, WELCOME_RETURNING, main_menu_keyboard
from app.config import settings
from app.database import get_session
from app.database.repositories import get_or_create_user

logger = logging.getLogger("nexus.handler.start")


async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    async with get_session() as session:
        user, created = await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

        if created:
            text = WELCOME_NEW.format(name=user.display_name)
        else:
            stats = user.stats
            if stats:
                text = WELCOME_RETURNING.format(
                    name=user.display_name,
                    streak=stats.streak_days,
                    points=stats.points,
                    level=stats.level,
                    messages=stats.total_messages,
                )
            else:
                text = WELCOME_NEW.format(name=user.display_name)

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


async def help_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def about_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"🤖 *Nexus AI Assistant* v{settings.BOT_VERSION}\n\n"
        "A fully self-hosted Telegram AI companion with:\n"
        "• Multi-model AI via OpenRouter\n"
        "• Long-term memory & personality\n"
        "• Image generation\n"
        "• Voice & file support\n"
        "• Gamification & achievements\n"
        "• Reminders & productivity tools\n\n"
        "_Built with ❤️ using Python & python-telegram-bot_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
