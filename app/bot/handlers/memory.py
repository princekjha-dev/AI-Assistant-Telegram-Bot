"""
Nexus — Memory management handlers
"""
from __future__ import annotations

import logging

from sqlalchemy import select, delete as sa_delete
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.database import get_session
from app.database.models import Memory
from app.database.repositories import get_or_create_user

logger = logging.getLogger("nexus.handler.memory")


async def memory_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/memory — Show memory management menu."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        result = await session.execute(
            select(Memory).where(Memory.user_id == user.id).order_by(Memory.created_at.desc())
        )
        memories = result.scalars().all()
        memory_list = [(m.id, m.fact) for m in memories]

    if not memory_list:
        text = (
            "🧠 *Your Memory*\n\n"
            "I don't have any saved facts about you yet.\n\n"
            "I automatically learn from our conversations, or you can add facts manually!"
        )
    else:
        facts_text = "\n".join(f"• {fact}" for _, fact in memory_list[:20])
        text = f"🧠 *Your Memory* ({len(memory_list)} facts)\n\n{facts_text}"
        if len(memory_list) > 20:
            text += f"\n\n_... and {len(memory_list) - 20} more_"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Fact", callback_data="memory_add")],
        [InlineKeyboardButton("🗑️ Clear All Memories", callback_data="memory_clear_confirm")],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def memory_add_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/memoryadd <fact> — Add a memory fact."""
    if not ctx.args:
        await update.message.reply_text(
            "Usage: `/memoryadd <fact>`\n\nExample: `/memoryadd I love hiking on weekends`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    fact = " ".join(ctx.args)
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        mem = Memory(user_id=user.id, fact=fact, category="manual")
        session.add(mem)

    await update.message.reply_text(
        f"✅ Memory saved!\n\n_\"{fact}\"_\n\nI'll remember this in our future conversations.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def memory_clear_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/memoryclear — Clear all memories."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        await session.execute(sa_delete(Memory).where(Memory.user_id == user.id))

    await update.message.reply_text("🧹 All memories cleared. I'll start fresh!")
