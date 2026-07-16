"""
Nexus — Rate Limiting Middleware
Per-user sliding-window rate limiting.
"""
from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Callable

from telegram import Update
from telegram.ext import BaseHandler, CallbackContext

from app.config import settings

logger = logging.getLogger("nexus.ratelimit")

# In-memory rate limiter (per-process; survives restarts poorly but is simple)
_windows: dict[int, deque[float]] = defaultdict(lambda: deque(maxlen=settings.MAX_REQUESTS_PER_MINUTE))
_daily: dict[int, tuple[int, str]] = {}  # user_id -> (count, date_str)


def is_rate_limited(user_id: int) -> tuple[bool, str]:
    """
    Returns (limited, reason).
    """
    if not settings.RATE_LIMIT_ENABLED:
        return False, ""

    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()
    today = now.date().isoformat()

    # Per-minute window
    window = _windows[user_id]
    # Purge entries older than 60 seconds
    while window and now_ts - window[0] > 60:
        window.popleft()

    if len(window) >= settings.MAX_REQUESTS_PER_MINUTE:
        return True, f"⚡ Easy there! You're sending messages too fast. Please wait a moment."

    # Daily limit
    count, date = _daily.get(user_id, (0, today))
    if date != today:
        count, date = 0, today
    if count >= settings.MAX_REQUESTS_PER_DAY:
        return True, f"📊 You've reached your daily limit of {settings.MAX_REQUESTS_PER_DAY} messages. See you tomorrow! 🌅"

    # Record request
    window.append(now_ts)
    _daily[user_id] = (count + 1, date)
    return False, ""
