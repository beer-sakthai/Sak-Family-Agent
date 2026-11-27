"""Tests for GitHub CLI Subagents and Dynamic Workflows Integration."""

import subprocess

import pytest

from sakthai.team.github_subagents import (
    GitHubCLISubagentFramework,
    GitHubSubagentConfig,
    GitHubSubagentRole,
    run_github_audit_pipeline,
    run_github_maintenance_pipeline,
    run_github_security_pipeline,
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

    code3, msg3 = fw.run_gh(["pr", "merge", "123", "--squash"])
    assert code3 == 1
    assert "Auto-merge blocked" in msg3


def test_check_duplicate_prs_detects_branch_and_file_overlaps(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args: list[str]) -> tuple[int, str]:
        if "list" in args:
            return 0, '[{"number": 999, "title": "feat: test", "headRefName": "feat/overlap-branch", "url": "https://github.com/test/999"}]'
        if "view" in args and "999" in args:
            return 0, '{"files": [{"path": "personas/sakthai/agent/guardrails.py"}]}'
        return 0, "[]"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)

    # Overlap by branch name
    branch_overlaps = fw.check_duplicate_prs(branch_name="feat/overlap-branch")
    assert len(branch_overlaps) == 1
    assert branch_overlaps[0]["number"] == 999

    # Overlap by target files
    file_overlaps = fw.check_duplicate_prs(target_files=["personas/sakthai/agent/guardrails.py"])
    assert len(file_overlaps) == 1
    assert file_overlaps[0]["number"] == 999

    # No overlap
    no_overlaps = fw.check_duplicate_prs(target_files=["other/unrelated/path.py"], branch_name="feat/different")
    assert len(no_overlaps) == 0


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


@pytest.mark.asyncio
async def test_run_github_maintenance_pipeline(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Test vacuum on temporary sqlite db
    db_file = tmp_path / "test.db"
    import sqlite3

    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE t (id INT);")
    conn.commit()
    conn.close()

    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))

    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args):
        if "issue" in args:
            return 0, '[{"number": 1, "title": "issue 1"}]'
        if "pr" in args:
            return 0, '[{"number": 2, "title": "pr 2"}]'
        return 0, "[]"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)
    report = await run_github_maintenance_pipeline(framework=fw, vacuum=True, run_audit=True)

    assert "Shard Maintenance" in report.phases_completed
    assert "Backlog Discovery" in report.phases_completed
    assert "Fleet Audit" in report.phases_completed
    assert report.auto_merge_blocked is True
    assert report.open_prs_audited == 1


@pytest.mark.asyncio
async def test_run_github_security_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args):
        if "branches/main" in " ".join(args):
            return 0, '{"name": "main", "protected": true}'
        return 0, "{}"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)
    report = await run_github_security_pipeline(framework=fw)

    assert "Branch Protection" in report.phases_completed
    assert "Action Pinning" in report.phases_completed
    assert "Credential Hygiene" in report.phases_completed
    assert report.auto_merge_blocked is True


def test_cli_gh_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    from click.testing import CliRunner

    from sakthai.cli.team import team_cmd
    from sakthai.team.github_subagents import GitHubCLISubagentFramework

    def mock_run_gh(self, args: list[str]) -> tuple[int, str]:
        if "pr" in args:
            return 0, '[{"number": 101, "title": "feat: mock PR"}]'
        if "issue" in args:
            return 0, '[{"number": 201, "title": "mock issue"}]'
        if "branches/main" in " ".join(args):
            return 0, '{"name": "main", "protected": true}'
        return 0, "[]"

    monkeypatch.setattr(GitHubCLISubagentFramework, "run_gh", mock_run_gh)

    runner = CliRunner()
    res_maint = runner.invoke(team_cmd, ["gh", "maintenance", "--json"])
    assert res_maint.exit_code == 0
    assert "gh-dyn-maintenance-v1" in res_maint.output

    res_audit = runner.invoke(team_cmd, ["gh", "audit", "--json"])
    assert res_audit.exit_code == 0
    assert "gh-dyn-workflow-v1" in res_audit.output

    res_sec = runner.invoke(team_cmd, ["gh", "security", "--json"])
    assert res_sec.exit_code == 0
    assert "gh-dyn-security-v1" in res_sec.output


def test_check_duplicate_prs_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()
    # code != 0
    monkeypatch.setattr(fw, "run_gh", lambda args: (1, "error"))
    assert fw.check_duplicate_prs() == []

    # empty output
    monkeypatch.setattr(fw, "run_gh", lambda args: (0, ""))
    assert fw.check_duplicate_prs() == []

    # non-list JSON
    monkeypatch.setattr(fw, "run_gh", lambda args: (0, '{"error": "not a list"}'))
    assert fw.check_duplicate_prs() == []

    # invalid JSON
    monkeypatch.setattr(fw, "run_gh", lambda args: (0, "{not valid json"))
    assert fw.check_duplicate_prs() == []

    # Branch doesn't match and target_files is None
    monkeypatch.setattr(fw, "run_gh", lambda args: (0, '[{"number": 1, "headRefName": "other"}]'))
    assert fw.check_duplicate_prs(branch_name="main") == []

    # Target files present but view fails
    def mock_run_gh(args):
        if "list" in args:
            return 0, '[{"number": 1, "headRefName": "other"}]'
        return 1, "view error"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)
    assert fw.check_duplicate_prs(target_files=["foo.py"]) == []


@pytest.mark.asyncio
async def test_run_github_maintenance_pipeline_edge_cases(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. DB integrity check fails
    db_bad = tmp_path / "bad.db"
    import sqlite3
    conn = sqlite3.connect(db_bad)
    conn.execute("CREATE TABLE t (id INT);")
    conn.commit()
    conn.close()

    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    fw = GitHubCLISubagentFramework()

    class FakeCursor:
        def execute(self, q): pass
        def fetchone(self): return ("corrupt",)

    class FakeConn:
        def cursor(self): return FakeCursor()
        def close(self): pass
        def execute(self, q): pass

    monkeypatch.setattr(sqlite3, "connect", lambda p: FakeConn())

    def mock_run_gh(args):
        if "issue" in args:
            return 0, "not valid json"
        if "pr" in args:
            return 0, "not valid json"
        return 0, "[]"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)

    import sakthai.agent.eval
    monkeypatch.setattr(sakthai.agent.eval, "summarize_fleet_audit", lambda: (_ for _ in ()).throw(RuntimeError("fleet err")))

    report = await run_github_maintenance_pipeline(framework=fw, vacuum=True, run_audit=True)
    assert "Shard Maintenance" in report.phases_completed
    assert any(d.get("phase") == "fleet" and d.get("status") == "error" for d in report.details)

    # 2. Vacuum execution raises exception
    class VacuumFailConn:
        def cursor(self):
            class C:
                def execute(self, q): pass
                def fetchone(self): return ("ok",)
            return C()
        def close(self): pass
        def execute(self, q):
            if "VACUUM" in q:
                raise sqlite3.OperationalError("disk error")

    monkeypatch.setattr(sqlite3, "connect", lambda p: VacuumFailConn())
    report_vac_fail = await run_github_maintenance_pipeline(framework=fw, vacuum=True)
    assert "Shard Maintenance" in report_vac_fail.phases_completed


@pytest.mark.asyncio
async def test_run_github_security_pipeline_edge_cases(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    fw = GitHubCLISubagentFramework()

    def mock_run_gh(args):
        if "branches/main" in " ".join(args):
            return 0, "invalid json"
        return 0, "{}"

    monkeypatch.setattr(fw, "run_gh", mock_run_gh)

    # Create dummy workflow with unpinned action in a temporary dir
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "unpinned.yml").write_text("uses: actions/checkout@v4\nuses: actions/setup-node@v3#comment\n", encoding="utf-8")
    # Subdirectory with .yml to trigger OSError on read_text
    (wf_dir / "broken.yml").mkdir()

    monkeypatch.chdir(tmp_path)

    (tmp_path / "secret.py").write_text("fake_key = 'sk-123456789012345678901234567890'\n", encoding="utf-8")
    # Subdirectory with .py to trigger OSError on read_text
    (tmp_path / "broken.py").mkdir()

    report = await run_github_security_pipeline(framework=fw)
    assert "Branch Protection" in report.phases_completed
    assert any(d.get("phase") == "action_pinning" and d.get("unpinned_count", 0) >= 1 for d in report.details)
    assert any(d.get("phase") == "credential_hygiene" and d.get("leak_count", 0) >= 1 for d in report.details)

