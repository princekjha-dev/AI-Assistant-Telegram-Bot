"""
Nexus — File & Document Handlers (Photos, PDFs, text files)
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from app.database import get_session
from app.database.repositories import get_or_create_user
from app.gamification import award_xp
from app.media import extract_text_from_bytes, truncate_text

logger = logging.getLogger("nexus.handler.file")

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


async def document_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads (PDFs, text files, etc.)."""
    doc = update.message.document
    if not doc:
        return

    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("📁 File too large! I can handle files up to 20 MB.")
        return

    tg_user = update.effective_user
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    status_msg = await update.message.reply_text(
        f"📄 *Processing {doc.file_name}...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        file_obj = await ctx.bot.get_file(doc.file_id)
        file_bytes = await file_obj.download_as_bytearray()
        file_bytes = bytes(file_bytes)

        text = await extract_text_from_bytes(file_bytes, doc.mime_type or "", doc.file_name or "")

        if not text:
            await status_msg.edit_text(
                "❌ Couldn't extract text from this file. I support: PDFs, TXT, MD, CSV, JSON, and code files."
            )
            return

        truncated = truncate_text(text, max_chars=6000)
        char_count = len(text)

        caption = (
            f"📄 *File loaded:* {doc.file_name}\n"
            f"📊 {char_count:,} characters extracted\n\n"
            "✅ File content loaded into our conversation!\n"
            "Ask me anything about it. For example:\n"
            '• _"Summarise this document"_\n'
            '• _"What are the key points?"_\n'
            '• _"Explain section 2"_'
        )

        # Store context for next message
        ctx.user_data["file_context"] = f"Document '{doc.file_name}':\n\n{truncated}"
        ctx.user_data["file_name"] = doc.file_name

        await status_msg.edit_text(caption, parse_mode=ParseMode.MARKDOWN)

        # Award XP
        async with get_session() as session:
            user, _ = await get_or_create_user(session, tg_user.id)
            await award_xp(session, user, "file")

    except Exception as exc:
        logger.error("Document handler error: %s", exc, exc_info=True)
        await status_msg.edit_text("😅 Had trouble reading that file. Please try again!")


async def photo_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages — describe or analyse image."""
    photo = update.message.photo
    if not photo:
        return

    tg_user = update.effective_user
    caption = update.message.caption or "Describe this image in detail."

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    status_msg = await update.message.reply_text("🔍 *Analysing image...*", parse_mode=ParseMode.MARKDOWN)

    try:
        # Get the highest resolution photo
        best_photo = max(photo, key=lambda p: p.width * p.height)
        photo_file = await ctx.bot.get_file(best_photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        photo_bytes = bytes(photo_bytes)

        # Use vision-capable model via OpenRouter with base64 image
        import base64
        from app.ai.client import openrouter
        from app.config import settings

        b64_image = base64.b64encode(photo_bytes).decode()
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                    {"type": "text", "text": caption},
                ],
            }
        ]

        # Use a vision-capable model
        vision_model = "anthropic/claude-3.5-sonnet"
        data = await openrouter.chat(messages, model=vision_model)
        reply = data["choices"][0]["message"]["content"]

        await status_msg.delete()
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

        async with get_session() as session:
            user, _ = await get_or_create_user(session, tg_user.id)
            await award_xp(session, user, "file")

    except Exception as exc:
        logger.error("Photo handler error: %s", exc, exc_info=True)
        await status_msg.edit_text(
            "😅 I couldn't analyse that photo. Make sure you're using a vision-capable model."
        )
