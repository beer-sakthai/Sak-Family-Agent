"""Tests for sakthai team CLI commands."""

from __future__ import annotations

import json
from types import SimpleNamespace
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


def test_cli_team_run_unknown_pipeline_exits_nonzero() -> None:
    result = CliRunner().invoke(main, ["team", "run", "no-such-pipeline", "task"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_cli_team_run_reports_step_progress() -> None:
    ok = StepResult(
        step_name="scope",
        persona="sakthai",
        output="done",
        iterations=2,
        usage={"total_tokens": 1234},
        duration_seconds=0.5,
    )
    failed = _failed_pipeline_result().steps[0]

    def fake_execute(pipeline, task, *, on_step_start, on_step_complete, verbose):  # type: ignore[no-untyped-def]
        step = pipeline.steps[0]
        on_step_start(step, 1, 2)
        on_step_complete(ok, 1, 2)
        on_step_start(step, 2, 2)
        on_step_complete(failed, 2, 2)
        return _failed_pipeline_result()

    with patch("sakthai.cli.team.execute_pipeline", side_effect=fake_execute):
        result = CliRunner().invoke(main, ["team", "run", "code-review", "Audit"])
    assert result.exit_code == 1
    assert "[1/2]" in result.output
    assert "Done" in result.output
    assert "1,234 tokens" in result.output
    assert "Failed" in result.output
    assert "No Hugging Face credentials found." in result.output


def _report(**fields: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "workflow_id": "wf-1",
        "phases_completed": ["a", "b"],
        "open_prs_audited": 3,
        "details": [],
        "auto_merge_blocked": False,
        "high_risk_detected": True,
        "boost_triggered": False,
    }
    base.update(fields)
    return SimpleNamespace(**base)


def _async_returning(value: object):  # type: ignore[no-untyped-def]
    async def _fn(*_args: object, **_kwargs: object) -> object:
        return value

    return _fn


@pytest.mark.parametrize(
    ("command", "target", "expected"),
    [
        ("maintenance", "run_github_maintenance_pipeline", "Weekly Maintenance Pipeline Completed"),
        ("audit", "run_github_audit_pipeline", "GitHub Audit Pipeline Completed"),
        ("security", "run_github_security_pipeline", "Repository Security Audit Completed"),
    ],
)
def test_cli_team_gh_text_output(command: str, target: str, expected: str) -> None:
    details = [
        {"phase": "branch_protection", "protected": True},
        {"phase": "action_pinning", "unpinned_count": 2},
        {"phase": "credential_hygiene", "status": "clean"},
        {"phase": "other"},
    ]
    with patch(
        f"sakthai.team.github_subagents.{target}", _async_returning(_report(details=details))
    ):
        result = CliRunner().invoke(main, ["team", "gh", command])
    assert result.exit_code == 0, result.output
    assert expected in result.output
    assert "wf-1" in result.output
    if command == "security":
        assert "Branch Protection: Enabled" in result.output
        assert "Unpinned Action References: 2" in result.output
        assert "Credential Hygiene: CLEAN" in result.output


@pytest.mark.parametrize(
    ("command", "target"),
    [
        ("maintenance", "run_github_maintenance_pipeline"),
        ("audit", "run_github_audit_pipeline"),
        ("security", "run_github_security_pipeline"),
    ],
)
def test_cli_team_gh_json_output(command: str, target: str) -> None:
    with patch(f"sakthai.team.github_subagents.{target}", _async_returning(_report())):
        result = CliRunner().invoke(main, ["team", "gh", command, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["workflow_id"] == "wf-1"
    assert data["phases_completed"] == ["a", "b"]


def test_cli_team_gh_security_reports_unprotected_branch() -> None:
    details = [{"phase": "branch_protection", "protected": False}]
    with patch(
        "sakthai.team.github_subagents.run_github_security_pipeline",
        _async_returning(_report(details=details)),
    ):
        result = CliRunner().invoke(main, ["team", "gh", "security"])
    assert "Disabled / Unconfigured" in result.output
