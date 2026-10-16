"""Tests for sakthai team CLI commands."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.team.models import PipelineResult, StepResult


def test_cli_team_list() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["team", "list"])
    assert result.exit_code == 0
    assert "feature-delivery" in result.output
    assert "code-review" in result.output


def test_cli_team_list_json() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["team", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert "feature-delivery" in names


def test_cli_team_show() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["team", "show", "feature-delivery"])
    assert result.exit_code == 0
    assert "feature-delivery" in result.output
    assert "SAKTHAI" in result.output
    assert "SAKKING" in result.output


def test_cli_team_show_json() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["team", "show", "feature-delivery", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "feature-delivery"
    assert len(data["steps"]) == 4


def test_cli_team_show_unknown() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["team", "show", "unknown-pipeline"])
    assert result.exit_code != 0
    assert "Unknown pipeline" in result.output


def test_cli_team_run() -> None:
    runner = CliRunner()
    mock_pipeline_result = PipelineResult(
        pipeline_name="code-review",
        task="Audit login flow",
        steps=[
            StepResult(
                step_name="scope",
                persona="sakthai",
                output="Scope defined.",
                iterations=1,
                usage={"total_tokens": 100},
                duration_seconds=1.2,
            )
        ],
        success=True,
        summary="Summary report",
    )

    with patch("sakthai.cli.team.execute_pipeline", return_value=mock_pipeline_result):
        result = runner.invoke(main, ["team", "run", "code-review", "Audit login flow"])
        assert result.exit_code == 0
        assert "Launching Team Workflow" in result.output
        assert "Summary report" in result.output


def test_cli_team_run_json() -> None:
    runner = CliRunner()
    mock_pipeline_result = PipelineResult(
        pipeline_name="code-review",
        task="Audit login flow",
        steps=[
            StepResult(
                step_name="scope",
                persona="sakthai",
                output="Scope defined.",
                iterations=1,
                usage={"total_tokens": 100},
                duration_seconds=1.2,
            )
        ],
        success=True,
        summary="Summary report",
    )

    with patch("sakthai.cli.team.execute_pipeline", return_value=mock_pipeline_result):
        result = runner.invoke(main, ["team", "run", "code-review", "Audit login flow", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["pipeline"] == "code-review"
        assert data["success"] is True
        assert len(data["steps"]) == 1


def _failed_pipeline_result() -> PipelineResult:
    return PipelineResult(
        pipeline_name="code-review",
        task="Audit login flow",
        steps=[
            StepResult(
                step_name="scope",
                persona="sakthai",
                output="",
                iterations=0,
                usage={},
                duration_seconds=0.1,
                is_error=True,
                error_message="No Hugging Face credentials found.",
            )
        ],
        success=False,
        summary="Summary report",
    )


@pytest.mark.parametrize("extra", [[], ["--json"]])
def test_cli_team_run_failed_pipeline_exits_nonzero(extra: list[str]) -> None:
    """A failed pipeline fails the command, so a script or cron job can tell."""
    runner = CliRunner()
    with patch("sakthai.cli.team.execute_pipeline", return_value=_failed_pipeline_result()):
        result = runner.invoke(main, ["team", "run", "code-review", "Audit login flow", *extra])
    assert result.exit_code == 1, result.output
    if extra:
        assert json.loads(result.output)["success"] is False
    else:
        assert "Summary report" in result.output
