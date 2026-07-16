"""
Nexus — Personality command handlers
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.ai.personalities import get_personality, list_personalities
from app.bot.helpers import personality_keyboard
from app.database import get_session
from app.database.repositories import get_or_create_user, update_user_personality

logger = logging.getLogger("nexus.handler.personality")


async def personality_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/personality — Show personality selection menu."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id, username=tg_user.username)
        current = get_personality(user.personality)

    text = (
        f"🎭 *AI Personality*\n\n"
        f"Current: {current.icon} *{current.name}*\n"
        f"_{current.description}_\n\n"
        "Choose a new personality:"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=personality_keyboard(),
    )


async def set_personality_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/setpersonality <name> — Set personality directly."""
    if not ctx.args:
        await update.message.reply_text(
            "Usage: `/setpersonality <name>`\n\nAvailable: friendly, professional, motivational, sarcastic, creative",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    key = ctx.args[0].lower()
    p = get_personality(key)
    if p.key != key and key not in ("friendly", "professional", "motivational", "sarcastic", "creative"):
        await update.message.reply_text("❌ Unknown personality. Try: friendly, professional, motivational, sarcastic, creative")
        return

    tg_user = update.effective_user
    async with get_session() as session:
        await get_or_create_user(session, tg_user.id, username=tg_user.username)
        await update_user_personality(session, tg_user.id, p.key)

    await update.message.reply_text(
        f"{p.icon} Personality switched to *{p.name}*!\n\n_{p.greeting}_",
        parse_mode=ParseMode.MARKDOWN,
    )
