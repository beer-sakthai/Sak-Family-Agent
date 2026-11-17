"""Tests for manual workflow approval gate integration, SHA pinning, and permissions."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.lint_workflow_permissions import find_scalar_permissions

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

PINNED_MANUAL_APPROVAL_SHA = "fa642940caf8412403569b28b2db4a1df08a83a3"
ACTION_NAME = "trstringer/manual-approval"


def test_manual_workflow_approval_gate_pinned() -> None:
    manual_yml = WORKFLOWS_DIR / "manual.yml"
    assert manual_yml.is_file(), "manual.yml does not exist"
    content = manual_yml.read_text(encoding="utf-8")

    expected_ref = f"{ACTION_NAME}@{PINNED_MANUAL_APPROVAL_SHA}"
    assert expected_ref in content, (
        f"manual.yml must pin {ACTION_NAME} to {PINNED_MANUAL_APPROVAL_SHA}"
    )
    assert "step-security/harden-runner" in content, "manual.yml must include harden-runner"

    data = yaml.safe_load(content)
    assert "concurrency" in data, "manual.yml must declare concurrency"
    assert "approval-gate" in data.get("jobs", {}), "manual.yml must define approval-gate job"


def test_reusable_manual_approval_gate_valid() -> None:
    reusable_yml = WORKFLOWS_DIR / "reusable-manual-approval-gate.yml"
    assert reusable_yml.is_file(), "reusable-manual-approval-gate.yml does not exist"
    content = reusable_yml.read_text(encoding="utf-8")

    expected_ref = f"{ACTION_NAME}@{PINNED_MANUAL_APPROVAL_SHA}"
    assert expected_ref in content, f"reusable-manual-approval-gate.yml must pin {ACTION_NAME}"
    assert "step-security/harden-runner" in content, "reusable gate must include harden-runner"

    data = yaml.safe_load(content)
    on_clause = data.get("on") or data.get(True) or {}
    assert "workflow_call" in on_clause, "reusable gate must support workflow_call"
    job = data.get("jobs", {}).get("gate", {})
    assert job.get("permissions", {}).get("issues") == "write"


def test_no_unpinned_manual_approval_in_any_workflow() -> None:
    """Ensure trstringer/manual-approval is always pinned by full 40-char SHA."""
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
    """Ensure no scalar permissions are introduced."""
    findings = find_scalar_permissions(WORKFLOWS_DIR)
    assert findings == [], f"Found scalar permissions: {findings}"
