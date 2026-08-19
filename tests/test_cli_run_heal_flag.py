"""CLI tests for the ``--heal`` flag (runtime self-healing) on ``sakthai run``.

Distinct from ``tests/test_cli_heal.py``, which covers the ``sakthai heal``
subcommand (the CI fix-PR agent in ``selfheal/``). This file covers the
runtime ``healing/`` supervisor opt-in on ``sakthai run``.
"""

from __future__ import annotations

from click.testing import CliRunner

from sakthai.agent.loop import AgentResult
from sakthai.cli import agent as cli_agent


def _spy_factory(captured: dict):
    def _spy_run_agent(*args, **kwargs) -> AgentResult:
        captured["supervisor"] = kwargs.get("supervisor")
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn")

    return _spy_run_agent


def test_run_heal_flag_constructs_supervisor(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))  # hermetic recovery.db/snapshots

    captured: dict = {}
    monkeypatch.setattr(cli_agent, "run_agent", _spy_factory(captured))

    result = CliRunner().invoke(cli_agent.run, ["--heal", "--no-mcp", "do thing"])

    assert result.exit_code == 0, result.output
    assert captured["supervisor"] is not None


def test_run_without_heal_passes_no_supervisor(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))

    captured: dict = {}
    monkeypatch.setattr(cli_agent, "run_agent", _spy_factory(captured))

    result = CliRunner().invoke(cli_agent.run, ["--no-mcp", "do thing"])

    assert result.exit_code == 0, result.output
    assert captured["supervisor"] is None


def test_run_heal_env_enables_supervisor(monkeypatch, tmp_path) -> None:
    """SAKTHAI_SELF_HEAL=1 enables the supervisor even without --heal."""
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    monkeypatch.setenv("SAKTHAI_SELF_HEAL", "1")

    captured: dict = {}
    monkeypatch.setattr(cli_agent, "run_agent", _spy_factory(captured))

    result = CliRunner().invoke(cli_agent.run, ["--no-mcp", "do thing"])

    assert result.exit_code == 0, result.output
    assert captured["supervisor"] is not None
