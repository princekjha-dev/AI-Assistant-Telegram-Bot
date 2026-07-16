"""
Nexus — Gamification Service
Handles XP, points, streaks, and achievements.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Achievement, User, UserAchievement, UserStats

logger = logging.getLogger("nexus.gamification")


# ── XP / Points rewards ──────────────────────────────────────────────────

REWARDS = {
    "message": {"xp": 5, "points": 2},
    "image": {"xp": 15, "points": 10},
    "file": {"xp": 10, "points": 5},
    "voice": {"xp": 10, "points": 5},
    "command": {"xp": 2, "points": 1},
    "streak": {"xp": 20, "points": 15},
    "first_message": {"xp": 50, "points": 25},
}

# ── Achievement definitions ──────────────────────────────────────────────

ACHIEVEMENT_DEFINITIONS = [
    {"key": "first_chat", "name": "First Chat", "description": "Sent your first message to Nexus", "icon": "🎉", "points_reward": 25},
    {"key": "chat_10", "name": "Getting Chatty", "description": "Sent 10 messages", "icon": "💬", "points_reward": 30},
    {"key": "chat_100", "name": "Chatterbox", "description": "Sent 100 messages", "icon": "🗣️", "points_reward": 100},
    {"key": "chat_1000", "name": "Conversationalist", "description": "Sent 1000 messages", "icon": "🏆", "points_reward": 500},
    {"key": "streak_3", "name": "On a Roll", "description": "3-day chat streak", "icon": "🔥", "points_reward": 30},
    {"key": "streak_7", "name": "7 Day Streak", "description": "7-day chat streak", "icon": "⚡", "points_reward": 75},
    {"key": "streak_30", "name": "Habit Formed", "description": "30-day chat streak", "icon": "🌟", "points_reward": 300},
    {"key": "image_first", "name": "Image Creator", "description": "Generated your first image", "icon": "🎨", "points_reward": 30},
    {"key": "image_10", "name": "Visual Artist", "description": "Generated 10 images", "icon": "🖼️", "points_reward": 75},
    {"key": "file_first", "name": "File Wizard", "description": "Processed your first file", "icon": "📁", "points_reward": 25},
    {"key": "memory_first", "name": "Memory Master", "description": "Added your first memory fact", "icon": "🧠", "points_reward": 25},
    {"key": "voice_first", "name": "Voice User", "description": "Sent your first voice message", "icon": "🎤", "points_reward": 25},
    {"key": "ai_explorer", "name": "AI Explorer", "description": "Tried 3 different personalities", "icon": "🚀", "points_reward": 50},
    {"key": "power_user", "name": "Power User", "description": "Used 10 different commands", "icon": "💪", "points_reward": 100},
    {"key": "level_10", "name": "Level 10", "description": "Reached level 10", "icon": "🎮", "points_reward": 100},
    {"key": "level_50", "name": "Level 50", "description": "Reached level 50", "icon": "💎", "points_reward": 500},
]


async def ensure_achievements_seeded(session: AsyncSession) -> None:
    """Insert achievement definitions that don't yet exist."""
    for defn in ACHIEVEMENT_DEFINITIONS:
        result = await session.execute(
            select(Achievement).where(Achievement.key == defn["key"])
        )
        if result.scalar_one_or_none() is None:
            session.add(Achievement(**defn))
    await session.flush()


async def _get_stats(session: AsyncSession, user_id: int) -> Optional[UserStats]:
    result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
    return result.scalar_one_or_none()


async def award_xp(
    session: AsyncSession,
    user: User,
    action: str,
) -> list[str]:
    """
    Award XP/points for an action.
    Returns a list of newly earned achievement names.
    """
    stats = await _get_stats(session, user.id)
    if not stats:
        return []

    reward = REWARDS.get(action, {"xp": 1, "points": 1})
    stats.xp += reward["xp"]
    stats.points += reward["points"]

    # Update action counters
    if action == "message":
        stats.total_messages += 1
        stats.weekly_messages += 1
        stats.monthly_messages += 1
    elif action == "image":
        stats.total_images += 1
    elif action == "file":
        stats.total_files += 1
    elif action == "voice":
        stats.total_voice += 1
    elif action == "command":
        stats.commands_used += 1

    # Update streak
    now = datetime.now(timezone.utc)
    if stats.last_activity_date:
        diff = (now.date() - stats.last_activity_date.date()).days
        if diff == 1:
            stats.streak_days += 1
            if stats.streak_days > stats.longest_streak:
                stats.longest_streak = stats.streak_days
            if stats.streak_days in (3, 7, 30):
                stats.xp += REWARDS["streak"]["xp"]
                stats.points += REWARDS["streak"]["points"]
        elif diff > 1:
            stats.streak_days = 1
    else:
        stats.streak_days = 1

    stats.last_activity_date = now

    # Check achievements
    earned = await _check_achievements(session, user, stats)
    return earned


async def _check_achievements(
    session: AsyncSession, user: User, stats: UserStats
) -> list[str]:
    """Check and award any newly earned achievements. Returns earned names."""
    earned_names = []

    # Get already-earned achievement keys
    result = await session.execute(
        select(Achievement.key)
        .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user.id)
    )
    already_earned = set(result.scalars().all())

    # Define check conditions
    conditions = {
        "first_chat": stats.total_messages >= 1,
        "chat_10": stats.total_messages >= 10,
        "chat_100": stats.total_messages >= 100,
        "chat_1000": stats.total_messages >= 1000,
        "streak_3": stats.streak_days >= 3,
        "streak_7": stats.streak_days >= 7,
        "streak_30": stats.streak_days >= 30,
        "image_first": stats.total_images >= 1,
        "image_10": stats.total_images >= 10,
        "file_first": stats.total_files >= 1,
        "voice_first": stats.total_voice >= 1,
        "level_10": stats.level >= 10,
        "level_50": stats.level >= 50,
    }

    for key, condition in conditions.items():
        if condition and key not in already_earned:
            # Fetch achievement
            result = await session.execute(select(Achievement).where(Achievement.key == key))
            achievement = result.scalar_one_or_none()
            if achievement:
                ua = UserAchievement(user_id=user.id, achievement_id=achievement.id)
                session.add(ua)
                stats.points += achievement.points_reward
                earned_names.append(f"{achievement.icon} {achievement.name}")
                logger.info("Achievement earned: %s by user %s", achievement.name, user.telegram_id)

    return earned_names
