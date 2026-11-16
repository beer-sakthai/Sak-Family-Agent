from __future__ import annotations

from pathlib import Path

import yaml

from scripts.lint_workflow_permissions import find_scalar_permissions

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def test_cache_cleanup_workflow_exists_and_valid() -> None:
    cleanup_file = WORKFLOWS_DIR / "cache-cleanup.yml"
    assert cleanup_file.is_file(), "cache-cleanup.yml must exist"

    with cleanup_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data is not None
    assert "name" in data
    # Check trigger on pull_request closed
    on_clause = data.get("on") or data.get(True)  # yaml may parse 'on' as boolean
    assert on_clause is not None
    assert "pull_request" in on_clause
    assert "types" in on_clause["pull_request"]
    assert "closed" in on_clause["pull_request"]["types"]

    # Check permissions (either top-level or job-level grants actions: write)
    perms = data.get("permissions")
    job_perms = data.get("jobs", {}).get("cleanup-cache", {}).get("permissions", {})
    actions_perm = (
        perms.get("actions")
        if isinstance(perms, dict) and perms.get("actions") is not None
        else job_perms.get("actions")
    )
    assert actions_perm == "write"

    # Check concurrency
    assert "concurrency" in data


def test_no_redundant_actions_cache_on_uv_dir() -> None:
    """Ensure no workflow combines setup-uv with manual actions/cache on ~/.cache/uv."""
    for yml_path in WORKFLOWS_DIR.glob("*.yml"):
        if yml_path.name.endswith(".lock.yml"):
            continue
        content = yml_path.read_text(encoding="utf-8")
        if "astral-sh/setup-uv" in content:
            assert "~/.cache/uv" not in content, (
                f"{yml_path.name} uses astral-sh/setup-uv and manual ~/.cache/uv cache. "
                "Remove redundant actions/cache step."
            )


def test_all_active_workflows_have_concurrency() -> None:
    """Ensure all active top-level workflow files define concurrency."""
    for yml_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        if yml_path.name.endswith(".lock.yml"):
            continue
        with yml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            continue
        assert "concurrency" in data, f"{yml_path.name} is missing concurrency declaration"


def test_workflows_do_not_use_scalar_permissions() -> None:
    """Require workflow permissions to be explicit mappings, not read-all shorthands."""
    forbidden = ("permissions: read-all", "permissions: write-all")
    for yml_path in WORKFLOWS_DIR.glob("*.yml"):
        content = yml_path.read_text(encoding="utf-8")
        for declaration in forbidden:
            assert declaration not in content, (
                f"{yml_path.name} uses scalar {declaration}; declare least-privilege "
                "permissions as a mapping instead"
            )


def test_workflow_permission_linter_catches_scalar_forms(tmp_path: Path) -> None:
    """Cover all forbidden scalar forms, including declarations not used today."""
    workflow = tmp_path / "sample.yml"
    workflow.write_text(
        "permissions: read\npermissions: write\npermissions: read-all\npermissions: {}\n",
        encoding="utf-8",
    )

    findings = find_scalar_permissions(tmp_path)

    assert [(line, value) for _, line, value in findings] == [
        (1, "read"),
        (2, "write"),
        (3, "read-all"),
    ]
