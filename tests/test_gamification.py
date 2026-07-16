"""
Tests for gamification service.
"""
import pytest

from app.gamification.service import REWARDS, ACHIEVEMENT_DEFINITIONS


def test_rewards_defined():
    assert "message" in REWARDS
    assert "image" in REWARDS
    assert REWARDS["message"]["xp"] > 0
    assert REWARDS["image"]["xp"] > REWARDS["message"]["xp"]


def test_achievement_definitions():
    assert len(ACHIEVEMENT_DEFINITIONS) >= 10
    keys = [a["key"] for a in ACHIEVEMENT_DEFINITIONS]
    assert "first_chat" in keys
    assert "streak_7" in keys
    assert "image_first" in keys
    assert "power_user" in keys


def test_achievement_has_required_fields():
    for ach in ACHIEVEMENT_DEFINITIONS:
        assert "key" in ach
        assert "name" in ach
        assert "description" in ach
        assert "icon" in ach
        assert "points_reward" in ach
        assert ach["points_reward"] > 0
