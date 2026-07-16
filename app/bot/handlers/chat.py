"""
Nexus — Core AI Chat Handler
"""
from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from app.ai.engine import chat, auto_extract_memory
from app.bot.helpers import back_keyboard
from app.bot.middleware.rate_limit import is_rate_limited
from app.config import settings
from app.database import get_session
from app.database.repositories import get_or_create_user
from app.gamification import award_xp

logger = logging.getLogger("nexus.handler.chat")


async def _get_user_or_create(tg_user) -> tuple:
    async with get_session() as session:
        user, _ = await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
    return user


async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main message handler — handles all plain text messages.
    In groups, only responds when mentioned.
    """
    message = update.message
    if not message or not message.text:
        return

    tg_user = update.effective_user
    chat_obj = update.effective_chat

    # Group mode: only respond to mentions
    if chat_obj.type in ("group", "supergroup"):
        bot_username = ctx.bot.username
        if not (
            message.text.startswith(f"@{bot_username}") or
            (message.reply_to_message and message.reply_to_message.from_user.id == ctx.bot.id)
        ):
            return
        user_text = message.text.replace(f"@{bot_username}", "").strip()
        if not user_text:
            return
    else:
        user_text = message.text

    # Rate limiting
    limited, reason = is_rate_limited(tg_user.id)
    if limited:
        await message.reply_text(reason)
        return

    # Show typing indicator
    await ctx.bot.send_chat_action(chat_obj.id, ChatAction.TYPING)

    try:
        async with get_session() as session:
            user, _ = await get_or_create_user(
                session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
            )

            # Get context if any is set (e.g. from file upload)
            file_context = ctx.user_data.get("file_context")
            if file_context:
                del ctx.user_data["file_context"]

            reply_text, tokens = await chat(session, user, user_text, context_text=file_context)

            # Award XP
            earned = await award_xp(session, user, "message")

            # Auto-extract memories in background (don't block response)
            asyncio.create_task(
                _background_memory(user.id, user_text, reply_text)
            )

        # Send reply (split if too long)
        if len(reply_text) <= 4000:
            await message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)
        else:
            # Send in chunks
            chunks = [reply_text[i:i+4000] for i in range(0, len(reply_text), 4000)]
            for chunk in chunks:
                await message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)

        # Notify achievements
        if earned:
            achievement_text = "🎉 *New Achievement" + ("s" if len(earned) > 1 else "") + "!*\n"
            achievement_text += "\n".join(earned)
            await message.reply_text(achievement_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as exc:
        logger.error("Chat handler error: %s", exc, exc_info=True)
        await message.reply_text(
            "😅 Oops! Something went wrong. Please try again in a moment.",
        )


async def _background_memory(user_id: int, user_msg: str, reply: str) -> None:
    """Background task to extract and save memories."""
    try:
        async with get_session() as session:
            from sqlalchemy import select
            from app.database.models import User
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                await auto_extract_memory(session, user, user_msg, reply)
    except Exception as exc:
        logger.debug("Background memory task error: %s", exc)


async def chat_command_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/chat <message> command."""
    if not ctx.args:
        await update.message.reply_text(
            "Usage: `/chat <your message>`\n\nOr just type directly!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Reuse main message handler
    update.message.text = " ".join(ctx.args)
    await message_handler(update, ctx)
