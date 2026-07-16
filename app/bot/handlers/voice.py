"""
Nexus — Voice Message Handler
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from app.ai.client import openrouter
from app.ai.engine import chat
from app.config import settings
from app.database import get_session
from app.database.repositories import get_or_create_user
from app.gamification import award_xp
from app.media import convert_ogg_to_wav

logger = logging.getLogger("nexus.handler.voice")


async def voice_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Telegram voice messages."""
    if not settings.VOICE_ENABLED:
        await update.message.reply_text("🎤 Voice support is currently disabled.")
        return

    voice = update.message.voice
    if not voice:
        return

    tg_user = update.effective_user
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    status_msg = await update.message.reply_text("🎤 *Processing voice message...*", parse_mode=ParseMode.MARKDOWN)

    try:
        # Download voice file
        voice_file = await ctx.bot.get_file(voice.file_id)
        ogg_bytes = await voice_file.download_as_bytearray()
        ogg_bytes = bytes(ogg_bytes)

        # Try to transcribe
        transcript = await openrouter.transcribe_audio(ogg_bytes, "voice.ogg")

        if not transcript:
            # Fallback: use convert_ogg_to_wav and retry
            wav_bytes = await convert_ogg_to_wav(ogg_bytes)
            transcript = await openrouter.transcribe_audio(wav_bytes, "voice.wav")

        if not transcript:
            await status_msg.edit_text(
                "🎤 I heard your voice, but couldn't transcribe it. "
                "Please check your audio or try speaking more clearly."
            )
            return

        await status_msg.edit_text(
            f"🎤 *Transcription:*\n_{transcript}_\n\n⏳ Thinking...",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Get AI reply
        async with get_session() as session:
            user, _ = await get_or_create_user(session, tg_user.id)
            reply, _ = await chat(session, user, transcript)
            await award_xp(session, user, "voice")

        await status_msg.edit_text(
            f"🎤 *You said:*\n_{transcript}_\n\n🤖 *Nexus:*\n{reply}",
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as exc:
        logger.error("Voice handler error: %s", exc, exc_info=True)
        await status_msg.edit_text("😅 Had trouble processing your voice message. Please try again!")
