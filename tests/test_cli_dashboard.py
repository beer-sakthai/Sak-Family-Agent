"""Tests for `sakthai dashboard` commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

import sakthai.cli.dashboard as dash_mod
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_dashboard_dev_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["dashboard", "dev", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "npm run dev" in result.output


def test_dashboard_build_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["dashboard", "build", "--dry-run"])
    assert result.exit_code == 0
    assert "npm run build" in result.output


def test_dashboard_test_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["dashboard", "test", "--dry-run"])
    assert result.exit_code == 0
    assert "npm run test" in result.output


def test_dashboard_install_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["dashboard", "install", "--dry-run"])
    assert result.exit_code == 0
    assert "npm install" in result.output


def test_dashboard_gen_types_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["dashboard", "gen-types", "--dry-run"])
    assert result.exit_code == 0
    assert "scripts/gen_dashboard_types.py" in result.output


def test_dashboard_missing_npm(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.setattr(dash_mod.shutil, "which", lambda cmd: None)
    result = runner.invoke(main, ["dashboard", "dev"])
    assert result.exit_code != 0
    assert "Node.js 22+ is required" in result.output


def test_dashboard_exit_code_propagation(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.setattr(dash_mod, "run_repo_argv", lambda argv, **kw: 5)
    for cmd in ["dev", "build", "test", "install", "gen-types"]:
        result = runner.invoke(main, ["dashboard", cmd])
        assert result.exit_code == 5
