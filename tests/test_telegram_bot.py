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
    monkeypatch.setenv("SAKTHAI_STATELESS", "1")
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
    assert calls[-1]["stateless"] is True


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


def test_sakthai_stateless_parses_truthy_and_falsy_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sakthai import config

    monkeypatch.delenv("SAKTHAI_STATELESS", raising=False)
    assert config.sakthai_stateless() is False  # unset -> False
    for truthy in ("1", "true", "YES", " On "):
        monkeypatch.setenv("SAKTHAI_STATELESS", truthy)
        assert config.sakthai_stateless() is True
    for falsy in ("0", "false", "no", ""):
        monkeypatch.setenv("SAKTHAI_STATELESS", falsy)
        assert config.sakthai_stateless() is False


def test_unauthorized_user_is_rejected_before_run_agent(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")

    def _explode(*_a: object, **_k: object) -> object:
        raise AssertionError("run_agent must not be called for an unauthorized user")

    monkeypatch.setattr(bot, "run_agent", _explode)
    update = _Update(999)  # not in the allow list
    context = _Context()

    import asyncio

    asyncio.run(bot.handle_text(update, context))

    assert update.message.replies == ["Sorry, you are not authorized to use this bot."]


def test_start_greets_authorized_and_rejects_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")

    import asyncio

    allowed = _Update(123)
    asyncio.run(bot.start(allowed, _Context()))
    assert "Welcome" in allowed.message.replies[-1]

    denied = _Update(999)
    asyncio.run(bot.start(denied, _Context()))
    assert denied.message.replies == ["Sorry, you are not authorized to use this bot."]


def test_handle_text_ignores_empty_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")

    def _explode(*_a: object, **_k: object) -> object:
        raise AssertionError("empty text must short-circuit before run_agent")

    monkeypatch.setattr(bot, "run_agent", _explode)
    update = _Update(123, text="")

    import asyncio

    asyncio.run(bot.handle_text(update, _Context()))

    assert update.message.replies == []


def test_workflow_requires_a_name_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    update = _Update(123)

    import asyncio

    asyncio.run(bot.workflow(update, _Context(args=[])))

    assert "Usage: /workflow" in update.message.replies[-1]


def test_workflow_rejects_unknown_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: ["alpha"])

    def _explode(*_a: object, **_k: object) -> object:
        raise AssertionError("unknown workflow must not reach run_agent")

    monkeypatch.setattr(bot, "run_agent", _explode)
    update = _Update(123)

    import asyncio

    asyncio.run(bot.workflow(update, _Context(args=["missing"])))

    reply = update.message.replies[-1]
    assert "Workflow not found" in reply
    assert "alpha" in reply


def test_workflow_rejects_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    update = _Update(999)

    import asyncio

    asyncio.run(bot.workflow(update, _Context(args=["alpha"])))

    assert update.message.replies == ["Sorry, you are not authorized to use this bot."]


def test_reply_reports_missing_chat_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")

    def _explode(*_a: object, **_k: object) -> object:
        raise AssertionError("run_agent must not run without a chat session")

    monkeypatch.setattr(bot, "run_agent", _explode)
    update = _Update(123)
    update.effective_chat = None  # cannot resolve a session key

    import asyncio

    asyncio.run(bot.handle_text(update, _Context()))

    assert update.message.replies == ["Sorry, I could not determine the chat session."]


def test_workflows_command_lists_and_reports_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")

    import asyncio

    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: ["alpha", "beta"])
    listed = _Update(123)
    asyncio.run(bot.workflows(listed, _Context()))
    assert "alpha" in listed.message.replies[-1]
    assert "beta" in listed.message.replies[-1]

    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: [])
    empty = _Update(123)
    asyncio.run(bot.workflows(empty, _Context()))
    assert empty.message.replies[-1] == "No workflows found."


def test_workflows_command_rejects_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    update = _Update(999)

    import asyncio

    asyncio.run(bot.workflows(update, _Context()))

    assert update.message.replies == ["Sorry, you are not authorized to use this bot."]


def test_help_command_lists_available_commands() -> None:
    update = _Update(123)

    import asyncio

    asyncio.run(bot.help_command(update, _Context()))

    reply = update.message.replies[-1]
    assert "/start" in reply
    assert "/workflows" in reply
    assert "/help" in reply


def test_main_raises_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        bot.main()


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
