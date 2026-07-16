"""
Nexus — Background Reminder Scheduler
Polls the database every 30 seconds and fires due reminders.
"""
from __future__ import annotations

import asyncio
import logging

from telegram.ext import Application

from app.database import get_session
from app.reminders import get_due_reminders, reschedule_or_mark_sent

logger = logging.getLogger("nexus.scheduler")


async def reminder_loop(app: Application) -> None:
    """Runs as a background task — checks for due reminders every 30 seconds."""
    logger.info("Reminder scheduler started ✓")
    while True:
        try:
            async with get_session() as session:
                due = await get_due_reminders(session)
                for reminder in due:
                    try:
                        await app.bot.send_message(
                            chat_id=reminder.chat_id,
                            text=(
                                f"⏰ *Reminder!*\n\n{reminder.text}\n\n"
                                f"_Set with Nexus AI_ 🤖"
                            ),
                            parse_mode="Markdown",
                        )
                        await reschedule_or_mark_sent(session, reminder)
                        logger.info("Fired reminder #%s for user %s", reminder.id, reminder.user_id)
                    except Exception as exc:
                        logger.error("Failed to send reminder #%s: %s", reminder.id, exc)
        except Exception as exc:
            logger.error("Reminder loop error: %s", exc)

        await asyncio.sleep(30)
