"""Tests for Marketplace Actions SHA pinning, concurrency, and security invariants."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.lint_workflow_permissions import find_scalar_permissions

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

PINNED_ACTIONS = {
    "devops-infra/action-pull-request": "e66e2ba93519dc63b9884a26e620e2fd0cffab2c",
    "devops-infra/action-commit-push": "be5ba37125c79eb0016cbd8cc385f0aa160538c5",
    "Andrew-Chen-Wang/github-wiki-action": "1bbb4280446f9630e8e21a18012cbacf3b0f992e",
    "connor-baer/action-sync-branch": "f5d20b6a6944c70909c187b558313dfc1d8daa48",
    "dineshsonachalam/markdown-autodocs": "6596b4a049f087c7abe84cc7457e2c53652df810",
    "Khan/pull-request-comment-trigger": "edab8d9ba7759221187ef7120592a6fbfada0d18",
    "chrnorm/deployment-action": "55729fcebec3d284f60f5bcabbd8376437d696b1",
}


def test_marketplace_workflows_exist_and_pinned() -> None:
    for action_name, expected_sha in PINNED_ACTIONS.items():
        found = False
        pattern = re.compile(rf"{re.escape(action_name)}@([a-f0-9]+)")
        for workflow_path in WORKFLOWS_DIR.glob("*.yml"):
            if workflow_path.name.endswith(".lock.yml"):
                continue
            content = workflow_path.read_text(encoding="utf-8")
            if action_name in content:
                found = True
                matches = pattern.findall(content)
                assert matches, f"{workflow_path.name} uses unpinned {action_name}"
                for sha in matches:
                    assert sha == expected_sha, (
                        f"{workflow_path.name} uses unexpected SHA {sha} for {action_name}"
                    )
        assert found, f"No active workflow found utilizing {action_name}"


MARKETPLACE_WORKFLOW_FILES = [
    "wiki-sync.yml",
    "pr-comment-trigger.yml",
    "autodocs.yml",
    "reusable-deployment.yml",
    "branch-sync.yml",
    "automated-pr-maintenance.yml",
]


def test_marketplace_workflows_have_concurrency_and_harden_runner() -> None:
    """Ensure all marketplace workflow files declare concurrency and harden-runner."""
    for filename in MARKETPLACE_WORKFLOW_FILES:
        workflow_path = WORKFLOWS_DIR / filename
        assert workflow_path.is_file(), f"{filename} does not exist"
        content = workflow_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        assert isinstance(data, dict), f"{filename} is not valid YAML"
        assert "concurrency" in data, f"{filename} is missing concurrency declaration"
        assert "step-security/harden-runner" in content, (
            f"{filename} is missing StepSecurity harden-runner"
        )


def test_marketplace_workflow_permissions_remain_strict_mappings() -> None:
    """Ensure no scalar permissions exist across any workflow file."""
    findings = find_scalar_permissions(WORKFLOWS_DIR)
    assert findings == [], f"Found scalar permissions: {findings}"
