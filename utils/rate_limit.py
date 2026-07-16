from datetime import datetime, timedelta
from database.db import Database
from database.models import RateLimit
import config


class RateLimiter:
    def __init__(self, db: Database):
        self.db = db

    async def check_rate_limit(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit.
        Returns: (is_allowed, remaining_requests)
        """
        rate_limit = await self.db.get_rate_limit(user_id)
        now = datetime.now()

        if rate_limit is None:
            # First request - create new rate limit entry
            new_limit = RateLimit(
                user_id=user_id,
                request_count=1,
                window_start=now
            )
            await self.db.update_rate_limit(new_limit)
            return True, config.RATE_LIMIT_MAX_REQUESTS - 1

        # Check if window has expired
        window_elapsed = (now - rate_limit.window_start).total_seconds()

        if window_elapsed > config.RATE_LIMIT_WINDOW:
            # Reset window
            rate_limit.request_count = 1
            rate_limit.window_start = now
            await self.db.update_rate_limit(rate_limit)
            return True, config.RATE_LIMIT_MAX_REQUESTS - 1

        # Check if limit exceeded
        if rate_limit.request_count >= config.RATE_LIMIT_MAX_REQUESTS:
            remaining_time = config.RATE_LIMIT_WINDOW - window_elapsed
            return False, 0

        # Increment count
        rate_limit.request_count += 1
        await self.db.update_rate_limit(rate_limit)

        remaining = config.RATE_LIMIT_MAX_REQUESTS - rate_limit.request_count
        return True, remaining

    @staticmethod
    def get_rate_limit_message(remaining_time_seconds: float) -> str:
        """Format rate limit exceeded message"""
        minutes = int(remaining_time_seconds / 60)
        seconds = int(remaining_time_seconds % 60)

        if minutes > 0:
            time_str = f"{minutes} minute(s) and {seconds} second(s)"
        else:
            time_str = f"{seconds} second(s)"

        return f"""⏰ Rate limit reached!

You've sent too many messages in a short time. Please wait {time_str} before sending more messages.

Limit: {config.RATE_LIMIT_MAX_REQUESTS} messages per hour"""