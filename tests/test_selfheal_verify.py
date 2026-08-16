"""Tests for the self-healing verification stage."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from sakthai.selfheal import verify
from sakthai.selfheal.models import FailureSignal
from sakthai.selfheal.verify import build_commands, default_runner, run_tests, targeted_selection

PYTEST_SIGNAL = FailureSignal(
    tool="pytest",
    error_type="AssertionError",
    message="boom",
    test_id="tests/test_math.py::test_divide",
)
RUFF_SIGNAL = FailureSignal(tool="ruff", error_type="F401", message="unused")


class _Recorder:
    """A command runner that records what it was asked to run."""

    def __init__(self, *returncodes: int) -> None:
        self.returncodes = list(returncodes) or [0]
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str], cwd: Path, timeout: float) -> tuple[int, str]:
        self.calls.append(tuple(command))
        code = self.returncodes.pop(0) if self.returncodes else 0
        return code, f"output for {' '.join(command)}"


def test_a_pytest_failure_is_targeted_by_node_id() -> None:
    assert targeted_selection(PYTEST_SIGNAL) == "tests/test_math.py::test_divide"


def test_a_lint_failure_has_no_targeted_selection() -> None:
    assert targeted_selection(RUFF_SIGNAL) is None


def test_a_pytest_signal_without_a_path_has_no_targeted_selection() -> None:
    assert targeted_selection(FailureSignal("pytest", "E", "m", test_id="test_bare")) is None


def test_commands_run_the_failing_test_first_then_the_whole_suite() -> None:
    commands = build_commands(PYTEST_SIGNAL)

    assert len(commands) == 2
    assert commands[0][-1] == "tests/test_math.py::test_divide"
    assert commands[1][-1] == "tests/"


def test_commands_for_a_lint_failure_are_the_full_suite_only() -> None:
    assert build_commands(RUFF_SIGNAL) == ((*verify.BASE_COMMAND, "tests/"),)


def test_commands_with_no_signal_are_the_full_suite_only() -> None:
    assert build_commands(None) == ((*verify.BASE_COMMAND, "tests/"),)


def test_integration_tests_are_excluded_the_same_way_ci_excludes_them() -> None:
    """The verification run must match the gate it is standing in for."""
    assert "-m" in verify.BASE_COMMAND
    assert verify.BASE_COMMAND[verify.BASE_COMMAND.index("-m") + 1] == "not integration"


def test_both_runs_must_pass(tmp_path: Path) -> None:
    runner = _Recorder(0, 0)

    outcome = run_tests(PYTEST_SIGNAL, tmp_path, runner=runner)

    assert outcome.passed is True
    assert len(runner.calls) == 2


def test_stops_at_the_first_failing_command(tmp_path: Path) -> None:
    runner = _Recorder(1, 0)

    outcome = run_tests(PYTEST_SIGNAL, tmp_path, runner=runner)

    assert outcome.passed is False
    assert outcome.returncode == 1
    assert len(runner.calls) == 1, "the full suite must not run after the targeted run failed"


def test_a_targeted_pass_followed_by_a_suite_failure_is_a_failure(tmp_path: Path) -> None:
    """Fixing the reported failure while breaking something else is still a failure."""
    runner = _Recorder(0, 1)

    outcome = run_tests(PYTEST_SIGNAL, tmp_path, runner=runner)

    assert outcome.passed is False
    assert outcome.command[-1] == "tests/"


def test_output_is_truncated_and_redacted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"

    def leaky(command: Sequence[str], cwd: Path, timeout: float) -> tuple[int, str]:
        return 1, ("x\n" * 10_000) + f"env: GITHUB_TOKEN={secret}\n"

    outcome = run_tests(PYTEST_SIGNAL, tmp_path, runner=leaky)

    assert secret not in outcome.output
    assert outcome.output.startswith("…(truncated)…")
    assert len(outcome.output) < 20_000


def test_default_runner_executes_a_real_command(tmp_path: Path) -> None:
    returncode, output = default_runner(["python", "-c", "print('hi')"], tmp_path, 30.0)

    assert returncode == 0
    assert "hi" in output


def test_default_runner_reports_a_missing_executable(tmp_path: Path) -> None:
    returncode, output = default_runner(["definitely-not-a-real-binary"], tmp_path, 30.0)

    assert returncode == 127
    assert "command not found" in output


def test_default_runner_reports_a_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def timing_out(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=1.0)

    monkeypatch.setattr(subprocess, "run", timing_out)

    returncode, output = default_runner(["pytest"], tmp_path, 1.0)

    assert returncode == 124
    assert "timed out" in output
