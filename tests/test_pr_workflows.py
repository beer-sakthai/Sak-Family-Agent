"""Tests for PR automation and setup workflows: Harden-Runner, timeouts, and permissions."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

PR_SETUP_WORKFLOW_FILES = [
    "copilot-setup-steps.yml",
    "labeler.yml",
    "pr-lint.yml",
    "pr-label-checker.yml",
    "pr-codename.yml",
    "pr-comment-trigger.yml",
    "pr-automation.yml",
    "update-pr-reminder.yml",
    "update-pr-branches-from-main.yml",
    "reusable-update-pr-branches.yml",
    "daily-pr-review.yml",
    "git-pr-release.yml",
    "reusable-comment-pr.yml",
    "reusable-manual-approval-gate.yml",
    "auto-merge-bot.yml",
    "merge-pr-action.yml",
    "merge-pr.yml",
    "automerge-pr.yml",
    "auto-label-merge-conflicts.yml",
    "self-approve.yml",
    "automated-pr-maintenance.yml",
    "gemini-review-bot.yml",
    "gemini-code-review-action.yml",
    "dependabot-auto-merge.yml",
    "dependabot-auto-merge-cli.yml",
    "dependabot-automerge.yml",
    "dependabot-fetch-metadata.yml",
    "dependabot-helper.yml",
    "dependabot-issue.yml",
    "dependabot-workflow.yml",
    "safe-dependabot.yml",
    "auto-reviewer-assign.yml",
    "autolabeler-codeowners.yml",
]

HARDEN_RUNNER_ACTION = "step-security/harden-runner@1d88384fd173af6ecb012dfd0264a306b711241a"


def test_pr_workflows_exist_and_valid_yaml() -> None:
    """Ensure all PR and setup workflow files exist and parse as valid YAML."""
    for filename in PR_SETUP_WORKFLOW_FILES:
        path = WORKFLOWS_DIR / filename
        assert path.is_file(), f"{filename} does not exist"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{filename} is not valid YAML dictionary"


def test_pr_workflows_have_concurrency() -> None:
    """Ensure all PR and setup workflows declare a concurrency group."""
    for filename in PR_SETUP_WORKFLOW_FILES:
        path = WORKFLOWS_DIR / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "concurrency" in data, f"{filename} is missing a top-level concurrency declaration"


def test_pr_workflows_have_harden_runner() -> None:
    """Ensure every job in PR workflows includes StepSecurity Harden-Runner with audit policy."""
    for filename in PR_SETUP_WORKFLOW_FILES:
        path = WORKFLOWS_DIR / filename
        content = path.read_text(encoding="utf-8")
        assert HARDEN_RUNNER_ACTION in content, (
            f"{filename} must integrate StepSecurity Harden-Runner pinned to {HARDEN_RUNNER_ACTION}"
        )
        assert "egress-policy: audit" in content, (
            f"{filename} Harden-Runner must configure 'egress-policy: audit'"
        )


def test_pr_workflows_have_job_timeouts() -> None:
    """Ensure every runner job in PR workflows declares explicit timeout-minutes."""
    for filename in PR_SETUP_WORKFLOW_FILES:
        path = WORKFLOWS_DIR / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        jobs = data.get("jobs", {})
        for job_name, job_def in jobs.items():
            if isinstance(job_def, dict) and "runs-on" in job_def:
                assert "timeout-minutes" in job_def, (
                    f"{filename} job '{job_name}' must declare explicit timeout-minutes"
                )


def test_pr_workflows_have_job_permissions() -> None:
    """Ensure every runner job in PR workflows declares explicit least-privilege permissions."""
    for filename in PR_SETUP_WORKFLOW_FILES:
        path = WORKFLOWS_DIR / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        jobs = data.get("jobs", {})
        for job_name, job_def in jobs.items():
            if isinstance(job_def, dict) and "runs-on" in job_def:
                assert "permissions" in job_def, (
                    f"{filename} job '{job_name}' must declare explicit job-level permissions"
                )
                assert isinstance(job_def["permissions"], dict), (
                    f"{filename} job '{job_name}' permissions must be a mapping dictionary"
                )


def test_pr_workflows_pinned_actions() -> None:
    """Ensure all third-party GitHub Actions in PR workflows are pinned by 40-char commit SHA."""
    pattern = re.compile(r"^\s*(?:-\s+)?uses:\s+([^\s]+)", re.MULTILINE)
    for filename in PR_SETUP_WORKFLOW_FILES:
        path = WORKFLOWS_DIR / filename
        content = path.read_text(encoding="utf-8")
        for match in pattern.finditer(content):
            action_ref = match.group(1)
            # Local actions and docker images are skipped
            if action_ref.startswith("./") or action_ref.startswith("docker://"):
                continue
            assert "@" in action_ref, f"{filename} uses action without version pin: {action_ref}"
            _, ref = action_ref.split("@", 1)
            assert len(ref) == 40 and all(c in "0123456789abcdefABCDEF" for c in ref), (
                f"{filename} uses action not pinned to 40-character SHA: {action_ref}"
            )
