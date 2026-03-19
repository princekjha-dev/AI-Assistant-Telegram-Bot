from typing import List
from database.db import Database
from database.models import User, Achievement


class AchievementManager:
    def __init__(self, db: Database):
        self.db = db

    async def check_and_unlock(self, user: User) -> List[Achievement]:
        """
        Check if user has unlocked any new achievements.
        Returns list of newly unlocked achievements.
        """
        all_achievements = await self.db.get_achievements()
        user_achievement_ids = await self.db.get_user_achievements(user.user_id)

        newly_unlocked = []

        for achievement in all_achievements:
            # Skip already unlocked
            if achievement.id in user_achievement_ids:
                continue

            # Check if user qualifies
            if await self._qualifies_for_achievement(user, achievement):
                await self.db.unlock_achievement(user.user_id, achievement.id)
                newly_unlocked.append(achievement)

        return newly_unlocked

    async def _qualifies_for_achievement(self, user: User, achievement: Achievement) -> bool:
        """Check if user meets achievement requirements"""

        if achievement.name == "First Steps":
            return user.interaction_score >= 0

        elif achievement.name == "Chatty":
            return user.interaction_score >= 500

        elif achievement.name == "Conversationalist":
            return user.interaction_score >= 2000

        elif achievement.name == "Streak Master":
            return user.streak_count >= 7

        elif achievement.name == "Mood Explorer":
            # Check if user has experienced different moods
            # This would require tracking mood history
            return False  # Placeholder

        elif achievement.name == "Personality Switch":
            # Check if user has tried different personalities
            # This would require tracking personality changes
            return False  # Placeholder

        return False

    @staticmethod
    def format_achievement_notification(achievement: Achievement) -> str:
        """Format achievement unlock message"""
        return f"""
🏆 **Achievement Unlocked!**

**{achievement.name}**
{achievement.description}

Points Required: {achievement.points_required}
"""

    async def get_user_progress(self, user: User) -> str:
        """Get formatted achievement progress"""
        all_achievements = await self.db.get_achievements()
        user_achievement_ids = await self.db.get_user_achievements(user.user_id)

        progress = f"🏆 **Your Achievements** ({len(user_achievement_ids)}/{len(all_achievements)})\n\n"

        for achievement in all_achievements:
            if achievement.id in user_achievement_ids:
                progress += f"✅ **{achievement.name}**\n"
            else:
                progress += f"🔒 {achievement.name}\n"
            progress += f"   {achievement.description}\n"
            progress += f"   Points: {achievement.points_required}\n\n"

        return progress