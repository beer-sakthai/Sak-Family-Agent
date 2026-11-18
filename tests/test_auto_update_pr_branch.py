"""Unit tests for scripts/auto_update_pr_branch.py and .github/workflows/auto-update-branch.yml."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scripts.auto_update_pr_branch import (
    PRUpdateResult,
    evaluate_and_update_pr,
    fetch_open_pull_requests,
    fetch_pull_request,
    generate_step_summary,
    main,
    make_github_request,
    parse_comment_trigger,
    update_pr_branch,
)
from scripts.lint_workflow_permissions import find_scalar_permissions

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


# ============================================================================
# 1. API Client & Security Tests
# ============================================================================


def test_make_github_request_rejects_insecure_scheme() -> None:
    with pytest.raises(ValueError, match="Insecure or invalid URL scheme"):
        make_github_request("http://api.github.com/repos/test/test", "dummy-token")


def test_make_github_request_rejects_untrusted_host() -> None:
    with pytest.raises(ValueError, match="Untrusted API host"):
        make_github_request("https://evil.com/repos/test/test", "dummy-token")


@patch("urllib.request.urlopen")
def test_make_github_request_success(mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    status, data = make_github_request(
        "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent",
        "dummy-token",
    )
    assert status == 200
    assert data == {"status": "ok"}


@patch("urllib.request.urlopen")
def test_fetch_open_pull_requests(mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps(
        [{"number": 100, "title": "Test PR", "draft": False}]
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    prs = fetch_open_pull_requests("beer-sakthai/Sak-Family-Agent", "token", "main")
    assert len(prs) == 1
    assert prs[0]["number"] == 100


@patch("urllib.request.urlopen")
def test_fetch_pull_request(mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps(
        {"number": 101, "title": "Single PR", "mergeable_state": "behind"}
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    pr = fetch_pull_request("beer-sakthai/Sak-Family-Agent", "token", 101)
    assert pr is not None
    assert pr["number"] == 101
    assert pr["mergeable_state"] == "behind"


@patch("urllib.request.urlopen")
def test_update_pr_branch_success(mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 202
    mock_resp.read.return_value = json.dumps({"message": "Updating pull request branch."}).encode(
        "utf-8"
    )
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    ok, msg = update_pr_branch("beer-sakthai/Sak-Family-Agent", "token", 101)
    assert ok is True
    assert "Updating pull request branch." in msg


# ============================================================================
# 2. Evaluation Logic & State Handling Tests
# ============================================================================


def test_evaluate_and_update_pr_skips_draft() -> None:
    pr_data = {
        "number": 10,
        "title": "Draft PR",
        "draft": True,
        "base": {"ref": "main"},
        "head": {"ref": "feat", "repo": {"full_name": "owner/repo"}},
    }
    result = evaluate_and_update_pr("owner/repo", "token", pr_data)
    assert result.status == "skipped"
    assert "Draft" in result.message


def test_evaluate_and_update_pr_skips_unpermitted_fork() -> None:
    pr_data = {
        "number": 11,
        "title": "Fork PR",
        "draft": False,
        "maintainer_can_modify": False,
        "base": {"ref": "main"},
        "head": {"ref": "feat", "repo": {"full_name": "contributor/repo"}},
    }
    result = evaluate_and_update_pr("owner/repo", "token", pr_data)
    assert result.status == "skipped"
    assert "Fork" in result.message


@patch("scripts.auto_update_pr_branch.fetch_pull_request")
def test_evaluate_and_update_pr_detects_conflict(mock_fetch: MagicMock) -> None:
    mock_fetch.return_value = {
        "number": 12,
        "mergeable": False,
        "mergeable_state": "dirty",
    }
    pr_data = {
        "number": 12,
        "title": "Conflicting PR",
        "draft": False,
        "base": {"ref": "main"},
        "head": {"ref": "feat", "repo": {"full_name": "owner/repo"}},
    }
    result = evaluate_and_update_pr("owner/repo", "token", pr_data)
    assert result.status == "conflict"
    assert "conflict" in result.message.lower()


@patch("scripts.auto_update_pr_branch.update_pr_branch")
@patch("scripts.auto_update_pr_branch.fetch_pull_request")
def test_evaluate_and_update_pr_behind_triggers_update(
    mock_fetch: MagicMock,
    mock_update: MagicMock,
) -> None:
    mock_fetch.return_value = {
        "number": 13,
        "mergeable": True,
        "mergeable_state": "behind",
    }
    mock_update.return_value = (True, "Updating pull request branch.")

    pr_data = {
        "number": 13,
        "title": "Behind PR",
        "draft": False,
        "base": {"ref": "main"},
        "head": {"ref": "feat", "repo": {"full_name": "owner/repo"}},
    }
    result = evaluate_and_update_pr("owner/repo", "token", pr_data)
    assert result.status == "updated"
    assert "updated successfully" in result.message.lower()
    mock_update.assert_called_once_with("owner/repo", "token", 13)


@patch("scripts.auto_update_pr_branch.fetch_pull_request")
def test_evaluate_and_update_pr_dry_run(mock_fetch: MagicMock) -> None:
    mock_fetch.return_value = {
        "number": 14,
        "mergeable": True,
        "mergeable_state": "behind",
    }
    pr_data = {
        "number": 14,
        "title": "Behind PR Dry Run",
        "draft": False,
        "base": {"ref": "main"},
        "head": {"ref": "feat", "repo": {"full_name": "owner/repo"}},
    }
    result = evaluate_and_update_pr("owner/repo", "token", pr_data, dry_run=True)
    assert result.status == "updated"
    assert "[DRY-RUN]" in result.message


@patch("scripts.auto_update_pr_branch.fetch_pull_request")
def test_evaluate_and_update_pr_already_clean(mock_fetch: MagicMock) -> None:
    mock_fetch.return_value = {
        "number": 15,
        "mergeable": True,
        "mergeable_state": "clean",
    }
    pr_data = {
        "number": 15,
        "title": "Clean PR",
        "draft": False,
        "base": {"ref": "main"},
        "head": {"ref": "feat", "repo": {"full_name": "owner/repo"}},
    }
    result = evaluate_and_update_pr("owner/repo", "token", pr_data)
    assert result.status == "already_up_to_date"


# ============================================================================
# 3. Comment Parsing & Summary Generation Tests
# ============================================================================


def test_parse_comment_trigger() -> None:
    assert parse_comment_trigger("/update") is True
    assert parse_comment_trigger("/update-branch please") is True
    assert parse_comment_trigger("@sakjules update") is True
    assert parse_comment_trigger("/autoupdate") is True
    assert parse_comment_trigger("Looks good to me!") is False
    assert parse_comment_trigger("regular comment") is False


def test_generate_step_summary_formatting() -> None:
    results = [
        PRUpdateResult(1, "Updated feature", "main", "feat-1", "updated", "Updated OK"),
        PRUpdateResult(2, "In-sync feature", "main", "feat-2", "already_up_to_date", "In sync"),
        PRUpdateResult(3, "Conflict feature", "main", "feat-3", "conflict", "Has conflicts"),
        PRUpdateResult(4, "Draft feature", "main", "feat-4", "skipped", "Draft"),
    ]
    summary = generate_step_summary(results)
    assert "Pull Request Branch Synchronization Summary" in summary
    assert "**Total Evaluated:** 4" in summary
    assert "**Updated:** 1" in summary
    assert "**Conflicts:** 1" in summary
    assert "Updated feature" in summary
    assert "Conflict feature" in summary


# ============================================================================
# 4. CLI Execution & Main Flow Tests
# ============================================================================


def test_main_missing_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    ret = main(["--repository", "", "--token", "test"])
    assert ret == 1


def test_main_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    ret = main(["--repository", "owner/repo", "--token", ""])
    assert ret == 1


@patch("scripts.auto_update_pr_branch.evaluate_and_update_pr")
@patch("scripts.auto_update_pr_branch.fetch_open_pull_requests")
def test_main_push_event_success(
    mock_fetch: MagicMock,
    mock_eval: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_fetch.return_value = [
        {"number": 20, "title": "PR 20", "draft": False, "base": {"ref": "main"}}
    ]
    mock_eval.return_value = PRUpdateResult(20, "PR 20", "main", "feat", "updated", "Updated")

    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")

    ret = main(["--repository", "owner/repo", "--token", "test", "--base-branch", "main"])
    assert ret == 0
    assert summary_file.is_file()
    assert "#20" in summary_file.read_text(encoding="utf-8")


# ============================================================================
# 5. Workflow YAML Linting & Invariant Tests
# ============================================================================


def test_auto_update_workflow_exists_and_valid() -> None:
    workflow_path = WORKFLOWS_DIR / "auto-update-branch.yml"
    assert workflow_path.is_file(), "auto-update-branch.yml does not exist"

    content = workflow_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    assert isinstance(data, dict)
    assert data["name"] == "Auto Update Out-of-Date Branches"
    assert "concurrency" in data, "auto-update-branch.yml must declare concurrency"

    # Triggers
    on_clause = data.get("on") or data.get(True) or {}
    assert "push" in on_clause
    assert "pull_request" in on_clause
    assert "schedule" in on_clause
    assert "issue_comment" in on_clause
    assert "workflow_dispatch" in on_clause

    # Permissions
    assert data.get("permissions") == {}, "Top-level permissions must be empty mapping"
    job_perms = data["jobs"]["auto-update"]["permissions"]
    assert job_perms.get("contents") == "write"
    assert job_perms.get("pull-requests") == "write"

    # Pinned actions
    assert "step-security/harden-runner@1d88384fd173af6ecb012dfd0264a306b711241a" in content
    assert "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683" in content
    assert "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0" in content


def test_no_scalar_permissions_in_auto_update_workflow() -> None:
    findings = find_scalar_permissions(WORKFLOWS_DIR)
    assert findings == [], f"Scalar permissions detected: {findings}"
