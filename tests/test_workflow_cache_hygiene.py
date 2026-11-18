from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from scripts import lint_workflow_permissions
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
        if yml_path.name.endswith(".lock.yml") or yml_path.name == "agentic_commands.yml":
            continue
        with yml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            continue
        assert "concurrency" in data, f"{yml_path.name} is missing concurrency declaration"


def test_workflows_do_not_use_scalar_permissions() -> None:
    """Require workflow permissions to be explicit mappings."""
    assert find_scalar_permissions(WORKFLOWS_DIR) == []


@pytest.mark.parametrize("extension", [".yml", ".yaml"])
def test_workflow_permission_linter_catches_scalar_forms(tmp_path: Path, extension: str) -> None:
    """Detect scalar forms at any mapping depth, including quoted values."""
    workflow = tmp_path / f"sample{extension}"
    workflow.write_text(
        """name: sample
permissions: read
jobs:
  read-job:
    permissions: write
  read-all-job:
    permissions: "read-all"
  write-all-job:
    permissions: 'write-all'
  allowed-job:
    permissions: {}
""",
        encoding="utf-8",
    )

    findings = find_scalar_permissions(tmp_path)

    assert [(line, value) for _, line, value in findings] == [
        (2, "read"),
        (5, "write"),
        (7, "read-all"),
        (9, "write-all"),
    ]


def test_workflow_permission_linter_ignores_comments_and_block_scalars(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "sample.yaml"
    workflow.write_text(
        """name: sample
# permissions: read-all
run-name: |
  permissions: write
  permissions: "read-all"
permissions: {}
jobs: {}
""",
        encoding="utf-8",
    )

    assert find_scalar_permissions(tmp_path) == []


def test_workflow_permission_linter_cli_reports_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workflow = tmp_path / "sample.yml"
    workflow.write_text('permissions: "read-all"\n', encoding="utf-8")
    monkeypatch.setattr(lint_workflow_permissions, "WORKFLOWS_DIR", tmp_path)

    assert lint_workflow_permissions.main() == 1

    captured = capsys.readouterr()
    assert "Workflow permissions lint failed:" in captured.err
    assert f"{workflow}:1: permissions: read-all" in captured.err


def test_workflow_permission_linter_cli_passes_for_allowed_declarations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "sample.yaml").write_text(
        "permissions: {contents: read}\njobs: {}\n", encoding="utf-8"
    )
    monkeypatch.setattr(lint_workflow_permissions, "WORKFLOWS_DIR", tmp_path)

    assert lint_workflow_permissions.main() == 0
    assert "no scalar permission declarations found" in capsys.readouterr().out


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


def test_workflows_do_not_declare_top_level_write_permissions() -> None:
    """Ensure top-level workflow permissions never grant write access."""
    offenders: list[str] = []
    for yml_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        if yml_path.name.endswith(".lock.yml"):
            continue
        data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        top_perms = data.get("permissions")
        if isinstance(top_perms, dict):
            write_scopes = [k for k, v in top_perms.items() if v == "write"]
            if write_scopes:
                offenders.append(f"{yml_path.name}: {write_scopes}")
    assert offenders == [], (
        f"Workflows must scope write permissions to jobs, not top-level: {offenders}"
    )


def test_workflows_do_not_contain_unpinned_pip_or_npm_installs() -> None:
    """Ensure workflows do not run unpinned pip install or npm install commands."""
    unpinned_pip_re = re.compile(r"(?<!uv )(?:\bpython3?\s+-m\s+)?\bpip3?\s+install\b")
    unpinned_npm_re = re.compile(r"\bnpm\s+(?:install|i|update)\b")
    offenders: list[str] = []

    for yml_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        if yml_path.name.endswith(".lock.yml"):
            continue
        data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        for job_name, job_data in (data.get("jobs") or {}).items():
            if not isinstance(job_data, dict):
                continue
            for step in job_data.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                run_script = step.get("run")
                if not isinstance(run_script, str):
                    continue
                if unpinned_pip_re.search(run_script) and "--require-hashes" not in run_script:
                    offenders.append(f"{yml_path.name}:{job_name} (unpinned pip install)")
                if unpinned_npm_re.search(run_script):
                    offenders.append(f"{yml_path.name}:{job_name} (unpinned npm install)")

    assert offenders == [], f"Found unpinned workflow package installs: {offenders}"


def test_workflows_do_not_reference_secrets_context_in_if_conditions() -> None:
    """Ensure workflows do not reference secrets.<NAME> in job or step if: expressions."""
    secrets_ctx_re = re.compile(r"(?<![A-Za-z0-9_.-])secrets\.[A-Za-z0-9_]+\b")
    offenders: list[str] = []

    for yml_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        for job_name, job_data in (data.get("jobs") or {}).items():
            if not isinstance(job_data, dict):
                continue
            job_if = str(job_data.get("if", ""))
            if secrets_ctx_re.search(job_if):
                offenders.append(f"{yml_path.name}:{job_name} (job if)")
            for step in job_data.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                step_if = str(step.get("if", ""))
                if secrets_ctx_re.search(step_if):
                    step_name = step.get("name", "<unnamed>")
                    offenders.append(f"{yml_path.name}:{job_name}:{step_name} (step if)")

    assert offenders == [], f"Found invalid secrets.* references in if: conditions: {offenders}"


def test_package_json_and_lockfiles_are_valid_json_and_overrides_consistent() -> None:
    """Ensure all tracked npm manifests and lockfiles parse cleanly and avoid conflicting overrides."""
    manifest_dirs = [
        REPO_ROOT / "apps" / "sak_agent_dashboard",
        REPO_ROOT / "personas" / "saksee" / "skills" / "SakSee-stitch-react-components",
    ]
    for pkg_dir in manifest_dirs:
        pkg_json_path = pkg_dir / "package.json"
        lock_json_path = pkg_dir / "package-lock.json"
        assert pkg_json_path.is_file(), f"Missing {pkg_json_path}"
        assert lock_json_path.is_file(), f"Missing {lock_json_path}"

        pkg_data = json.loads(pkg_json_path.read_text(encoding="utf-8"))
        lock_data = json.loads(lock_json_path.read_text(encoding="utf-8"))
        assert isinstance(pkg_data, dict)
        assert isinstance(lock_data, dict)

        direct_deps = {
            *(pkg_data.get("dependencies") or {}).keys(),
            *(pkg_data.get("devDependencies") or {}).keys(),
        }
        for override_key, override_val in (pkg_data.get("overrides") or {}).items():
            if override_key in direct_deps and isinstance(override_val, str):
                assert override_val == f"${override_key}", (
                    f"{pkg_json_path}: override for direct dependency '{override_key}' "
                    f"must use '${override_key}' reference to avoid Dependabot conflicts"
                )


def test_dependabot_config_avoids_known_update_failures() -> None:
    """Verify .github/dependabot.yml avoids wildcard github-actions groups and ignores incompatible tenacity."""
    dependabot_path = REPO_ROOT / ".github" / "dependabot.yml"
    data = yaml.safe_load(dependabot_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    updates = data.get("updates") or []

    uv_entry = next((u for u in updates if u.get("package-ecosystem") == "uv"), None)
    assert uv_entry is not None, "Missing uv ecosystem in dependabot.yml"
    uv_ignores = uv_entry.get("ignore") or []
    assert any(item.get("dependency-name") == "tenacity" for item in uv_ignores), (
        "uv dependabot config must ignore incompatible tenacity >= 9.2.0"
    )

    gha_entry = next(
        (u for u in updates if u.get("package-ecosystem") == "github-actions"),
        None,
    )
    assert gha_entry is not None, "Missing github-actions ecosystem in dependabot.yml"
    for group_cfg in (gha_entry.get("groups") or {}).values():
        if isinstance(group_cfg, dict):
            assert "*" not in (group_cfg.get("patterns") or []), (
                "github-actions dependabot config must not group '*' across all workflows (causes 55m timeout)"
            )


def test_gitattributes_and_scorecard_lockfile_hygiene() -> None:
    """Ensure generated workflow lockfiles are marked export-ignore to prevent Scorecard noise."""
    gitattributes_path = REPO_ROOT / ".gitattributes"
    assert gitattributes_path.is_file(), ".gitattributes must exist"
    content = gitattributes_path.read_text(encoding="utf-8")
    assert ".github/workflows/*.lock.yml" in content, "Must configure lock.yml in .gitattributes"
    lines = [line for line in content.splitlines() if ".github/workflows/*.lock.yml" in line]
    assert lines, "Must find lock.yml line in .gitattributes"
    lock_line = lines[0]
    assert "export-ignore" in lock_line, "Lockfiles must be marked export-ignore"
    assert "linguist-generated=true" in lock_line, "Lockfiles must be marked linguist-generated"

    scorecard_path = WORKFLOWS_DIR / "scorecard.yml"
    assert scorecard_path.is_file(), "scorecard.yml must exist"
    scorecard_data = yaml.safe_load(scorecard_path.read_text(encoding="utf-8"))
    on_clause = scorecard_data.get("on") or scorecard_data.get(True)
    assert "workflow_dispatch" in on_clause, "scorecard.yml must support manual workflow_dispatch"
