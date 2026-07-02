"""Tests for the Telegram bot refactor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from sakthai.telegram import bot


@dataclass
class _User:
    id: int


class _Message:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


class _Update:
    def __init__(self, user_id: int, text: str = "hello") -> None:
        self.effective_user = _User(user_id)
        self.effective_chat = type("Chat", (), {"id": user_id})()
        self.message = _Message(text)


class _Context:
    def __init__(self, args: list[str] | None = None) -> None:
        self.args = args or []
        self.application = type("App", (), {"bot_data": {}})()


def test_session_store_is_persistent_per_chat(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    context = _Context()
    first = bot._get_chat_session(context, 123)
    second = bot._get_chat_session(context, 123)

    assert first is second
    assert first.db_path == sakthai_home / "telegram" / "123" / "memory.db"


def test_text_message_routes_through_run_agent(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "run_agent", lambda *a, **k: type("R", (), {"text": "ok"})())
    update = _Update(123)
    context = _Context()

    import asyncio

    asyncio.run(bot.handle_text(update, context))

    assert update.message.replies[-1] == "ok"


def test_workflow_command_routes_through_run_agent(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "run_agent", lambda *a, **k: type("R", (), {"text": "workflow"})())
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: ["alpha"])
    update = _Update(123)
    context = _Context(["alpha"])

    import asyncio

    asyncio.run(bot.workflow(update, context))

    assert any("workflow" in reply for reply in update.message.replies)
