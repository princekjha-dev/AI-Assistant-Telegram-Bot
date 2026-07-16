"""
Nexus — Reminder command handlers
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.database import get_session
from app.database.repositories import get_or_create_user
from app.reminders import (
    create_reminder, delete_reminder, get_user_reminders, parse_reminder_with_ai
)

logger = logging.getLogger("nexus.handler.reminder")

RECURRENCE_LABELS = {"none": "Once", "daily": "Daily 🔁", "weekly": "Weekly 🔁", "monthly": "Monthly 🔁"}


async def remind_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/remind <natural language> — Set a reminder."""
    if not ctx.args:
        await update.message.reply_text(
            "⏰ *Reminder Examples:*\n\n"
            '• `/remind Call John tomorrow at 9am`\n'
            '• `/remind Take medication every day at 8am`\n'
            '• `/remind Team meeting every Monday at 10am`\n'
            '• `/remind Buy groceries in 2 hours`',
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    text = " ".join(ctx.args)
    tg_user = update.effective_user
    now = datetime.now(timezone.utc)

    status_msg = await update.message.reply_text("⏰ *Parsing your reminder...*", parse_mode=ParseMode.MARKDOWN)

    try:
        parsed = await parse_reminder_with_ai(text, now)

        if not parsed:
            await status_msg.edit_text(
                "❌ Couldn't parse your reminder. Try being more specific:\n"
                "_Example: 'Remind me tomorrow at 9 AM to call John'_",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        reminder_text = parsed.get("text", text)
        due_str = parsed.get("due_at", "")
        recurrence = parsed.get("recurrence", "none")

        # Parse due date
        try:
            if due_str.endswith("Z"):
                due_str = due_str[:-1] + "+00:00"
            due_at = datetime.fromisoformat(due_str)
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=timezone.utc)
        except Exception:
            await status_msg.edit_text("❌ Couldn't parse the date/time. Please try again with a clearer time.")
            return

        async with get_session() as session:
            user, _ = await get_or_create_user(session, tg_user.id)
            reminder = await create_reminder(
                session, user,
                chat_id=update.effective_chat.id,
                text=reminder_text,
                due_at=due_at,
                recurrence=recurrence,
            )

        recur_label = RECURRENCE_LABELS.get(recurrence, recurrence)
        await status_msg.edit_text(
            f"✅ *Reminder Set!*\n\n"
            f"📝 {reminder_text}\n"
            f"📅 {due_at.strftime('%a, %b %d %Y at %H:%M UTC')}\n"
            f"🔁 {recur_label}\n\n"
            f"_ID: #{reminder.id}_",
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as exc:
        logger.error("Reminder creation error: %s", exc, exc_info=True)
        await status_msg.edit_text("😅 Had trouble setting that reminder. Please try again!")


async def reminders_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/reminders — List all pending reminders."""
    tg_user = update.effective_user
    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        reminders = await get_user_reminders(session, user.id)

    if not reminders:
        await update.message.reply_text(
            "⏰ *No Pending Reminders*\n\nSet one with `/remind <text>`!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    lines = ["⏰ *Your Reminders*\n"]
    for r in reminders:
        recur = f" ({RECURRENCE_LABELS[r.recurrence]})" if r.recurrence != "none" else ""
        due = r.due_at.strftime("%b %d, %H:%M UTC")
        lines.append(f"*#{r.id}* — {r.text}{recur}\n   📅 {due}")

    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )


async def del_reminder_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/delreminder <id> — Delete a reminder."""
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text(
            "Usage: `/delreminder <id>`\n\nGet IDs with /reminders",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    reminder_id = int(ctx.args[0])
    tg_user = update.effective_user

    async with get_session() as session:
        user, _ = await get_or_create_user(session, tg_user.id)
        deleted = await delete_reminder(session, reminder_id, user.id)

    if deleted:
        await update.message.reply_text(f"✅ Reminder #{reminder_id} deleted!")
    else:
        await update.message.reply_text(f"❌ Reminder #{reminder_id} not found.")
