from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: int
    username: str
    llm_provider: str = "openai"
    personality_mode: str = "friendly"
    mood_state: str = "neutral"
    interaction_score: int = 0
    streak_count: int = 0
    last_active: datetime = None

@dataclass
class ChatMessage:
    id: Optional[int]
    user_id: int
    role: str
    message: str
    timestamp: datetime

@dataclass
class Achievement:
    id: int
    name: str
    description: str
    points_required: int

@dataclass
class UserAchievement:
    user_id: int
    achievement_id: int
    unlocked_at: datetime

@dataclass
class Gift:
    id: int
    name: str
    reward_type: str

@dataclass
class RateLimit:
    user_id: int
    request_count: int
    window_start: datetime