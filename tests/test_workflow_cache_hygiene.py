from __future__ import annotations

from pathlib import Path

import yaml

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
    actions_perm = perms.get("actions") if isinstance(perms, dict) else job_perms.get("actions")
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


def test_root_uv_workflows_use_locked_execution() -> None:
    """Prevent CI from silently rewriting or relocking the root environment."""
    root_uv_workflows = {
        "ci.yml",
        "continuous-security.yml",
        "huggingface-integration.yml",
        "pylint.yml",
        "repository-security-quality.yml",
        "run-evals.yml",
        "sak-family-agent-contract.yml",
        "subprojects.yml",
        "verify-assets.yml",
    }

    for workflow_name in root_uv_workflows:
        content = (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        commands = [
            line.strip() for line in content.splitlines() if not line.lstrip().startswith("#")
        ]
        uv_commands = [line for line in commands if "uv sync" in line or "uv run" in line]
        assert uv_commands, f"{workflow_name} should contain uv commands"
        assert all("--locked" in line for line in uv_commands), (
            f"{workflow_name} must use --locked for every uv sync/run command"
        )
