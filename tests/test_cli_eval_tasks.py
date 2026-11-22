"""Tests for `sakthai eval tasks` and `sakthai eval bench` commands."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

import sakthai.cli.eval as eval_cli
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_eval_tasks_text_and_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tasks"])
    assert result.exit_code == 0
    assert "Registered lm-eval Tasks" in result.output
    assert "soul_following" in result.output

    result_json = runner.invoke(main, ["eval", "tasks", "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.output)
    assert isinstance(data, list)
    soul_task = next(item for item in data if item["task"] == "soul_following")
    assert soul_task["rows"] == 9
    assert soul_task["file"] == "soul_following.yaml"


def test_eval_bench_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "bench", "--dry-run", "--", "--model", "test-model"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "scripts/eval/run_bench.py" in result.output
    assert "--model test-model" in result.output


def test_eval_bench_exit_code_propagation(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.setattr(eval_cli, "run_repo_argv", lambda argv, **kw: 13)
    result = runner.invoke(main, ["eval", "bench", "--legacy"])
    assert result.exit_code == 13
