"""Tests for the chat input suggester (slash + history)."""

from __future__ import annotations

import pytest

from sakthai.agent.tui import ChatSuggester


@pytest.mark.asyncio
async def test_suggests_slash_command_by_prefix() -> None:
    s = ChatSuggester([])
    assert await s.get_suggestion("/he") == "/help"


@pytest.mark.asyncio
async def test_suggests_recent_history_by_prefix() -> None:
    s = ChatSuggester(["remember the milk", "read the file"])
    assert await s.get_suggestion("rem") == "remember the milk"


@pytest.mark.asyncio
async def test_no_suggestion_when_nothing_matches() -> None:
    s = ChatSuggester([])
    assert await s.get_suggestion("zzz") is None
