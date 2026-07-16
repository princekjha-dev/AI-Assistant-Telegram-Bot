"""
Nexus — AI Chat Engine
Orchestrates conversation context, memory, and personality.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.client import openrouter
from app.ai.personalities import get_personality
from app.config import settings
from app.database.models import Conversation, Message, Memory, User, MessageRole

logger = logging.getLogger("nexus.ai.engine")

SUMMARY_THRESHOLD = 30  # messages before we summarise older ones


async def _get_or_create_active_conversation(
    session: AsyncSession, user: User
) -> Conversation:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id, Conversation.is_active == True)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        conv = Conversation(user_id=user.id, title="New Chat")
        session.add(conv)
        await session.flush()
    return conv


async def _build_context_messages(
    session: AsyncSession,
    conversation: Conversation,
    user: User,
    personality_key: str,
) -> list[dict]:
    """Build the message list to send to the LLM."""
    personality = get_personality(personality_key)

    # System prompt
    system_parts = [personality.system_prompt]

    # Inject long-term memories
    result = await session.execute(
        select(Memory)
        .where(Memory.user_id == user.id)
        .order_by(Memory.importance.desc())
        .limit(15)
    )
    memories = result.scalars().all()
    if memories:
        facts = "\n".join(f"- {m.fact}" for m in memories)
        system_parts.append(f"\n\n## What I know about this user:\n{facts}")

    # Conversation summary (if exists)
    if conversation.summary:
        system_parts.append(f"\n\n## Earlier conversation summary:\n{conversation.summary}")

    messages = [{"role": "system", "content": "\n".join(system_parts)}]

    # Recent messages
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(settings.CONTEXT_WINDOW)
    )
    recent = list(reversed(result.scalars().all()))
    for msg in recent:
        messages.append({"role": msg.role, "content": msg.content})

    return messages


async def _maybe_summarise(session: AsyncSession, conversation: Conversation) -> None:
    """If conversation is long, summarise the older half to save tokens."""
    result = await session.execute(
        select(Message).where(Message.conversation_id == conversation.id)
    )
    msgs = result.scalars().all()
    if len(msgs) < SUMMARY_THRESHOLD:
        return

    # Summarise oldest half
    half = len(msgs) // 2
    to_summarise = msgs[:half]
    text = "\n".join(f"{m.role}: {m.content}" for m in to_summarise)

    summary_prompt = [
        {"role": "system", "content": "You are a summarisation assistant. Summarise the following conversation concisely, preserving key information and context."},
        {"role": "user", "content": text},
    ]
    try:
        summary, _ = await openrouter.chat_text(summary_prompt, max_tokens=512)
        conversation.summary = summary
        # Delete summarised messages
        for m in to_summarise:
            await session.delete(m)
        logger.info("Summarised conversation %s (%d messages)", conversation.id, half)
    except Exception as exc:
        logger.warning("Summarisation failed: %s", exc)


async def chat(
    session: AsyncSession,
    user: User,
    user_message: str,
    model_override: Optional[str] = None,
    context_text: Optional[str] = None,  # extra context (e.g. file content)
) -> tuple[str, int]:
    """
    Main chat function.
    Returns (assistant_reply, tokens_used).
    """
    conversation = await _get_or_create_active_conversation(session, user)

    # Persist user message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=user_message,
    )
    session.add(user_msg)

    # Build context
    context_messages = await _build_context_messages(
        session, conversation, user, user.personality
    )

    # Inject ephemeral context (file contents, etc.)
    if context_text:
        context_messages.append({
            "role": "system",
            "content": f"[Context provided by user]\n{context_text}",
        })

    # Add the live user message
    context_messages.append({"role": "user", "content": user_message})

    # Call LLM
    model = model_override or user.preferred_model or settings.OPENROUTER_MODEL
    reply, tokens = await openrouter.chat_text(context_messages, model=model)

    # Persist assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=reply,
        tokens_used=tokens,
        model_used=model,
    )
    session.add(assistant_msg)

    # Auto-title conversation after first exchange
    if not conversation.title or conversation.title == "New Chat":
        title_words = user_message[:50].strip()
        conversation.title = title_words if title_words else "Conversation"

    conversation.updated_at = datetime.now(timezone.utc)

    # Maybe summarise
    await _maybe_summarise(session, conversation)

    return reply, tokens


async def auto_extract_memory(
    session: AsyncSession,
    user: User,
    message: str,
    reply: str,
) -> None:
    """
    Ask the LLM to extract memorable facts from the exchange and save them.
    Runs in background — failures are swallowed.
    """
    try:
        extraction_prompt = [
            {
                "role": "system",
                "content": (
                    "Extract any personal facts about the user from this conversation exchange. "
                    "Return ONLY a JSON array of short fact strings, or an empty array [] if none. "
                    "Example: [\"User's name is Alex\", \"User loves hiking\"]"
                ),
            },
            {"role": "user", "content": f"User: {message}\nAssistant: {reply}"},
        ]
        raw, _ = await openrouter.chat_text(extraction_prompt, max_tokens=256, temperature=0.1)

        import json
        raw = raw.strip()
        # Extract JSON array
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            facts: list[str] = json.loads(raw[start:end])
            for fact in facts[:5]:  # cap at 5 per exchange
                if fact and len(fact) > 5:
                    mem = Memory(user_id=user.id, fact=fact, category="auto")
                    session.add(mem)
    except Exception as exc:
        logger.debug("Auto-memory extraction skipped: %s", exc)
