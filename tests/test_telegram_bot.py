"""Tests for the Telegram bot refactor."""

from __future__ import annotations

import asyncio
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

    async def reply_text(self, text: str, parse_mode: str | None = None) -> None:
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


class _FakeStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def close(self) -> None:
        pass


def test_session_store_is_persistent_per_chat(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    context = _Context()
    first = bot._get_chat_session(context, 123)
    second = bot._get_chat_session(context, 123)

    assert first is second
    assert first.db_path == sakthai_home / "telegram" / "123" / "memory.db"


def test_set_model_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    update = _Update(123)
    context = _Context(args=["gemini-2.5-pro"])

    asyncio.run(bot.set_model(update, context))

    assert "Model set to 'gemini-2.5-pro'" in update.message.replies[-1]
    session = bot._get_chat_session(context, 123)
    assert session.model == "gemini-2.5-pro"


def test_set_persona_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    update = _Update(123)
    context = _Context(args=["sakking"])

    asyncio.run(bot.set_persona(update, context))

    assert "Persona set to 'Sakking'" in update.message.replies[-1]
    session = bot._get_chat_session(context, 123)
    assert session.persona == "sakking"


def test_session_status_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    update = _Update(123)
    context = _Context()

    session = bot._get_chat_session(context, 123)
    session.model = "qwen2.5-coder"
    session.persona = "saksee"

    asyncio.run(bot.session_status(update, context))

    assert "qwen2.5-coder" in update.message.replies[-1]
    assert "Saksee" in update.message.replies[-1]
