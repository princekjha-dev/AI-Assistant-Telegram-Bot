"""
Nexus — Shared formatting & helper utilities for handlers.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ── Text formatting ────────────────────────────────────────────────────────

def escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    specials = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in specials else c for c in text)


def progress_bar(current: int, maximum: int, length: int = 10) -> str:
    filled = int(length * current / max(maximum, 1))
    return "█" * filled + "░" * (length - filled)


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ── Keyboard builders ──────────────────────────────────────────────────────

def personality_keyboard() -> InlineKeyboardMarkup:
    from app.ai.personalities import list_personalities
    buttons = []
    for p in list_personalities():
        buttons.append([InlineKeyboardButton(
            f"{p.icon} {p.name}  —  {p.description}",
            callback_data=f"set_personality:{p.key}",
        )])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 New Chat", callback_data="new_chat"),
            InlineKeyboardButton("🧠 Memory", callback_data="memory_view"),
        ],
        [
            InlineKeyboardButton("🎨 Image", callback_data="image_prompt"),
            InlineKeyboardButton("⏰ Reminders", callback_data="reminders_list"),
        ],
        [
            InlineKeyboardButton("🏆 Profile", callback_data="profile"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ])


def back_keyboard(callback: str = "main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=callback)]])


def confirm_keyboard(yes_data: str, no_data: str = "cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=yes_data),
            InlineKeyboardButton("❌ No", callback_data=no_data),
        ]
    ])


# ── Welcome message ────────────────────────────────────────────────────────

WELCOME_NEW = """\
✨ *Welcome to Nexus!* ✨

Hey {name}! I'm *Nexus*, your intelligent AI companion — powered by cutting-edge LLMs and built to make your life easier, more creative, and more fun! 🚀

Here's what I can do:

🤖 *AI Chat* — Natural conversations with memory & personality
🎨 *Image Generation* — Create art from your imagination
🎤 *Voice Messages* — Talk to me, I'll listen
📄 *File Analysis* — PDF, text, docs — I'll read them all
⏰ *Reminders* — Natural language, recurring, smart
🧠 *Long-term Memory* — I remember what matters to you
🏆 *Gamification* — Earn XP, badges, and climb the leaderboard
👥 *Group Support* — Works in Telegram groups too!

*Quick start:* Just type a message — I'm ready to chat! 💬

Type /help to see all commands or tap a button below 👇
"""

WELCOME_RETURNING = """\
Welcome back, {name}! 👋

Great to see you again. You've got a *{streak}-day streak* going — keep it up! 🔥

Your stats: *{points} pts* • *Level {level}* • *{messages} messages*

What can I help you with today?
"""

HELP_TEXT = """\
🤖 *Nexus Command Reference*

*General*
/start — Welcome & main menu
/help — This help message
/about — About Nexus
/settings — Bot settings

*AI Chat*
/chat \\<message\\> — Chat with AI
/new — Start new conversation
/model — View/change AI model
/personality — Change AI personality
/memory — View your memories

*Media*
/image \\<prompt\\> — Generate an image
/voice — Voice message info

*Conversations*
/history — Browse conversation history
/export — Export current conversation
/branch — Create conversation branch

*Reminders*
/remind \\<text\\> — Set a reminder
/reminders — List your reminders
/delreminder \\<id\\> — Delete reminder

*Profile & Gamification*
/profile — Your profile & stats
/stats — Detailed statistics
/achievements — View achievements
/leaderboard — Global leaderboard

*Group Commands*
In a group, mention me: @YourBotName \\<message\\>

💡 *Tip:* Just type naturally — I understand conversation!
"""
