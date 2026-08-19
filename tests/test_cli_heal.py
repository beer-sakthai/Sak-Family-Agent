"""Tests for ``sakthai heal``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import heal as heal_module
from sakthai.cli import main
from sakthai.selfheal.models import Diagnosis, FailureSignal, HealingOutcome, HealStatus

FAILING_LOG = """\
=================================== FAILURES ===================================
_________________________________ test_divide __________________________________
tests/test_math.py:12: in test_divide
    result = divide(1, 0)
E   ZeroDivisionError: division by zero
=========================== short test summary info ============================
FAILED tests/test_math.py::test_divide - ZeroDivisionError: division by zero
"""


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    path = tmp_path / "ci.log"
    path.write_text(FAILING_LOG, encoding="utf-8")
    return path


def test_heal_is_registered_on_the_cli(runner: CliRunner) -> None:
    result = runner.invoke(main, ["heal", "--help"])

    assert result.exit_code == 0
    assert "inspect" in result.output
    assert "run" in result.output


# -- inspect -------------------------------------------------------------


def test_inspect_lists_the_failures_and_their_frames(runner: CliRunner, log_file: Path) -> None:
    result = runner.invoke(main, ["heal", "inspect", "--log", str(log_file)])

    assert result.exit_code == 0
    assert "1 failure(s)" in result.output
    assert "ZeroDivisionError" in result.output
    assert "tests/test_math.py:12 in test_divide" in result.output


def test_inspect_emits_json(runner: CliRunner, log_file: Path) -> None:
    result = runner.invoke(main, ["heal", "inspect", "--log", str(log_file), "--json"])

    payload = json.loads(result.output)
    assert payload[0]["error_type"] == "ZeroDivisionError"
    assert payload[0]["frames"][0]["path"] == "tests/test_math.py"


def test_inspect_says_so_when_a_log_is_clean(runner: CliRunner, tmp_path: Path) -> None:
    clean = tmp_path / "clean.log"
    clean.write_text("42 passed\n", encoding="utf-8")

    result = runner.invoke(main, ["heal", "inspect", "--log", str(clean)])

    assert "no recognised failure" in result.output


def test_inspect_reads_stdin(runner: CliRunner) -> None:
    result = runner.invoke(main, ["heal", "inspect", "--log", "-"], input=FAILING_LOG)

    assert result.exit_code == 0
    assert "ZeroDivisionError" in result.output


def test_inspect_makes_no_model_call(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hermetic half must stay hermetic — no credentials, no network."""

    def explode(**kwargs: object) -> object:
        raise AssertionError("inspect must not build a model client")

    monkeypatch.setattr(heal_module, "build_completion", explode)

    assert runner.invoke(main, ["heal", "inspect", "--log", str(log_file)]).exit_code == 0


def test_an_unreadable_log_is_a_clean_cli_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["heal", "inspect", "--log", str(tmp_path / "missing.log")])

    assert result.exit_code != 0
    assert "cannot read log" in result.output


# -- run -----------------------------------------------------------------


def _stub_completions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(heal_module, "build_completion", lambda **kwargs: lambda s, u: "{}")


def _stub_heal(monkeypatch: pytest.MonkeyPatch, outcome: HealingOutcome) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_heal(log_text: str, config: object, **kwargs: object) -> HealingOutcome:
        captured["log_text"] = log_text
        captured["config"] = config
        captured.update(kwargs)
        return outcome

    monkeypatch.setattr(heal_module, "run_heal", fake_heal)
    return captured


PUBLISHED = HealingOutcome(
    status=HealStatus.PUBLISHED,
    detail="fix pushed to selfheal/fix-thing",
    signal=FailureSignal("pytest", "ZeroDivisionError", "division by zero"),
    diagnosis=Diagnosis(summary="s", root_cause="r", confidence=0.9),
    branch="selfheal/fix-thing",
    pull_request_url="https://github.com/o/r/pull/3",
    report="# report body",
    changed_files=("sakthai/calc.py",),
)


def test_run_reports_the_outcome(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    _stub_heal(monkeypatch, PUBLISHED)

    result = runner.invoke(
        main, ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "status: published" in result.output
    assert "selfheal/fix-thing" in result.output
    assert "https://github.com/o/r/pull/3" in result.output


def test_run_emits_json(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    _stub_heal(monkeypatch, PUBLISHED)

    result = runner.invoke(
        main,
        ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path), "--json"],
    )
    payload = json.loads(result.output)

    assert payload["status"] == "published"
    assert payload["changed_files"] == ["sakthai/calc.py"]
    assert payload["confidence"] == 0.9


def test_run_json_handles_an_outcome_with_no_diagnosis(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    _stub_heal(monkeypatch, HealingOutcome(status=HealStatus.NO_FAILURE, detail="nothing to do"))

    result = runner.invoke(
        main,
        ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path), "--json"],
    )
    payload = json.loads(result.output)

    assert payload["status"] == "no_failure"
    assert payload["failure"] == ""
    assert payload["tests_passed"] is None


def test_run_writes_the_report_file(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    _stub_heal(monkeypatch, PUBLISHED)
    report = tmp_path / "report.md"

    runner.invoke(
        main,
        [
            "heal",
            "run",
            "--log",
            str(log_file),
            "--repo-root",
            str(tmp_path),
            "--report",
            str(report),
        ],
    )

    assert report.read_text(encoding="utf-8") == "# report body"


def test_options_reach_the_pipeline_config(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    captured = _stub_heal(monkeypatch, PUBLISHED)

    runner.invoke(
        main,
        [
            "heal",
            "run",
            "--log",
            str(log_file),
            "--repo-root",
            str(tmp_path),
            "--min-confidence",
            "0.85",
            "--base",
            "develop",
            "--branch-prefix",
            "autofix/",
            "--run-id",
            "777",
            "--run-url",
            "https://x/runs/777",
            "--no-pr",
        ],
    )
    config = captured["config"]

    assert config.min_confidence == 0.85  # type: ignore[union-attr]
    assert config.base_branch == "develop"  # type: ignore[union-attr]
    assert config.branch_prefix == "autofix/"  # type: ignore[union-attr]
    assert config.run_id == "777"  # type: ignore[union-attr]
    assert config.open_pr is False  # type: ignore[union-attr]


def test_dry_run_never_publishes(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    captured = _stub_heal(monkeypatch, PUBLISHED)

    runner.invoke(
        main,
        ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path), "--dry-run"],
    )
    config = captured["config"]

    assert config.dry_run is True  # type: ignore[union-attr]
    assert config.publish_fix is False  # type: ignore[union-attr]


def test_no_publish_leaves_the_fix_in_the_tree(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_completions(monkeypatch)
    captured = _stub_heal(monkeypatch, PUBLISHED)

    runner.invoke(
        main,
        ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path), "--no-publish"],
    )

    assert captured["config"].publish_fix is False  # type: ignore[union-attr]


def test_a_missing_diagnosis_provider_is_a_clean_cli_error(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def explode(**kwargs: object) -> object:
        raise RuntimeError("no credentials configured")

    monkeypatch.setattr(heal_module, "build_completion", explode)

    result = runner.invoke(
        main, ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path)]
    )

    assert result.exit_code != 0
    assert "cannot build the diagnosis model client" in result.output


def test_an_unavailable_narrator_does_not_stop_the_run(
    runner: CliRunner, log_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The walkthrough model is optional; only the diagnosis model is required."""

    def build(**kwargs: object) -> object:
        if kwargs.get("model") == "gemini-3.1-flash-lite":
            raise RuntimeError("no GEMINI_API_KEY")
        return lambda system, user: "{}"

    monkeypatch.setattr(heal_module, "build_completion", build)
    captured = _stub_heal(monkeypatch, PUBLISHED)

    result = runner.invoke(
        main, ["heal", "run", "--log", str(log_file), "--repo-root", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert captured["narrator"] is None


def test_heal_run_args_dataclass_instantiation() -> None:
    from sakthai.cli.heal import HealRunArgs

    args = HealRunArgs.from_dict(
        {
            "log_source": "test.log",
            "repo_root": ".",
            "model": "test-model",
            "provider": None,
            "walkthrough_model": "walk-model",
            "min_confidence": 0.8,
            "base": "main",
            "branch_prefix": "fix/",
            "run_id": "123",
            "run_url": "http://example.com",
            "dry_run": True,
            "no_publish": False,
            "no_pr": False,
            "report_path": None,
            "as_json": True,
        }
    )

    assert args.log_source == "test.log"
    assert args.dry_run is True
    assert args.as_json is True
