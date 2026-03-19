from datetime import datetime, timedelta
from database.models import User
import config


class StreakManager:
    @staticmethod
    def update_streak(user: User) -> tuple[bool, int]:
        """
        Update user's streak based on last activity.
        Returns: (streak_continued, new_streak_count)
        """
        now = datetime.now()

        if user.last_active is None:
            # First interaction
            user.streak_count = 1
            user.last_active = now
            return True, 1

        hours_since_last = (now - user.last_active).total_seconds() / 3600

        if hours_since_last <= 24:
            # Same day or within 24 hours - maintain streak
            user.last_active = now
            return True, user.streak_count
        elif hours_since_last <= config.STREAK_RESET_HOURS:
            # Within grace period - increment streak
            user.streak_count += 1
            user.last_active = now
            return True, user.streak_count
        else:
            # Streak broken - reset
            old_streak = user.streak_count
            user.streak_count = 1
            user.last_active = now
            return False, old_streak

    @staticmethod
    def get_streak_message(streak_count: int, streak_broken: bool = False) -> str:
        """Generate streak status message"""
        if streak_broken:
            return f"🔥 Streak reset! You had a {streak_count} day streak. Let's start fresh!"

        if streak_count == 1:
            return "🔥 Day 1 streak! Come back tomorrow to keep it going!"
        elif streak_count < 7:
            return f"🔥 {streak_count} day streak! Keep it up!"
        elif streak_count < 30:
            return f"🔥🔥 {streak_count} day streak! You're on fire!"
        else:
            return f"🔥🔥🔥 {streak_count} day streak! Absolutely incredible!"

    @staticmethod
    def should_show_streak_reminder(user: User) -> bool:
        """Check if we should remind user about streak"""
        if user.last_active is None:
            return False

        hours_since_last = (datetime.now() - user.last_active).total_seconds() / 3600

        # Remind if approaching streak reset threshold
        return 36 <= hours_since_last <= config.STREAK_RESET_HOURS