"""
Tests for AI personality system.
"""
import pytest
from app.ai.personalities import get_personality, list_personalities, PERSONALITIES


def test_all_personalities_defined():
    assert len(PERSONALITIES) == 5
    for key in ("friendly", "professional", "motivational", "sarcastic", "creative"):
        assert key in PERSONALITIES


def test_get_personality_returns_correct():
    p = get_personality("friendly")
    assert p.key == "friendly"
    assert p.name == "Friendly"
    assert p.icon
    assert p.system_prompt
    assert p.greeting


def test_get_personality_fallback():
    """Unknown key should fallback to friendly."""
    p = get_personality("unknown_key")
    assert p.key == "friendly"


def test_list_personalities():
    all_p = list_personalities()
    assert len(all_p) == 5
    keys = [p.key for p in all_p]
    assert "sarcastic" in keys
    assert "creative" in keys


def test_personality_system_prompts_not_empty():
    for p in list_personalities():
        assert len(p.system_prompt) > 50, f"{p.key} system_prompt too short"
