"""
Tests for media processing service.
"""
import pytest
import asyncio
from app.media.service import extract_text_from_bytes, truncate_text


def test_truncate_text_short():
    text = "Hello world"
    assert truncate_text(text, max_chars=100) == text


def test_truncate_text_long():
    text = "A" * 10000
    result = truncate_text(text, max_chars=500)
    assert len(result) < 10000
    assert "truncated" in result


@pytest.mark.asyncio
async def test_extract_plain_text():
    content = b"Hello, this is plain text content."
    result = await extract_text_from_bytes(content, "text/plain", "test.txt")
    assert result == "Hello, this is plain text content."


@pytest.mark.asyncio
async def test_extract_json_text():
    content = b'{"key": "value", "number": 42}'
    result = await extract_text_from_bytes(content, "application/json", "test.json")
    assert result is not None
    assert "value" in result


@pytest.mark.asyncio
async def test_extract_binary_returns_none():
    # Random binary that can't be decoded as UTF-8
    content = bytes(range(256))
    result = await extract_text_from_bytes(content, "application/octet-stream", "file.bin")
    assert result is None
