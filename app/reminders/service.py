"""
Nexus — Reminder Service
Natural-language reminder parsing and scheduling.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import openrouter
from app.database.models import Reminder, ReminderRecurrence, User

logger = logging.getLogger("nexus.reminders")


async def parse_reminder_with_ai(text: str, user_now: datetime) -> Optional[dict]:
    """
    Use the LLM to parse a natural language reminder.
    Returns {"text": str, "due_at": ISO datetime str, "recurrence": str} or None.
    """
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a reminder parser. Given a user's reminder request, extract:\n"
                "- 'text': what to remind them about\n"
                "- 'due_at': ISO 8601 datetime (UTC) for the reminder\n"
                "- 'recurrence': one of 'none', 'daily', 'weekly', 'monthly'\n"
                f"Current UTC time is: {user_now.isoformat()}\n"
                "Return ONLY valid JSON, nothing else. Example:\n"
                '{"text": "Call John", "due_at": "2024-01-15T09:00:00Z", "recurrence": "none"}'
            ),
        },
        {"role": "user", "content": text},
    ]
    try:
        raw, _ = await openrouter.chat_text(prompt, max_tokens=200, temperature=0.1)
        import json
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as exc:
        logger.warning("Reminder parse failed: %s", exc)
    return None


async def create_reminder(
    session: AsyncSession,
    user: User,
    chat_id: int,
    text: str,
    due_at: datetime,
    recurrence: str = ReminderRecurrence.NONE,
) -> Reminder:
    reminder = Reminder(
        user_id=user.id,
        chat_id=chat_id,
        text=text,
        due_at=due_at,
        recurrence=recurrence,
    )
    session.add(reminder)
    await session.flush()
    logger.info("Reminder created: id=%s user=%s due=%s", reminder.id, user.telegram_id, due_at)
    return reminder


async def get_user_reminders(session: AsyncSession, user_id: int) -> list[Reminder]:
    result = await session.execute(
        select(Reminder)
        .where(Reminder.user_id == user_id, Reminder.is_sent == False)
        .order_by(Reminder.due_at)
    )
    return result.scalars().all()


async def delete_reminder(session: AsyncSession, reminder_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
    )
    reminder = result.scalar_one_or_none()
    if reminder:
        await session.delete(reminder)
        return True
    return False


async def get_due_reminders(session: AsyncSession) -> list[Reminder]:
    """Fetch all reminders that are due right now."""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Reminder).where(Reminder.due_at <= now, Reminder.is_sent == False)
    )
    return result.scalars().all()


async def reschedule_or_mark_sent(session: AsyncSession, reminder: Reminder) -> None:
    """Mark reminder sent; reschedule if recurring."""
    if reminder.recurrence == ReminderRecurrence.DAILY:
        reminder.due_at = reminder.due_at + timedelta(days=1)
    elif reminder.recurrence == ReminderRecurrence.WEEKLY:
        reminder.due_at = reminder.due_at + timedelta(weeks=1)
    elif reminder.recurrence == ReminderRecurrence.MONTHLY:
        # Approximate month
        reminder.due_at = reminder.due_at + timedelta(days=30)
    else:
        reminder.is_sent = True
