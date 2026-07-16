"""
Nexus — Callback Query Handler
Handles all inline keyboard button presses.
"""
from __future__ import annotations

import logging

from sqlalchemy import delete as sa_delete
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.ai.personalities import get_personality
from app.bot.helpers import main_menu_keyboard, personality_keyboard, HELP_TEXT
from app.database import get_session
from app.database.models import Memory
from app.database.repositories import get_or_create_user, update_user_personality

logger = logging.getLogger("nexus.handler.callbacks")


async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Route callback queries to appropriate handlers."""
    query = update.callback_query
    await query.answer()

    data = query.data
    tg_user = update.effective_user

    try:
        # ── Personality ──────────────────────────────────
        if data.startswith("set_personality:"):
            key = data.split(":", 1)[1]
            p = get_personality(key)
            async with get_session() as session:
                await get_or_create_user(session, tg_user.id)
                await update_user_personality(session, tg_user.id, p.key)

            await query.edit_message_text(
                f"{p.icon} *Personality: {p.name}*\n\n_{p.greeting}_",
                parse_mode=ParseMode.MARKDOWN,
            )

            # Track for AI Explorer achievement
            used = ctx.user_data.setdefault("personalities_tried", set())
            used.add(key)

        elif data == "personality_menu":
            await query.edit_message_text(
                "🎭 *Choose a personality:*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=personality_keyboard(),
            )

        # ── Model selection ──────────────────────────────
        elif data.startswith("set_model:"):
            model_id = data.split(":", 1)[1]
            async with get_session() as session:
                user, _ = await get_or_create_user(session, tg_user.id)
                user.preferred_model = model_id

            await query.edit_message_text(
                f"✅ AI model set to:\n`{model_id}`",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif data == "model_select":
            from app.bot.handlers.settings import POPULAR_MODELS
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            async with get_session() as session:
                user, _ = await get_or_create_user(session, tg_user.id)
                current = user.preferred_model or ""

            buttons = []
            for model_id, label in POPULAR_MODELS:
                check = "✅ " if model_id == current else ""
                buttons.append([InlineKeyboardButton(f"{check}{label}", callback_data=f"set_model:{model_id}")])
            buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

        # ── Memory ───────────────────────────────────────
        elif data == "memory_view":
            from app.bot.handlers.memory import memory_handler
            await query.delete_message()
            await memory_handler(update, ctx)

        elif data == "memory_add":
            await query.edit_message_text(
                "➕ *Add a Memory Fact*\n\nUse the command:\n`/memoryadd <fact about yourself>`\n\n"
                "Example: `/memoryadd I prefer concise answers`",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif data == "memory_clear_confirm":
            from app.bot.helpers import confirm_keyboard
            await query.edit_message_text(
                "🗑️ *Clear All Memories?*\n\nThis will delete all saved facts about you. This cannot be undone.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=confirm_keyboard("memory_clear_yes"),
            )

        elif data == "memory_clear_yes":
            async with get_session() as session:
                user, _ = await get_or_create_user(session, tg_user.id)
                await session.execute(sa_delete(Memory).where(Memory.user_id == user.id))
            await query.edit_message_text("🧹 All memories cleared! Starting fresh.")

        # ── Navigation ───────────────────────────────────
        elif data == "main_menu":
            await query.edit_message_text(
                f"🏠 *Main Menu*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard(),
            )

        elif data == "new_chat":
            from app.bot.handlers.conversations import new_conversation_handler
            await query.delete_message()
            await new_conversation_handler(update, ctx)

        elif data == "reminders_list":
            from app.bot.handlers.reminders import reminders_handler
            await query.delete_message()
            await reminders_handler(update, ctx)

        elif data == "profile":
            from app.bot.handlers.profile import profile_handler
            await query.delete_message()
            await profile_handler(update, ctx)

        elif data == "help":
            await query.edit_message_text(
                HELP_TEXT,
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        elif data == "image_prompt":
            await query.edit_message_text(
                "🎨 *Image Generation*\n\nUse the command:\n`/image <description>`\n\n"
                "Example: `/image A futuristic city skyline at sunset`",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif data == "settings":
            from app.bot.handlers.settings import settings_handler
            await query.delete_message()
            await settings_handler(update, ctx)

        elif data == "settings_reset":
            async with get_session() as session:
                user, _ = await get_or_create_user(session, tg_user.id)
                user.preferred_model = None
                user.personality = "friendly"
            await query.edit_message_text("🔄 Settings reset to defaults!")

        elif data == "cancel":
            await query.delete_message()

        else:
            logger.warning("Unknown callback: %s", data)

    except Exception as exc:
        logger.error("Callback handler error for '%s': %s", data, exc, exc_info=True)
        try:
            await query.edit_message_text("😅 Something went wrong. Please try again.")
        except Exception:
            pass
