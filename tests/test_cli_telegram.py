"""Tests for `sakthai telegram` commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

import sakthai.cli.telegram as tg_mod
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_telegram_serve_requires_token(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.setattr(tg_mod, "telegram_bot_token", lambda: None)
    result = runner.invoke(main, ["telegram", "serve"])
    assert result.exit_code != 0
    assert "TELEGRAM_BOT_TOKEN environment variable not set" in result.output


def test_telegram_serve_launches_bot(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    called = []
    monkeypatch.setattr(tg_mod, "telegram_bot_token", lambda: "fake-token")

    import sakthai.telegram.bot as bot_module

    monkeypatch.setattr(bot_module, "main", lambda: called.append(True))
    result = runner.invoke(main, ["telegram", "serve"])
    assert result.exit_code == 0
    assert called == [True]


def test_telegram_send_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["telegram", "send", "--text", "hello world", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "scripts/telegram_send.py" in result.output
    assert "hello world" in result.output

    result_chat = runner.invoke(
        main, ["telegram", "send", "--text", "alert", "--chat-id", "12345", "--dry-run"]
    )
    assert result_chat.exit_code == 0
    assert "12345" in result_chat.output


def test_telegram_verify_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["telegram", "verify", "--dry-run"])
    assert result.exit_code == 0
    assert "scripts/verify_vm_telegram_agents.py" in result.output


def test_telegram_setup_vm_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["telegram", "setup-vm", "--dry-run"])
    assert result.exit_code == 0
    assert "scripts/setup_vm_telegram_agents.py" in result.output


def test_telegram_exit_code_propagation(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.setattr(tg_mod, "run_repo_argv", lambda argv, **kw: 9)
    assert runner.invoke(main, ["telegram", "verify"]).exit_code == 9
    assert runner.invoke(main, ["telegram", "setup-vm"]).exit_code == 9
    assert runner.invoke(main, ["telegram", "send", "-m", "hi"]).exit_code == 9
