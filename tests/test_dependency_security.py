"""Tests for GitHub Dependency Security Architecture & Configuration.

Validates that .github/dependency-review-config.yml, .github/workflows/dependency-review.yml,
and docs/manage-your-dependency-security.md conform to supply chain security invariants.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
GITHUB_DIR = REPO_ROOT / ".github"
WORKFLOWS_DIR = GITHUB_DIR / "workflows"
DOCS_DIR = REPO_ROOT / "docs"

CONFIG_FILE = GITHUB_DIR / "dependency-review-config.yml"
WORKFLOW_FILE = WORKFLOWS_DIR / "dependency-review.yml"
GUIDE_FILE = DOCS_DIR / "manage-your-dependency-security.md"


def test_dependency_review_config_exists_and_is_valid_yaml() -> None:
    """Verify that .github/dependency-review-config.yml exists and has required keys."""
    assert CONFIG_FILE.is_file(), f"{CONFIG_FILE} does not exist"
    data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{CONFIG_FILE} did not parse into a dictionary"

    # Severity threshold
    assert data.get("fail-on-severity") == "high"

    # Scopes
    scopes = data.get("fail-on-scopes")
    assert isinstance(scopes, list)
    assert "runtime" in scopes
    assert "development" in scopes

    # License allowlist
    licenses = data.get("allow-licenses")
    assert isinstance(licenses, list)
    assert len(licenses) >= 10
    for expected_license in ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]:
        assert expected_license in licenses

    # Exempted GHSAs
    ghsas = data.get("allow-ghsas")
    assert isinstance(ghsas, list)
    assert "GHSA-fc5q-39xc-vjpf" in ghsas


def test_dependency_review_workflow_references_config_file() -> None:
    """Ensure the workflow delegates policy to .github/dependency-review-config.yml."""
    assert WORKFLOW_FILE.is_file(), f"{WORKFLOW_FILE} does not exist"
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    assert isinstance(data, dict)
    assert "concurrency" in data

    # Check the step
    jobs = data.get("jobs", {})
    review_job = jobs.get("dependency-review", {})
    steps = review_job.get("steps", [])

    review_steps = [
        step
        for step in steps
        if "dependency-review-action" in str(step.get("uses", ""))
    ]
    assert len(review_steps) == 1, "Expected exactly 1 dependency review step"
    with_args = review_steps[0].get("with", {})
    assert with_args.get("config-file") == "./.github/dependency-review-config.yml"
    assert with_args.get("comment-summary-in-pr") == "on-failure"


def test_dependency_security_guide_document_exists_and_covers_framework() -> None:
    """Ensure docs/manage-your-dependency-security.md exists and covers all core components."""
    assert GUIDE_FILE.is_file(), f"{GUIDE_FILE} does not exist"
    content = GUIDE_FILE.read_text(encoding="utf-8")

    assert "Managing Dependency Security in Sak-Family-Agent" in content
    assert "https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security" in content
    assert "dependency-review-config.yml" in content
    assert "dependabot.yml" in content
    assert "GHSA-fc5q-39xc-vjpf" in content
    assert "SPDX" in content
    assert "fail-on-severity" in content
