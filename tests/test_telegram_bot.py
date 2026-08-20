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


UNAUTHORIZED_REPLY = "Sorry, you are not authorized to use this bot."

# Every handler that reaches the agent loop or mutates session state. `/help`
# is deliberately excluded — it answers anyone by design.
GATED_HANDLERS = (
    "start",
    "set_model",
    "set_persona",
    "list_models",
    "session_status",
    "workflow",
    "workflows",
    "handle_text",
)


@pytest.fixture
def authorized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow user 123, and keep the session store off the real filesystem."""
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123")
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)


@pytest.fixture
def captured_run_agent(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Record every `run_agent` call instead of invoking a model."""
    calls: list[dict] = []

    def _fake_run_agent(task: str, **kwargs: object) -> object:
        calls.append({"task": task, **kwargs})
        return type("Result", (), {"text": "agent replied"})()

    monkeypatch.setattr(bot, "run_agent", _fake_run_agent)
    return calls


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------
#
# `_reply_with_agent_result` is the choke point: `/workflow` and every
# free-form message reach `run_agent` through it, and it is where the
# allowlist is enforced. These tests assert the *denial* — that an
# unauthorized user is turned away and, critically, that `run_agent` is never
# reached. Asserting only on the reply text would pass even if the agent ran
# first and the refusal were cosmetic.


@pytest.mark.parametrize("handler_name", GATED_HANDLERS)
def test_unauthorized_user_is_refused_by_every_gated_handler(
    handler_name: str,
    authorized: None,
    captured_run_agent: list[dict],
) -> None:
    update = _Update(999, text="do something")
    context = _Context(args=["anything"])

    asyncio.run(getattr(bot, handler_name)(update, context))

    assert update.message.replies == [UNAUTHORIZED_REPLY], (
        f"{handler_name} did not refuse an unauthorized user"
    )
    assert captured_run_agent == [], f"{handler_name} reached run_agent despite refusing the user"


def test_user_with_no_id_is_refused(authorized: None, captured_run_agent: list[dict]) -> None:
    """`update.effective_user` is None for channel posts; `_is_authorized`
    must treat a missing id as unauthorized rather than crashing."""
    update = _Update(123)
    update.effective_user = None

    asyncio.run(bot.handle_text(update, context=_Context()))

    assert update.message.replies == [UNAUTHORIZED_REPLY]
    assert captured_run_agent == []


def test_empty_allowlist_authorizes_nobody(
    monkeypatch: pytest.MonkeyPatch, captured_run_agent: list[dict]
) -> None:
    """An unset allowlist must fail closed, not open."""
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
    monkeypatch.setattr(bot, "MemoryStore", _FakeStore)
    update = _Update(123)

    asyncio.run(bot.handle_text(update, context=_Context()))

    assert update.message.replies == [UNAUTHORIZED_REPLY]
    assert captured_run_agent == []


def test_help_command_is_open_to_everyone(authorized: None) -> None:
    """Characterization: `/help` has no authorization check. It only prints
    static usage text, so this is intentional — pinned so that adding a gate
    (or leaking anything user-specific into it) is a deliberate change."""
    update = _Update(999)

    asyncio.run(bot.help_command(update, context=_Context()))

    assert "/model" in update.message.replies[-1]


# ---------------------------------------------------------------------------
# `_reply_with_agent_result` — the path to the agent loop
# ---------------------------------------------------------------------------


def test_free_form_text_runs_the_agent_and_replies(
    authorized: None, captured_run_agent: list[dict]
) -> None:
    update = _Update(123, text="what is the weather")

    asyncio.run(bot.handle_text(update, context=_Context()))

    assert len(captured_run_agent) == 1
    assert captured_run_agent[0]["task"] == "what is the weather"
    assert update.message.replies == ["agent replied"]


def test_empty_message_does_not_run_the_agent(
    authorized: None, captured_run_agent: list[dict]
) -> None:
    update = _Update(123, text="")

    asyncio.run(bot.handle_text(update, context=_Context()))

    assert captured_run_agent == []
    assert update.message.replies == []


def test_session_model_and_persona_are_passed_through_to_run_agent(
    authorized: None, captured_run_agent: list[dict]
) -> None:
    """The whole point of `/model` and `/persona` is that they change the next
    agent call. Pin that they actually reach `run_agent`."""
    context = _Context()
    session = bot._get_chat_session(context, 123)
    session.model = "ollama/qwen2.5-coder"
    session.persona = "sakking"

    asyncio.run(bot.handle_text(_Update(123, text="hi"), context))

    assert captured_run_agent[0]["model"] == "ollama/qwen2.5-coder"
    assert "Active Persona: Sakking" in captured_run_agent[0]["system_prompt_prefix"]


def test_missing_chat_is_reported_rather_than_crashing(
    authorized: None, captured_run_agent: list[dict]
) -> None:
    update = _Update(123)
    update.effective_chat = None

    asyncio.run(bot.handle_text(update, context=_Context()))

    assert "could not determine the chat session" in update.message.replies[-1]
    assert captured_run_agent == []


# ---------------------------------------------------------------------------
# `/workflow` and `/workflows`
# ---------------------------------------------------------------------------


def test_workflow_without_a_name_asks_for_one(
    authorized: None, captured_run_agent: list[dict]
) -> None:
    update = _Update(123)

    asyncio.run(bot.workflow(update, _Context(args=[])))

    assert "specify a workflow" in update.message.replies[-1]
    assert captured_run_agent == []


def test_unknown_workflow_is_rejected_and_lists_available_ones(
    authorized: None, captured_run_agent: list[dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: ["daily-report"])
    update = _Update(123)

    asyncio.run(bot.workflow(update, _Context(args=["nope"])))

    assert "daily-report" in update.message.replies[-1]
    assert captured_run_agent == []


def test_unknown_workflow_with_none_installed_says_so(
    authorized: None, captured_run_agent: list[dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", list)
    update = _Update(123)

    asyncio.run(bot.workflow(update, _Context(args=["nope"])))

    assert "No workflows are installed" in update.message.replies[-1]
    assert captured_run_agent == []


def test_known_workflow_runs_the_agent_with_that_skill(
    authorized: None, captured_run_agent: list[dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", lambda: ["daily-report"])
    update = _Update(123)

    asyncio.run(bot.workflow(update, _Context(args=["daily-report"])))

    assert len(captured_run_agent) == 1
    assert "daily-report" in captured_run_agent[0]["skills"]
    assert update.message.replies == ["Executing workflow: daily-report", "agent replied"]


def test_workflows_lists_installed_workflows(
    authorized: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        bot.workflow_executor, "get_available_workflows", lambda: ["daily-report", "digest"]
    )
    update = _Update(123)

    asyncio.run(bot.workflows(update, _Context()))

    assert "daily-report" in update.message.replies[-1]
    assert "digest" in update.message.replies[-1]


def test_workflows_with_none_installed(authorized: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot.workflow_executor, "get_available_workflows", list)
    update = _Update(123)

    asyncio.run(bot.workflows(update, _Context()))

    assert "No workflows found" in update.message.replies[-1]


# ---------------------------------------------------------------------------
# Argument handling on the session commands
# ---------------------------------------------------------------------------


def test_set_model_without_args_prompts_for_one(authorized: None) -> None:
    update = _Update(123)

    asyncio.run(bot.set_model(update, _Context(args=[])))

    assert "specify a model name" in update.message.replies[-1]


def test_set_persona_without_args_lists_choices(authorized: None) -> None:
    update = _Update(123)

    asyncio.run(bot.set_persona(update, _Context(args=[])))

    assert "sakthai" in update.message.replies[-1]


def test_set_persona_rejects_an_unknown_persona(authorized: None) -> None:
    update = _Update(123)
    context = _Context(args=["not-a-persona"])

    asyncio.run(bot.set_persona(update, context))

    assert "Unknown persona" in update.message.replies[-1]
    assert bot._get_chat_session(context, 123).persona is None


def test_start_and_list_models_answer_authorized_users(authorized: None) -> None:
    update = _Update(123)
    asyncio.run(bot.start(update, _Context()))
    assert "Welcome" in update.message.replies[-1]

    asyncio.run(bot.list_models(update, _Context()))
    assert "/model <model-name>" in update.message.replies[-1]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("TRUE", True),
        (" yes ", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("", False),
        ("maybe", False),
    ],
)
def test_env_bool_parsing(value: str, expected: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_TEST_FLAG", value)
    assert bot._env_bool("SAKTHAI_TEST_FLAG") is expected


def test_env_bool_returns_the_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_TEST_FLAG", raising=False)
    assert bot._env_bool("SAKTHAI_TEST_FLAG") is False
    assert bot._env_bool("SAKTHAI_TEST_FLAG", default=True) is True


def test_session_key_prefers_chat_id_and_falls_back_to_user_id() -> None:
    assert bot._session_key(10, 20) == 10
    assert bot._session_key(None, 20) == 20
    assert bot._session_key(None, None) is None


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


# ---------------------------------------------------------------------------
# Startup wiring
# ---------------------------------------------------------------------------


def test_main_refuses_to_start_without_a_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        bot.main()


def test_main_registers_every_handler_and_starts_polling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pins the command wiring, so a handler that is written but never
    registered — invisible to every other test in this file, since they call
    the coroutines directly — fails here."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")

    registered: list[object] = []
    polled: list[bool] = []

    class _FakeApplication:
        def add_handler(self, handler: object) -> None:
            registered.append(handler)

        def run_polling(self) -> None:
            polled.append(True)

    class _FakeBuilder:
        def token(self, token: str) -> _FakeBuilder:
            assert token == "test-token"
            return self

        def build(self) -> _FakeApplication:
            return _FakeApplication()

    monkeypatch.setattr(bot, "ApplicationBuilder", _FakeBuilder)
    monkeypatch.setattr(bot, "_ensure_main_thread_event_loop", lambda: None)

    bot.main()

    command_handlers = [h for h in registered if isinstance(h, bot.CommandHandler)]
    commands = {name for handler in command_handlers for name in handler.commands}
    assert commands == {
        "start",
        "model",
        "m",
        "persona",
        "agent",
        "models",
        "status",
        "workflow",
        "workflows",
        "help",
    }
    # One MessageHandler for free-form text, on top of the commands.
    assert len(registered) == len(commands) + 1
    assert polled == [True]


def test_ensure_main_thread_event_loop_installs_a_loop() -> None:
    """python-telegram-bot's startup needs a current event loop on this
    thread; `main()` calls this before building the application."""
    previous = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(previous)
    try:
        bot._ensure_main_thread_event_loop()
        installed = asyncio.get_event_loop()
        assert installed is not previous
        assert not installed.is_closed()
        installed.close()
    finally:
        asyncio.set_event_loop(None)
