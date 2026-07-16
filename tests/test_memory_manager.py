from datetime import datetime

from ai.memory_manager import MemoryManager
from database.models import ChatMessage


def test_prepare_context_messages_includes_summary_for_old_history():
    history = []
    for index in range(25):
        history.append(
            ChatMessage(
                id=index,
                user_id=1,
                role="user" if index % 2 == 0 else "assistant",
                message=f"message {index}",
                timestamp=datetime.now(),
            )
        )

    messages = MemoryManager.prepare_context_messages(history, include_summary=True)

    assert any(msg["role"] == "system" and "Previous conversation history" in msg["content"] for msg in messages)
    assert any(msg["role"] == "user" and msg["content"] == "message 24" for msg in messages)
