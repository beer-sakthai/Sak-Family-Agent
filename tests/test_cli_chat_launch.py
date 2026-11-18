"""The chat command wires options into SakThaiApp or run_chat based on --ui."""

from __future__ import annotations

from typing import Any

import pytest
from click.testing import CliRunner

import sakthai.cli.chat as chat_cli
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_chat_launches_inline_when_ui_inline(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    def _fake_run_chat(**kwargs: Any) -> None:
        captured.update(kwargs)
        captured["ran"] = "inline"

    monkeypatch.setattr(chat_cli, "run_chat", _fake_run_chat)
    result = runner.invoke(
        main, ["chat", "--ui", "inline", "--no-mcp", "--model", "sakthai", "--provider", "ollama"]
    )
    assert result.exit_code == 0, result.output
    assert captured.get("ran") == "inline"
    assert captured["persona"] == "sakthai"
    assert captured["model"] == "sakthai"


def test_chat_auto_defaults_to_inline_in_non_interactive_runner(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    def _fake_run_chat(**kwargs: Any) -> None:
        captured["ran"] = "inline"

    monkeypatch.setattr(chat_cli, "run_chat", _fake_run_chat)
    monkeypatch.setattr(chat_cli, "_is_interactive", lambda: False)
    result = runner.invoke(main, ["chat", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert captured.get("ran") == "inline"


def test_chat_auto_picks_tui_when_interactive(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = "tui"

    monkeypatch.setattr(chat_cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(chat_cli, "_make_tui_app", lambda **kwargs: _FakeApp(**kwargs))
    result = runner.invoke(main, ["chat", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert captured.get("ran") == "tui"
    assert captured["persona"] == "sakthai"


def test_chat_tui_rejects_non_interactive_terminal(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    monkeypatch.setattr(chat_cli, "_is_interactive", lambda: False)
    result = runner.invoke(main, ["chat", "--ui", "tui", "--no-mcp"])
    assert result.exit_code != 0
    assert "--ui tui needs an interactive terminal" in result.output


def test_chat_forwards_options_to_tui_app(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = "tui"

    monkeypatch.setattr(chat_cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(chat_cli, "_make_tui_app", lambda **kwargs: _FakeApp(**kwargs))
    result = runner.invoke(
        main,
        [
            "chat",
            "--persona",
            "saksee",
            "--no-mcp",
            "--model",
            "gpt-4o",
            "--provider",
            "openai",
            "--caveman",
            "lite",
            "--with-skills",
            "skill-a",
            "--with-skills",
            "skill-b",
            "--ui",
            "tui",
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured["ran"] == "tui"
    assert captured["persona"] == "saksee"
    assert captured["model"] == "gpt-4o"
    assert captured["provider"] == "openai"
    assert captured["caveman"] == "lite"
    assert captured["with_skills"] == ("skill-a", "skill-b")


def test_chat_uses_persona_memory_shard(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    opened_paths: list[str] = []

    from sakthai.memory.store import MemoryStore

    orig_init = MemoryStore.__init__

    def _tracking_init(self: Any, path: Any, *args: Any, **kwargs: Any) -> None:
        opened_paths.append(str(path))
        orig_init(self, ":memory:", *args, **kwargs)

    monkeypatch.setattr(MemoryStore, "__init__", _tracking_init)
    monkeypatch.setattr(chat_cli, "run_chat", lambda **kw: None)
    monkeypatch.setattr(chat_cli, "_is_interactive", lambda: False)

    result = runner.invoke(main, ["chat", "--persona", "sakjules", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert any("sakjules" in p for p in opened_paths)


def test_chat_internal_helpers() -> None:
    from sakthai.agent.tui import SakThaiApp
    from sakthai.memory.store import MemoryStore

    app = chat_cli._make_tui_app(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="sakthai",
        provider="ollama",
        caveman=None,
        with_skills=(),
        store=MemoryStore(":memory:"),
    )
    assert isinstance(app, SakThaiApp)

    # _is_interactive
    assert isinstance(chat_cli._is_interactive(), bool)

    # _make_read_input
    reader = chat_cli._make_read_input()
    assert callable(reader)
