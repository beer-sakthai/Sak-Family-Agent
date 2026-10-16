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


def test_session_is_kept_per_chat_but_memory_is_the_personas(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each chat keeps its own settings; every chat writes to the persona's one shard."""
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123,456")
    monkeypatch.setenv("SAKTHAI_PERSONA", "saktan")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    context = _Context()
    first = bot._get_chat_session(context, 123)
    second = bot._get_chat_session(context, 123)
    other_chat = bot._get_chat_session(context, 456)

    assert first is second
    assert other_chat is not first
    shard = Path.home() / ".sakthai" / "saktan" / "memory.db"
    assert first.db_path == other_chat.db_path == shard


def test_session_memory_without_a_persona_is_the_default_store(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.delenv("SAKTHAI_PERSONA", raising=False)
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)

    assert bot._get_chat_session(_Context(), 123).db_path == sakthai_home / "memory.db"


def test_deployed_skills_resolve_from_the_personas_own_skills(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The VM's SAKTHAI_WITH_SKILLS name reaches SakSee's prompt.

    The bot called run_agent without the persona, so skills resolved against
    SakThai's skill folder and SakSee-playwright, which only SakSee has, was
    silently skipped.
    """
    from sakthai.agent.loop import _build_skills_block

    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setenv("SAKTHAI_PERSONA", "saksee")
    monkeypatch.setenv("SAKTHAI_WITH_SKILLS", "SakSee-playwright")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    calls: list[dict[str, object]] = []

    def fake_run_agent(task: str, **kwargs: object) -> object:
        calls.append(kwargs)
        return type("Result", (), {"text": "done"})()

    monkeypatch.setattr(bot, "run_agent", fake_run_agent)
    asyncio.run(bot.handle_text(_Update(123, text="check the site"), _Context()))

    (kwargs,) = calls
    skills, persona = kwargs["skills"], kwargs.get("persona")
    assert isinstance(skills, list) and (persona is None or isinstance(persona, str))
    assert "### SakSee-playwright" in _build_skills_block(skills, "", None, persona)


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


_REFUSAL = "Sorry, you are not authorized to use this bot."
_GATED_HANDLERS = (
    "start",
    "set_model",
    "set_persona",
    "list_models",
    "session_status",
    "workflow",
    "workflows",
    "handle_text",
)


@pytest.mark.parametrize("handler", _GATED_HANDLERS)
@pytest.mark.parametrize("allowlist", ["123", ""], ids=["unlisted-user", "empty-allowlist"])
def test_unauthorized_user_gets_only_the_refusal(
    monkeypatch: pytest.MonkeyPatch, handler: str, allowlist: str
) -> None:
    """A user missing from the allowlist gets the refusal and the agent never runs.

    The six bots are public on Telegram, so this gate is all that stands between
    a stranger and the agent. An empty allowlist must refuse everyone, not admit
    everyone.
    """
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", allowlist)
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    ran: list[str] = []

    def fake_run_agent(task: str, **_: object) -> object:
        ran.append(task)
        return type("Result", (), {"text": "agent ran"})()

    monkeypatch.setattr(bot, "run_agent", fake_run_agent)
    update = _Update(999, text="read my memory")
    context = _Context(args=["sakking"])

    asyncio.run(getattr(bot, handler)(update, context))

    assert update.message.replies == [_REFUSAL]
    assert ran == []
