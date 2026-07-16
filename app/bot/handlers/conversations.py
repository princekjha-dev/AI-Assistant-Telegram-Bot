"""
Nexus — Conversation management handlers
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update as sa_update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.database import get_session
from app.database.models import Conversation, Message
from app.database.repositories import get_or_create_user

logger = logging.getLogger("nexus.handler.conversation")


async def new_conversation_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/new — Start a new conversation."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)

        # Deactivate current conversations
        await session.execute(
            sa_update(Conversation)
            .where(Conversation.user_id == user.id, Conversation.is_active == True)
            .values(is_active=False)
        )

        # Create new one
        conv = Conversation(user_id=user.id, title="New Chat", is_active=True)
        session.add(conv)

    await update.message.reply_text(
        "✨ *New conversation started!*\n\nFresh slate. What's on your mind?",
        parse_mode=ParseMode.MARKDOWN,
    )


async def history_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/history — Browse conversation history."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc())
            .limit(10)
        )
        convs = result.scalars().all()
        conv_data = [(c.id, c.title, c.is_active, c.created_at) for c in convs]

    if not conv_data:
        await update.message.reply_text("📚 No conversation history yet. Start chatting!")
        return

    lines = ["📚 *Conversation History*\n"]
    for cid, title, active, created in conv_data:
        status = "✅ Active" if active else ""
        date = created.strftime("%b %d") if created else ""
        lines.append(f"*#{cid}* {title or 'Untitled'} {status}\n   _📅 {date}_")

    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )


async def export_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/export — Export current conversation as JSON."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id, Conversation.is_active == True)
            .order_by(Conversation.updated_at.desc())
            .limit(1)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            await update.message.reply_text("No active conversation to export.")
            return

        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        export_data = {
            "conversation_id": conv.id,
            "title": conv.title,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        }

    export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
    export_bytes = export_json.encode("utf-8")

    await update.message.reply_document(
        document=export_bytes,
        filename=f"nexus_conversation_{conv.id}.json",
        caption=f"📤 Exported: *{conv.title}* ({len(messages)} messages)",
        parse_mode=ParseMode.MARKDOWN,
    )


async def branch_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/branch — Fork the current conversation."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id, Conversation.is_active == True)
            .limit(1)
        )
        parent = result.scalar_one_or_none()

        if not parent:
            await update.message.reply_text("No active conversation to branch.")
            return

        # Deactivate parent
        await session.execute(
            sa_update(Conversation)
            .where(Conversation.id == parent.id)
            .values(is_active=False)
        )

        # Create branch
        branch = Conversation(
            user_id=user.id,
            title=f"Branch of: {parent.title}",
            is_active=True,
            parent_id=parent.id,
            summary=parent.summary,
        )
        session.add(branch)

    await update.message.reply_text(
        f"🌿 *Conversation branched!*\n\n"
        f"Forked from: _{parent.title}_\n\n"
        "Continue from here — your original conversation is preserved.",
        parse_mode=ParseMode.MARKDOWN,
    )
