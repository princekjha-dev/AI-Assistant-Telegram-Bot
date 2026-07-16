"""
Nexus — Image Generation Handler
"""
from __future__ import annotations

import logging
import base64
import io

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from app.ai.client import openrouter
from app.bot.middleware.rate_limit import is_rate_limited
from app.config import settings
from app.database import get_session
from app.database.repositories import get_or_create_user
from app.gamification import award_xp

logger = logging.getLogger("nexus.handler.image")


async def image_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/image <prompt> — Generate an image."""
    if not settings.IMAGE_GENERATION_ENABLED:
        await update.message.reply_text("🎨 Image generation is currently disabled.")
        return

    if not ctx.args:
        await update.message.reply_text(
            "🎨 *Image Generation*\n\nUsage: `/image <description>`\n\n"
            "Example: `/image A cyberpunk city at night with neon lights`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    prompt = " ".join(ctx.args)
    tg_user = update.effective_user

    # Rate limit
    limited, reason = is_rate_limited(tg_user.id)
    if limited:
        await update.message.reply_text(reason)
        return

    thinking_msg = await update.message.reply_text(
        f"🎨 *Creating your image...*\n\n`{prompt}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO)

    try:
        result = await openrouter.generate_image(prompt)

        if result is None:
            await thinking_msg.edit_text("❌ Image generation failed. Please try again or try a different prompt.")
            return

        await thinking_msg.delete()

        # Handle URL vs base64
        if result.startswith("http"):
            await update.message.reply_photo(
                photo=result,
                caption=f"🎨 *{prompt[:200]}*",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            # base64
            img_bytes = base64.b64decode(result)
            await update.message.reply_photo(
                photo=io.BytesIO(img_bytes),
                caption=f"🎨 *{prompt[:200]}*",
                parse_mode=ParseMode.MARKDOWN,
            )

        # Award XP
        async with get_session() as session:
            user, _ = await get_or_create_user(session, tg_user.id)
            earned = await award_xp(session, user, "image")

        if earned:
            await update.message.reply_text(
                "🎉 *Achievement Unlocked!*\n" + "\n".join(earned),
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as exc:
        logger.error("Image generation error: %s", exc, exc_info=True)
        await thinking_msg.edit_text(
            "😅 Couldn't generate the image right now. Please try again later."
        )
