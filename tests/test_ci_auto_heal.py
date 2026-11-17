from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import call, patch

_SCRIPT = Path(__file__).parents[1] / "scripts" / "ci_auto_heal.py"
_SPEC = spec_from_file_location("ci_auto_heal", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _result(returncode: int) -> CompletedProcess[str]:
    return CompletedProcess(args=[], returncode=returncode, stdout="", stderr="")


def test_dry_run_reports_commands_without_executing_them() -> None:
    with patch.object(_MODULE, "run_command") as run_command:
        output = StringIO()
        with redirect_stdout(output):
            assert _MODULE.heal_formatting(dry_run=True) is True

    run_command.assert_not_called()
    assert "Would run 'uv run ruff format .'" in output.getvalue()
    assert "uv run ruff check --fix ." in output.getvalue()


def test_heal_formatting_runs_format_then_fix_and_succeeds() -> None:
    with patch.object(_MODULE, "run_command", side_effect=[_result(0), _result(0)]) as run_command:
        assert _MODULE.heal_formatting() is True

    assert run_command.call_args_list == [
        call(["uv", "run", "ruff", "format", "."]),
        call(["uv", "run", "ruff", "check", "--fix", "."]),
    ]


def test_heal_formatting_reports_failure_when_either_step_fails() -> None:
    with patch.object(_MODULE, "run_command", side_effect=[_result(1), _result(0)]):
        assert _MODULE.heal_formatting() is False

    with patch.object(_MODULE, "run_command", side_effect=[_result(0), _result(1)]):
        assert _MODULE.heal_formatting() is False


def test_check_only_returns_zero_when_both_quality_checks_pass() -> None:
    with (
        patch.object(_MODULE, "run_command", side_effect=[_result(0), _result(0)]),
        patch.object(_MODULE.sys, "argv", ["ci_auto_heal.py", "--check-only"]),
    ):
        assert _MODULE.main() == 0


def test_check_only_returns_one_when_a_quality_check_fails() -> None:
    with (
        patch.object(_MODULE, "run_command", side_effect=[_result(0), _result(1)]),
        patch.object(_MODULE.sys, "argv", ["ci_auto_heal.py", "--check-only"]),
    ):
        assert _MODULE.main() == 1


def test_check_only_runs_format_check_before_lint_check() -> None:
    with (
        patch.object(_MODULE, "run_command", side_effect=[_result(0), _result(0)]) as run_command,
        patch.object(_MODULE.sys, "argv", ["ci_auto_heal.py", "--check-only"]),
    ):
        _MODULE.main()

    assert run_command.call_args_list == [
        call(["uv", "run", "ruff", "format", "--check", "."]),
        call(["uv", "run", "ruff", "check", "."]),
    ]
