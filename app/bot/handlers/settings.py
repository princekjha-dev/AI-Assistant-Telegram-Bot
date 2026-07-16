"""
Nexus — Settings & Model selection handlers
"""
from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.ai.client import openrouter
from app.config import settings
from app.database import get_session
from app.database.repositories import get_or_create_user

logger = logging.getLogger("nexus.handler.settings")

POPULAR_MODELS = [
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet 🧠"),
    ("anthropic/claude-3-haiku", "Claude 3 Haiku ⚡"),
    ("openai/gpt-4o", "GPT-4o 🤖"),
    ("openai/gpt-4o-mini", "GPT-4o Mini 💨"),
    ("google/gemini-pro-1.5", "Gemini 1.5 Pro 💎"),
    ("meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B 🦙"),
    ("mistralai/mistral-7b-instruct", "Mistral 7B 🌊"),
]


async def settings_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/settings — Bot settings menu."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        current_model = user.preferred_model or settings.OPENROUTER_MODEL
        personality = user.personality

    text = (
        f"⚙️ *Settings*\n\n"
        f"🤖 Model: `{current_model}`\n"
        f"🎭 Personality: *{personality.title()}*\n"
        f"🌐 Default Model: `{settings.OPENROUTER_MODEL}`\n\n"
        "What would you like to configure?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Change Model", callback_data="model_select")],
        [InlineKeyboardButton("🎭 Change Personality", callback_data="personality_menu")],
        [InlineKeyboardButton("🔄 Reset to Defaults", callback_data="settings_reset")],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def model_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/model — View or change AI model."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        current = user.preferred_model or settings.OPENROUTER_MODEL

    buttons = []
    for model_id, label in POPULAR_MODELS:
        check = "✅ " if model_id == current else ""
        buttons.append([InlineKeyboardButton(f"{check}{label}", callback_data=f"set_model:{model_id}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    await update.message.reply_text(
        f"🤖 *Select AI Model*\n\nCurrent: `{current}`\n\nChoose a model:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
