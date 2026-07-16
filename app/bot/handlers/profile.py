"""
Nexus — Profile, Stats, Achievements, Leaderboard handlers
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.helpers import format_number, progress_bar
from app.database import get_session
from app.database.models import Achievement, User, UserAchievement, UserStats
from app.database.repositories import get_or_create_user, get_top_users

logger = logging.getLogger("nexus.handler.profile")


async def profile_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/profile — Show user profile."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        stats = user.stats

    if not stats:
        await update.message.reply_text("Profile not found. Try /start first!")
        return

    xp_bar = progress_bar(stats.xp % 100, 100, 10)
    streak_emoji = "🔥" if stats.streak_days >= 7 else ("⚡" if stats.streak_days >= 3 else "📅")

    text = (
        f"👤 *{user.display_name}'s Profile*\n\n"
        f"🏅 Level *{stats.level}*\n"
        f"✨ XP: {stats.xp} `{xp_bar}` +{stats.xp_to_next_level} to next level\n"
        f"⭐ Points: *{format_number(stats.points)}*\n\n"
        f"{streak_emoji} Streak: *{stats.streak_days} days* (best: {stats.longest_streak})\n\n"
        f"📊 *Activity*\n"
        f"• 💬 {format_number(stats.total_messages)} messages\n"
        f"• 🎨 {format_number(stats.total_images)} images generated\n"
        f"• 📄 {format_number(stats.total_files)} files processed\n"
        f"• 🎤 {format_number(stats.total_voice)} voice messages\n"
        f"• ⌨️ {format_number(stats.commands_used)} commands used\n\n"
        f"🤖 Personality: *{user.personality.title()}*\n"
        f"🌐 Model: `{user.preferred_model or 'default'}`"
    )

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def stats_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats — Detailed statistics."""
    await profile_handler(update, ctx)


async def achievements_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/achievements — List achievements."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)

        # Get earned achievements
        result = await session.execute(
            select(Achievement)
            .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
            .where(UserAchievement.user_id == user.id)
        )
        earned = result.scalars().all()
        earned_keys = {a.key for a in earned}

        # Get all achievements
        result = await session.execute(select(Achievement))
        all_achievements = result.scalars().all()

    earned_lines = ["🏆 *Your Achievements*\n"]
    locked_lines = ["\n🔒 *Locked*\n"]

    for ach in all_achievements:
        if ach.key in earned_keys:
            earned_lines.append(f"✅ {ach.icon} *{ach.name}* — {ach.description}")
        else:
            locked_lines.append(f"🔒 {ach.icon} {ach.name} — {ach.description}")

    total = len(all_achievements)
    completed = len(earned)
    progress = progress_bar(completed, total, 10)

    header = f"Progress: {completed}/{total} `{progress}`\n\n"
    full_text = header + "\n".join(earned_lines) + "\n".join(locked_lines)

    await update.message.reply_text(full_text, parse_mode=ParseMode.MARKDOWN)


async def leaderboard_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/leaderboard — Global top users."""
    async with get_session() as session:
        top = await get_top_users(session, limit=10)

    if not top:
        await update.message.reply_text("🏆 No leaderboard data yet. Start chatting!")
        return

    medals = ["🥇", "🥈", "🥉"] + ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    lines = ["🏆 *Global Leaderboard*\n"]

    for i, (user, stats) in enumerate(top):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user.display_name[:20]
        lines.append(
            f"{medal} *{name}* — {format_number(stats.points)} pts"
            f" | Lv.{stats.level} | 🔥{stats.streak_days}d"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
