"""The chat command wires options into SakThaiApp and runs it."""

from __future__ import annotations

import types
from typing import Any

import pytest
from click.testing import CliRunner

import sakthai.cli.chat as chat_cli
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class _FakeStream:
    def __init__(self, atty: bool) -> None:
        self._atty = atty

    def isatty(self) -> bool:
        return self._atty


@pytest.fixture(autouse=True)
def _fake_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default ``chat_cli.sys`` to "yes, it's a real terminal".

    CliRunner's own ``isolation()`` replaces the *real* ``sys.stdin``/
    ``sys.stdout`` with fresh non-tty buffer wrappers for the duration of
    ``invoke()``, so patching attributes on the pre-invoke stream objects
    would be silently discarded. Instead this replaces the ``sys`` name
    bound in ``chat_cli``'s own module namespace with a small fake, so the
    module's ``sys.stdin.isatty()`` / ``sys.stdout.isatty()`` calls read our
    fake regardless of what CliRunner does to the real ``sys`` module. Only
    the test that specifically exercises the non-TTY path overrides this.
    """
    fake_sys = types.SimpleNamespace(stdin=_FakeStream(True), stdout=_FakeStream(True))
    monkeypatch.setattr(chat_cli, "sys", fake_sys)


def test_chat_constructs_and_runs_the_app(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    result = runner.invoke(main, ["chat", "--persona", "sakthai", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert captured.get("ran") is True
    assert captured["persona"] == "sakthai"
    assert captured["model"] == chat_cli.DEFAULT_CHAT_MODEL


def test_chat_forwards_model_provider_caveman_and_skills(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    result = runner.invoke(
        main,
        [
            "chat",
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
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured["model"] == "gpt-4o"
    assert captured["provider"] == "openai"
    assert captured["caveman"] == "lite"
    assert captured["with_skills"] == ("skill-a", "skill-b")


def test_chat_defaults_to_sakthai_persona(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    result = runner.invoke(main, ["chat", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert captured["persona"] == "sakthai"


def test_chat_closes_store_on_normal_exit(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    closed: list[bool] = []

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def run(self) -> None:
            pass

    class _FakeStore:
        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    monkeypatch.setattr(chat_cli, "MemoryStore", lambda: _FakeStore())
    result = runner.invoke(main, ["chat", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert closed == [True]


def test_chat_defaults_to_local_sakthai_model() -> None:
    # The default backend contract: the fine-tuned SakThai weights served by a
    # local Ollama tag (built by scripts/setup_local_model.sh). Change these
    # deliberately, together with the README "Serving" section.
    assert chat_cli.DEFAULT_CHAT_PROVIDER == "ollama"
    assert chat_cli.DEFAULT_CHAT_MODEL == "sakthai"


def test_chat_rejects_invalid_persona(runner: CliRunner, sakthai_home: object) -> None:
    result = runner.invoke(main, ["chat", "--persona", "notreal", "--no-mcp"])
    assert result.exit_code != 0
    assert "notreal" in result.output


def test_chat_closes_store_and_propagates_when_app_run_raises(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    """A genuine runtime error from inside the app must propagate, not be
    relabeled as "chat needs an interactive terminal" -- only the TTY
    precheck may raise that friendly message now (see the test below)."""
    closed: list[bool] = []

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def run(self) -> None:
            raise RuntimeError("boom from inside the app")

    class _FakeStore:
        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    monkeypatch.setattr(chat_cli, "MemoryStore", lambda: _FakeStore())
    result = runner.invoke(main, ["chat", "--no-mcp"])
    assert result.exit_code != 0
    assert "interactive terminal" not in result.output
    assert isinstance(result.exception, RuntimeError)
    assert closed == [True]


def test_chat_rejects_non_tty_with_friendly_message(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    """Without a real TTY, chat raises the friendly ClickException *before*
    constructing the app or opening the store -- no app.run() is attempted."""
    constructed: list[bool] = []

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            constructed.append(True)

        def run(self) -> None:
            pass

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    monkeypatch.setattr(chat_cli.sys, "stdin", _FakeStream(False))
    result = runner.invoke(main, ["chat", "--no-mcp"])
    assert result.exit_code != 0
    assert "interactive terminal" in result.output
    assert constructed == []
