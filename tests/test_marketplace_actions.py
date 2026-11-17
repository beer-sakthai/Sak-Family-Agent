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
    "bakunyo/git-pr-release-action": "035b7151a53745c03b85c6274ab1ae4bc734eccd",
    "hngprojects/pr-deploy": "2f8b3e0dce07f0c6f7e6e80018dc52081a61b63b",
    "benchmark-action/github-action-benchmark": "4322e5726e6334590d251fc4f92bec0efafc45dc",
    "ghalactic/github-release-from-tag": "30770b91acccc8e1e2f14562d813cb30af08f1c6",
    "jamesgeorge007/github-activity-readme": "4aefbfa1c222d70537dc6a02f0519266aab2b1ea",
    "renovatebot/github-action": "acdd6bda8b035c99ce59d5675816af2aa65a1774",
    "wearerequired/lint-action": "124229c6e2974984ba137c67a499ba28bfc33e33",
    "actions/create-github-app-token": "64ab729a6294000f5aa4a4bc0b73d1f32bc45510",
    "fastify/github-action-merge-dependabot": "73ec4cbb5e56df5591eae286972d5b2201ffe90f",
    "seferov/pr-lint-action": "cbef81c153f36262fbcd92fe97d6c6b8736d891d",
    "Optimal-AI/PR-Label-Checker": "48d46fe6336aedcbb836ca580e86f195f9d14b01",
    "trstringer/manual-approval": "fa642940caf8412403569b28b2db4a1df08a83a3",
    "stepci/stepci": "570a42a52dcb9c7864031da79b047ffbaa268847",
    "benc-uk/workflow-dispatch": "d004979be141727c7a17c28f603e2facc40d0855",
    "BetaHuhn/repo-file-sync-action": "8b92be3375cf1d1b0cd579af488a9255572e4619",
    "convictional/trigger-workflow-and-wait": "f69fa9eedd3c62a599220f4d5745230e237904be",
    "technote-space/workflow-conclusion-action": "45ce8e0eb155657ab8ccf346ade734257fd196a5",
    "saadmk11/github-actions-version-updater": "764bee6cd2905c6c91624f35332f1472fa736c23",
    "rokibhasansagar/slimhub_actions": "5560c2d964bc240edfc5a0855b4b2c8261a29f29",
    "the-actions-org/workflow-dispatch": "3133c5d135c7dbe4be4f9793872b6ef331b53bc7",
    "ahmadnassri/action-workflow-queue": "542658b3a8270cac81ae15d401b0d974732808ac",
    "varunsridharan/action-github-workflow-sync": "3c60cce5ee8e615a7c68ac75fc14893dcac62d49",
    "technote-space/auto-cancel-redundant-workflow": "7d35aba30420fc2368f8aeed50371e99e7fa3239",
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
    "git-pr-release.yml",
    "reusable-pr-deploy.yml",
    "continuous-benchmark.yml",
    "release-from-tag.yml",
    "activity-readme.yml",
    "renovate.yml",
    "lint-check.yml",
    "reusable-app-token.yml",
    "dependabot-auto-merge.yml",
    "pr-lint.yml",
    "pr-label-checker.yml",
    "reusable-manual-approval-gate.yml",
    "step-ci.yml",
    "actions-version-updater.yml",
    "runner-disk-cleaner.yml",
    "workflow-queue.yml",
    "workflow-conclusion.yml",
    "auto-cancel-redundant.yml",
    "reusable-workflow-dispatch.yml",
    "reusable-workflow-dispatch-wait.yml",
    "reusable-trigger-workflow-wait.yml",
    "repo-file-sync.yml",
    "github-workflow-sync.yml",
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
