"""
Tests for rate limiting middleware.
"""
import pytest
from unittest.mock import patch
from app.bot.middleware.rate_limit import is_rate_limited, _windows, _daily


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    """Reset rate limit state before each test."""
    _windows.clear()
    _daily.clear()
    yield
    _windows.clear()
    _daily.clear()


def test_not_limited_initially():
    limited, reason = is_rate_limited(user_id=99999)
    assert not limited
    assert reason == ""


def test_rate_limit_disabled():
    with patch("app.bot.middleware.rate_limit.settings") as mock_settings:
        mock_settings.RATE_LIMIT_ENABLED = False
        mock_settings.MAX_REQUESTS_PER_MINUTE = 20
        mock_settings.MAX_REQUESTS_PER_DAY = 500
        limited, reason = is_rate_limited(user_id=1)
        assert not limited


def test_per_minute_limit():
    with patch("app.bot.middleware.rate_limit.settings") as mock_settings:
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_settings.MAX_REQUESTS_PER_MINUTE = 3
        mock_settings.MAX_REQUESTS_PER_DAY = 500

        # Import fresh to use our mock
        from app.bot.middleware import rate_limit
        rate_limit.settings = mock_settings

        # Manually populate the window
        import time
        now_ts = time.time()
        rate_limit._windows[999] = __import__("collections").deque(
            [now_ts, now_ts, now_ts], maxlen=3
        )
        limited, reason = rate_limit.is_rate_limited(user_id=999)
        assert limited
        assert "fast" in reason.lower() or "easy" in reason.lower()
