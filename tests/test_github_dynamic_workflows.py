"""Tests for GitHub CLI Subagents and Dynamic Workflows Integration."""

import subprocess

import pytest

from sakthai.team.github_subagents import (
    GitHubCLISubagentFramework,
    GitHubSubagentConfig,
    GitHubSubagentRole,
    run_github_audit_pipeline,
)
from scripts.workflows.github_cli_dynamic_workflow import (
    execute_github_workflow,
    phase,
    run_gh_command,
)


def test_framework_initialization() -> None:
    fw = GitHubCLISubagentFramework()
    subagents = fw.list_subagents()
    assert len(subagents) >= 2

    auditor = fw.get_subagent("github-cli-auditor")
    assert auditor is not None
    assert auditor.role == GitHubSubagentRole.AUDITOR
    assert auditor.read_only is True

    runner = fw.get_subagent("github-cli-pr-runner")
    assert runner is not None
    assert runner.role == GitHubSubagentRole.PR_RUNNER
    assert runner.read_only is False


def test_custom_subagent_registration() -> None:
    fw = GitHubCLISubagentFramework()
    custom = GitHubSubagentConfig(
        name="custom-verifier",
        role=GitHubSubagentRole.BOOST_VERIFIER,
        description="Custom verifier",
    )
    fw.register(custom)
    assert fw.get_subagent("custom-verifier") == custom


def test_run_gh_auto_merge_blocked() -> None:
    fw = GitHubCLISubagentFramework()
    code, msg = fw.run_gh(["pr", "merge", "123", "--auto"])
    assert code == 1
    assert "Auto-merge blocked" in msg

    code2, msg2 = fw.run_gh(["pr", "merge", "123", "-y"])
    assert code2 == 1
    assert "Auto-merge blocked" in msg2


def test_run_gh_subprocess_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    class MockCompletedProcess:
        returncode = 0
        stdout = '{"status": "ok"}'
        stderr = ""

    def mock_run(cmd, **kwargs):
        return MockCompletedProcess()

    monkeypatch.setattr(subprocess, "run", mock_run)
    code, out = fw.run_gh(["pr", "list"])
    assert code == 0
    assert '{"status": "ok"}' in out


@pytest.mark.asyncio
async def test_run_github_audit_pipeline_low_risk() -> None:
    mock_prs = [
        {"number": 101, "title": "feat: standard enhancement"},
        {"number": 102, "title": "fix: minor typo fix"},
    ]
    report = await run_github_audit_pipeline(mock_prs=mock_prs)

    assert report.phases_completed == [
        "Discover",
        "Audit & Triage",
        "Deep Reasoning Boost",
        "Execute & Verify",
    ]
    assert report.open_prs_audited == 2
    assert report.high_risk_detected == 0
    assert report.boost_triggered is False
    assert report.auto_merge_blocked is True


@pytest.mark.asyncio
async def test_run_github_audit_pipeline_high_risk_boost() -> None:
    mock_prs = [
        {"number": 201, "title": "feat: breaking security refactoring"},
    ]
    report = await run_github_audit_pipeline(mock_prs=mock_prs)

    assert report.open_prs_audited == 1
    assert report.high_risk_detected == 1
    assert report.boost_triggered is True
    assert report.auto_merge_blocked is True


def test_workflow_script_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test phase function
    phase("TestPhase")

    # Test run_gh_command with JSON
    class MockSuccessProc:
        stdout = '{"key": "value"}'

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: MockSuccessProc())
    res = run_gh_command(["test"])
    assert res == {"key": "value"}


def test_run_gh_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_fail(cmd, **kwargs):
        raise FileNotFoundError("gh not found")

    monkeypatch.setattr(subprocess, "run", mock_run_fail)
    code, msg = fw.run_gh(["pr", "list"])
    assert code == 127
    assert "gh command not found" in msg


@pytest.mark.asyncio
async def test_run_github_audit_pipeline_with_real_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args):
        return 0, '[{"number": 301, "title": "feat: normal change"}]'

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)
    report = await run_github_audit_pipeline(framework=fw)
    assert report.open_prs_audited == 1
    assert report.high_risk_detected == 0


@pytest.mark.asyncio
async def test_run_github_audit_pipeline_with_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args):
        return 0, "invalid json"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)
    report = await run_github_audit_pipeline(framework=fw)
    assert report.open_prs_audited == 0


@pytest.mark.asyncio
async def test_run_github_audit_pipeline_with_gh_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args):
        return 1, "simulated error"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)
    report = await run_github_audit_pipeline(framework=fw)
    assert report.open_prs_audited == 0


@pytest.mark.asyncio
async def test_execute_github_workflow_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_gh(args):
        if "pr" in args:
            return [{"number": 999, "title": "feat: test PR"}]
        return []

    monkeypatch.setattr("scripts.workflows.github_cli_dynamic_workflow.run_gh_command", mock_gh)
    res = await execute_github_workflow()
    assert res["status"] == "success"
    assert res["open_prs_count"] == 1
    assert res["audited_count"] == 1
    assert res["auto_merge_blocked"] is True
