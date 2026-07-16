"""
Nexus — User Repository
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import User, UserStats
from app.config import settings

logger = logging.getLogger("nexus.repo.user")


async def get_or_create_user(session: AsyncSession, telegram_id: int, **kwargs) -> tuple[User, bool]:
    """Return (user, created). Always updates last_active."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id).options(selectinload(User.stats))
    )
    user = result.scalar_one_or_none()

    created = False
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=kwargs.get("username"),
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
            is_admin=telegram_id in settings.admin_ids,
        )
        session.add(user)
        await session.flush()

        # Create default stats row
        stats = UserStats(user_id=user.id)
        session.add(stats)
        await session.flush()
        created = True
        logger.info("New user registered: %s (tg_id=%s)", user.display_name, telegram_id)
    else:
        # Update metadata if changed
        user.username = kwargs.get("username", user.username)
        user.first_name = kwargs.get("first_name", user.first_name)
        user.last_name = kwargs.get("last_name", user.last_name)

    user.last_active = datetime.now(timezone.utc)
    return user, created


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.stats), selectinload(User.memories))
    )
    return result.scalar_one_or_none()


async def update_user_personality(session: AsyncSession, telegram_id: int, personality: str) -> None:
    user = await get_user(session, telegram_id)
    if user:
        user.personality = personality


async def get_top_users(session: AsyncSession, limit: int = 10) -> list[tuple[User, UserStats]]:
    result = await session.execute(
        select(User, UserStats)
        .join(UserStats, User.id == UserStats.user_id)
        .order_by(UserStats.points.desc())
        .limit(limit)
    )
    return result.all()
