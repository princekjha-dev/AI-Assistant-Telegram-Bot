import sqlite3
import asyncio
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager
import config
from database.models import User, ChatMessage, Achievement, UserAchievement, Gift, RateLimit


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db_sync(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    llm_provider TEXT DEFAULT 'openai',
                    personality_mode TEXT DEFAULT 'friendly',
                    mood_state TEXT DEFAULT 'neutral',
                    interaction_score INTEGER DEFAULT 0,
                    streak_count INTEGER DEFAULT 0,
                    last_active TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    points_required INTEGER
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id INTEGER,
                    achievement_id INTEGER,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, achievement_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (achievement_id) REFERENCES achievements(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS gifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    reward_type TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    request_count INTEGER DEFAULT 0,
                    window_start TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            conn.commit()
            self._seed_achievements_sync(conn)

    def _seed_achievements_sync(self, conn):
        achievements_data = [
            ("First Steps", "Send your first message", 0),
            ("Chatty", "Send 50 messages", 500),
            ("Conversationalist", "Send 200 messages", 2000),
            ("Streak Master", "Maintain a 7-day streak", 700),
            ("Mood Explorer", "Experience all mood states", 300),
            ("Personality Switch", "Try all personality modes", 200),
        ]

        for name, desc, points in achievements_data:
            conn.execute(
                "INSERT OR IGNORE INTO achievements (name, description, points_required) VALUES (?, ?, ?)",
                (name, desc, points)
            )
        conn.commit()

    async def init_db(self):
        await asyncio.to_thread(self._init_db_sync)

    def _get_or_create_user_sync(self, user_id: int, username: str) -> User:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    llm_provider=row['llm_provider'],
                    personality_mode=row['personality_mode'],
                    mood_state=row['mood_state'],
                    interaction_score=row['interaction_score'],
                    streak_count=row['streak_count'],
                    last_active=datetime.fromisoformat(row['last_active']) if row['last_active'] else None
                )
            else:
                conn.execute(
                    """INSERT INTO users (user_id, username, last_active) 
                       VALUES (?, ?, ?)""",
                    (user_id, username, datetime.now().isoformat())
                )
                conn.commit()
                return User(user_id=user_id, username=username, last_active=datetime.now())

    async def get_or_create_user(self, user_id: int, username: str) -> User:
        return await asyncio.to_thread(self._get_or_create_user_sync, user_id, username)

    def _update_user_sync(self, user: User):
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE users SET username=?, llm_provider=?, personality_mode=?, 
                   mood_state=?, interaction_score=?, streak_count=?, last_active=?
                   WHERE user_id=?""",
                (user.username, user.llm_provider, user.personality_mode,
                 user.mood_state, user.interaction_score, user.streak_count,
                 user.last_active.isoformat(), user.user_id)
            )
            conn.commit()

    async def update_user(self, user: User):
        await asyncio.to_thread(self._update_user_sync, user)

    def _save_message_sync(self, user_id: int, role: str, message: str):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
                (user_id, role, message)
            )
            conn.commit()

    async def save_message(self, user_id: int, role: str, message: str):
        await asyncio.to_thread(self._save_message_sync, user_id, role, message)

    def _get_chat_history_sync(self, user_id: int, limit: int = 10) -> List[ChatMessage]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                """SELECT * FROM chat_history WHERE user_id = ? 
                   ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            )
            rows = cursor.fetchall()

            messages = []
            for row in reversed(rows):
                messages.append(ChatMessage(
                    id=row['id'],
                    user_id=row['user_id'],
                    role=row['role'],
                    message=row['message'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ))
            return messages

    async def get_chat_history(self, user_id: int, limit: int = 10) -> List[ChatMessage]:
        return await asyncio.to_thread(self._get_chat_history_sync, user_id, limit)

    def _clear_chat_history_sync(self, user_id: int):
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM chat_history WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()

    async def clear_chat_history(self, user_id: int):
        await asyncio.to_thread(self._clear_chat_history_sync, user_id)

    def _get_achievements_sync(self) -> List[Achievement]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM achievements")
            rows = cursor.fetchall()
            return [Achievement(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                points_required=row['points_required']
            ) for row in rows]

    async def get_achievements(self) -> List[Achievement]:
        return await asyncio.to_thread(self._get_achievements_sync)

    def _get_user_achievements_sync(self, user_id: int) -> List[int]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT achievement_id FROM user_achievements WHERE user_id = ?",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [row['achievement_id'] for row in rows]

    async def get_user_achievements(self, user_id: int) -> List[int]:
        return await asyncio.to_thread(self._get_user_achievements_sync, user_id)

    def _unlock_achievement_sync(self, user_id: int, achievement_id: int):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
                (user_id, achievement_id)
            )
            conn.commit()

    async def unlock_achievement(self, user_id: int, achievement_id: int):
        await asyncio.to_thread(self._unlock_achievement_sync, user_id, achievement_id)

    def _get_rate_limit_sync(self, user_id: int) -> Optional[RateLimit]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM rate_limits WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return RateLimit(
                    user_id=row['user_id'],
                    request_count=row['request_count'],
                    window_start=datetime.fromisoformat(row['window_start'])
                )
            return None

    async def get_rate_limit(self, user_id: int) -> Optional[RateLimit]:
        return await asyncio.to_thread(self._get_rate_limit_sync, user_id)

    def _update_rate_limit_sync(self, rate_limit: RateLimit):
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO rate_limits (user_id, request_count, window_start)
                   VALUES (?, ?, ?)""",
                (rate_limit.user_id, rate_limit.request_count,
                 rate_limit.window_start.isoformat())
            )
            conn.commit()

    async def update_rate_limit(self, rate_limit: RateLimit):
        await asyncio.to_thread(self._update_rate_limit_sync, rate_limit)