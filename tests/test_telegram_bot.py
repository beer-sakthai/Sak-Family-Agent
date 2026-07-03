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


def test_text_message_routes_through_run_agent(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    monkeypatch.setenv("SAKTHAI_PROVIDER", "openai")
    monkeypatch.setenv("SAKTHAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("SAKTHAI_SYSTEM_PROMPT", "PERSONA")
    monkeypatch.setenv("SAKTHAI_WITH_SKILLS", "skill-a, skill-b")
    calls: list[dict[str, object]] = []

    def _fake_run_agent(*_a: object, **kwargs: object) -> object:
        calls.append(kwargs)
        return type("R", (), {"text": "ok"})()

    monkeypatch.setattr(bot, "run_agent", _fake_run_agent)
    update = _Update(123)
    context = _Context()

    import asyncio

    asyncio.run(bot.handle_text(update, context))

    assert update.message.replies[-1] == "ok"
    assert calls[-1]["provider"] == "openai"
    assert calls[-1]["model"] == "gpt-4o-mini"
    assert calls[-1]["system_prompt_prefix"] == "PERSONA"
    assert calls[-1]["skills"] == ["skill-a", "skill-b"]


def test_workflow_command_routes_through_run_agent(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    monkeypatch.setattr(bot, "run_agent", lambda *a, **k: type("R", (), {"text": "workflow"})())
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: ["alpha"])
    update = _Update(123)
    context = _Context(["alpha"])

    import asyncio

    asyncio.run(bot.workflow(update, context))

    assert any("workflow" in reply for reply in update.message.replies)


def test_main_registers_an_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, bool] = {}

    class _FakeApp:
        def add_handler(self, *_args: object, **_kwargs: object) -> None:
            pass

        def run_polling(self) -> None:
            pass

    class _FakeBuilder:
        def token(self, _token: str) -> _FakeBuilder:
            return self

        def build(self) -> _FakeApp:
            return _FakeApp()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setattr(bot.asyncio, "new_event_loop", lambda: object())
    monkeypatch.setattr(
        bot.asyncio,
        "set_event_loop",
        lambda loop: seen.__setitem__("called", True),
    )
    monkeypatch.setattr(bot, "ApplicationBuilder", lambda: _FakeBuilder())

    bot.main()

    assert seen["called"] is True
