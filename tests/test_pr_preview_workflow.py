"""Tests for Pull Request Preview workflow, SHA pinning, and permissions."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.lint_workflow_permissions import find_scalar_permissions

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

PINNED_PR_PREVIEW_SHA = "873417d2df72380da1f3978378fb58560bcde976"
ACTION_NAME = "rossjrw/pr-preview-action"


def test_pr_preview_workflow_pinned_and_valid() -> None:
    preview_yml = WORKFLOWS_DIR / "pr-preview.yml"
    assert preview_yml.is_file(), "pr-preview.yml does not exist"
    content = preview_yml.read_text(encoding="utf-8")

    expected_ref = f"{ACTION_NAME}@{PINNED_PR_PREVIEW_SHA}"
    assert expected_ref in content, (
        f"pr-preview.yml must pin {ACTION_NAME} to {PINNED_PR_PREVIEW_SHA}"
    )
    assert "step-security/harden-runner" in content, "pr-preview.yml must include harden-runner"

    data = yaml.safe_load(content)
    assert "concurrency" in data, "pr-preview.yml must declare concurrency"

    on_clause = data.get("on") or data.get(True) or {}
    assert "pull_request" in on_clause, "pr-preview.yml must trigger on pull_request"

    perms = data.get("permissions", {})
    assert perms.get("contents") == "write"
    assert perms.get("pull-requests") == "write"


def test_no_unpinned_pr_preview_in_any_workflow() -> None:
    """Ensure rossjrw/pr-preview-action is always pinned by full 40-char SHA."""
    pattern = re.compile(rf"{re.escape(ACTION_NAME)}@([a-f0-9]+)")
    for workflow_path in WORKFLOWS_DIR.glob("*.yml"):
        if workflow_path.name.endswith(".lock.yml"):
            continue
        content = workflow_path.read_text(encoding="utf-8")
        if ACTION_NAME in content:
            matches = pattern.findall(content)
            assert matches, f"{workflow_path.name} uses unpinned {ACTION_NAME}"
            for sha in matches:
                assert len(sha) == 40, f"{workflow_path.name} uses short/invalid SHA: {sha}"


def test_workflow_permissions_remain_strict_mappings() -> None:
    """Ensure no scalar permissions are introduced across all workflows."""
    findings = find_scalar_permissions(WORKFLOWS_DIR)
    assert findings == [], f"Found scalar permissions: {findings}"
