"""Tests for sakthai.sandbox — Docker sandbox wrapper."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.sandbox import SANDBOX_IMAGE, SandboxError, build_image, run_in_sandbox


def test_build_image_raises_when_docker_missing() -> None:
    with (
        patch("sakthai.sandbox.shutil.which", return_value=None),
        pytest.raises(SandboxError, match="Docker is not installed"),
    ):
        build_image()


def test_run_in_sandbox_raises_when_docker_missing() -> None:
    with (
        patch("sakthai.sandbox.shutil.which", return_value=None),
        pytest.raises(SandboxError, match="Docker is not installed"),
    ):
        run_in_sandbox(
            "hi",
            model="m",
            max_tokens=100,
            max_iterations=3,
            max_seconds=None,
            verbose=False,
        )


def _mock_docker_run(returncode: int = 0, stderr: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stderr = stderr
    return result


def test_build_image_success() -> None:
    with (
        patch("sakthai.sandbox.shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run", return_value=_mock_docker_run(0)) as mock_run,
    ):
        build_image()
    args = mock_run.call_args[0][0]
    assert "build" in args
    assert SANDBOX_IMAGE in args


def test_build_image_raises_on_nonzero_exit() -> None:
    with (
        patch("sakthai.sandbox.shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run", return_value=_mock_docker_run(1, "build error")),
        pytest.raises(SandboxError, match="Docker build failed"),
    ):
        build_image()


def test_build_image_force_passes_no_cache() -> None:
    with (
        patch("sakthai.sandbox.shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run", return_value=_mock_docker_run(0)) as mock_run,
    ):
        build_image(force=True)
    args = mock_run.call_args[0][0]
    assert "--no-cache" in args


def _run_sandbox(tmp_path: Path, extra_kwargs: dict | None = None) -> MagicMock:
    kwargs = dict(
        model="claude-test",
        max_tokens=256,
        max_iterations=3,
        max_seconds=None,
        verbose=False,
    )
    if extra_kwargs:
        kwargs.update(extra_kwargs)

    build_result = _mock_docker_run(0)
    run_result = _mock_docker_run(0)

    with (
        patch("sakthai.sandbox.shutil.which", return_value="/usr/bin/docker"),
        patch("sakthai.sandbox.memory_db_path", return_value=tmp_path / "memory.db"),
        patch("subprocess.run", side_effect=[build_result, run_result]) as mock_run,
    ):
        run_in_sandbox("do something", **kwargs)
    return mock_run


def test_run_in_sandbox_passes_task(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path)
    docker_cmd = mock.call_args_list[1][0][0]
    assert "do something" in docker_cmd


def test_run_in_sandbox_passes_api_keys_via_e_flag(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path)
    docker_cmd = mock.call_args_list[1][0][0]
    assert "ANTHROPIC_API_KEY" in docker_cmd
    assert "GEMINI_API_KEY" in docker_cmd
    assert "OPENAI_API_KEY" in docker_cmd


def test_run_in_sandbox_sets_shell_allow(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path)
    docker_cmd = mock.call_args_list[1][0][0]
    assert any("SAKTHAI_SHELL_ALLOW=1" in str(a) for a in docker_cmd)


def test_run_in_sandbox_mounts_memory_db(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path)
    docker_cmd = mock.call_args_list[1][0][0]
    assert any("/root/.sakthai/memory.db" in str(a) for a in docker_cmd)


def test_run_in_sandbox_includes_resource_limits(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path)
    docker_cmd = mock.call_args_list[1][0][0]
    assert "--memory" in docker_cmd
    assert "--cpus" in docker_cmd
    assert "--security-opt" in docker_cmd


def test_run_in_sandbox_passes_max_seconds(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path, {"max_seconds": 60.0})
    docker_cmd = mock.call_args_list[1][0][0]
    assert "--max-seconds" in docker_cmd
    assert "60.0" in docker_cmd


def test_run_in_sandbox_passes_verbose(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path, {"verbose": True})
    docker_cmd = mock.call_args_list[1][0][0]
    assert "-v" in docker_cmd


def test_run_in_sandbox_passes_new_v2_options(tmp_path: Path) -> None:
    mock = _run_sandbox(
        tmp_path,
        {
            "no_mcp": True,
            "with_skills": ("test-skill",),
            "fast": True,
            "caveman": "lite",
            "dry_run": True,
            "stream": True,
        },
    )
    docker_cmd = mock.call_args_list[1][0][0]
    assert "--no-mcp" in docker_cmd
    assert "--with-skills" in docker_cmd
    assert "test-skill" in docker_cmd
    assert "--fast" in docker_cmd
    assert "--caveman" in docker_cmd
    assert "lite" in docker_cmd
    assert "--dry-run" in docker_cmd
    assert "--stream" in docker_cmd


def test_run_in_sandbox_creates_memory_db_if_missing(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    assert not db.exists()
    _run_sandbox(tmp_path)
    assert db.exists()


def test_run_in_sandbox_returns_container_exit_code(tmp_path: Path) -> None:
    build_result = _mock_docker_run(0)
    run_result = _mock_docker_run(42)
    with (
        patch("sakthai.sandbox.shutil.which", return_value="/usr/bin/docker"),
        patch("sakthai.sandbox.memory_db_path", return_value=tmp_path / "memory.db"),
        patch("subprocess.run", side_effect=[build_result, run_result]),
    ):
        code = run_in_sandbox(
            "fail",
            model="m",
            max_tokens=100,
            max_iterations=3,
            max_seconds=None,
            verbose=False,
        )
    assert code == 42


def test_run_in_sandbox_passes_provider(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path, {"provider": "gemini"})
    docker_cmd = mock.call_args_list[1][0][0]
    assert "--provider" in docker_cmd
    assert "gemini" in docker_cmd


def test_run_in_sandbox_passes_stateless(tmp_path: Path) -> None:
    mock = _run_sandbox(tmp_path, {"stateless": True})
    docker_cmd = mock.call_args_list[1][0][0]
    assert "--stateless" in docker_cmd


def test_cli_sandbox_flag_triggers_sandbox(tmp_path: Path) -> None:
    with (
        patch("sakthai.sandbox.shutil.which", return_value="/usr/bin/docker"),
        patch("sakthai.sandbox.memory_db_path", return_value=tmp_path / "memory.db"),
        patch("subprocess.run", side_effect=[_mock_docker_run(0), _mock_docker_run(0)]),
    ):
        r = CliRunner().invoke(main, ["run", "--sandbox", "hello"])
    assert r.exit_code == 0


def test_cli_sandbox_flag_shows_error_when_docker_missing() -> None:
    with patch("sakthai.sandbox.shutil.which", return_value=None):
        r = CliRunner().invoke(main, ["run", "--sandbox", "hello"])
    assert r.exit_code != 0
    assert "Docker" in r.output
