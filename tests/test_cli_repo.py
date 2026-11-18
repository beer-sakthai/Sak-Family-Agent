"""Tests for `sakthai repo` commands and the task registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.cli._runner import resolve_repo_cwd, run_repo_argv
from sakthai.cli.repo_registry import (
    AREAS,
    TASKS,
    RepoTask,
    get_repo_coverage_map,
    get_task,
    list_tasks,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_registry_invariants() -> None:
    """Verify registry invariants: uniqueness, valid areas, and file paths on disk."""
    names = set()
    for task in TASKS:
        assert task.name not in names, f"Duplicate task name: {task.name}"
        names.add(task.name)
        assert task.area in AREAS, f"Task {task.name} has invalid area {task.area}"
        assert task.argv, f"Task {task.name} has empty argv"
        assert task.check_target_file(), (
            f"Target file missing for task {task.name}: {task.file_path}"
        )
        assert isinstance(task.check_requirements(), list)


def test_repo_registry_helpers() -> None:
    assert get_task("diagnose-personas") is not None
    assert get_task("nonexistent-task-12345") is None

    eval_tasks = list_tasks(area="eval")
    assert all(t.area == "eval" for t in eval_tasks)
    assert len(eval_tasks) >= 3

    all_tasks = list_tasks()
    assert len(all_tasks) == len(TASKS)

    cov_map = get_repo_coverage_map()
    assert set(cov_map.keys()) == set(AREAS.keys())
    assert cov_map["eval"]["task_count"] >= 3


def test_repo_map_text_and_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["repo", "map"])
    assert result.exit_code == 0
    assert "Repository Coverage Map" in result.output
    assert "scripts" in result.output

    result_json = runner.invoke(main, ["repo", "map", "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.output)
    assert "scripts" in data
    assert "training" in data


def test_repo_list_text_and_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["repo", "list"])
    assert result.exit_code == 0
    assert "diagnose-personas" in result.output

    result_filtered = runner.invoke(main, ["repo", "list", "--area", "eval"])
    assert result_filtered.exit_code == 0
    assert "eval-bench" in result_filtered.output

    result_json = runner.invoke(main, ["repo", "list", "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.output)
    assert isinstance(data, list)
    assert any(item["name"] == "diagnose-personas" for item in data)


def test_repo_run_dry_run(runner: CliRunner) -> None:
    result = runner.invoke(main, ["repo", "run", "diagnose-personas", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "scripts/diagnose_personas.py" in result.output


def test_repo_run_unknown_task(runner: CliRunner) -> None:
    result = runner.invoke(main, ["repo", "run", "unknown-task-xyz"])
    assert result.exit_code != 0
    assert "Unknown repo task 'unknown-task-xyz'" in result.output


def test_repo_run_missing_requirement(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    task = get_task("diagnose-personas")
    assert task is not None
    fake_task = RepoTask(
        name="test-fake-missing-tool",
        area="scripts",
        summary="Test",
        argv=("test-missing-tool-exe",),
        requires=("test-missing-tool-exe",),
    )
    import sakthai.cli.repo as repo_mod

    monkeypatch.setattr(
        repo_mod, "get_task", lambda name: fake_task if name == "test-fake" else None
    )
    result = runner.invoke(main, ["repo", "run", "test-fake"])
    assert result.exit_code != 0
    assert "requires tools not found on PATH" in result.output


def test_repo_run_missing_target_file(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    fake_task = RepoTask(
        name="test-fake-missing-file",
        area="scripts",
        summary="Test",
        argv=("uv", "run", "python", "nonexistent/file.py"),
        file_path="nonexistent/file.py",
        requires=(),
    )
    import sakthai.cli.repo as repo_mod

    monkeypatch.setattr(
        repo_mod, "get_task", lambda name: fake_task if name == "test-fake" else None
    )
    result = runner.invoke(main, ["repo", "run", "test-fake"])
    assert result.exit_code != 0
    assert "does not exist on disk" in result.output


def test_repo_run_executes_argv_and_returns_code(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    called_argv: list[list[str]] = []

    def _fake_run(argv: Any, **kwargs: Any) -> int:
        called_argv.append(list(argv))
        return 42

    import sakthai.cli.repo as repo_mod

    monkeypatch.setattr(repo_mod, "run_repo_argv", _fake_run)
    result = runner.invoke(main, ["repo", "run", "diagnose-personas", "--", "--verbose"])
    assert result.exit_code == 42
    assert len(called_argv) == 1
    assert "--verbose" in called_argv[0]


def test_runner_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cwd = resolve_repo_cwd("scripts")
    assert cwd.is_dir()
    assert cwd.name == "scripts"

    assert resolve_repo_cwd(None).is_dir()
    assert resolve_repo_cwd(tmp_path) == tmp_path
    assert resolve_repo_cwd(str(tmp_path)) == tmp_path

    no_file_task = RepoTask(
        name="no-file", area="scripts", summary="test", argv=("true",), file_path=None
    )
    assert no_file_task.check_target_file() is True

    with pytest.raises(ValueError, match="cannot be empty"):
        run_repo_argv([])

    assert run_repo_argv(["echo", "hello"], dry_run=True, echo=False) == 0

    import subprocess

    def _mock_run(argv: Any, **kwargs: Any) -> Any:
        class _Proc:
            returncode = 7

        return _Proc()

    monkeypatch.setattr(subprocess, "run", _mock_run)
    assert run_repo_argv(["python3", "-c", "pass"], extra_env={"TEST_VAR": "1"}) == 7
    assert run_repo_argv(["python3", "-c", "pass"], echo=False) == 7
