"""CLI error paths must end in a clean ``Error:`` line and a non-zero exit.

Each case here used to crash with a raw traceback, exit 0 on failure, or accept
a meaningless value silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

import sakthai.web.server as server_mod
from sakthai.cli import main


@pytest.fixture(autouse=True)
def _isolated_home(sakthai_home: Path) -> Path:
    return sakthai_home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _assert_clean_failure(result, exit_code: int = 1) -> None:  # type: ignore[no-untyped-def]
    assert result.exit_code == exit_code, result.output
    assert "Traceback" not in result.output
    assert not isinstance(result.exception, OSError | ValueError | OverflowError)


# --- web serve ------------------------------------------------------------


@pytest.mark.parametrize("port", ["99999", "-1"])
def test_web_serve_rejects_out_of_range_port(runner: CliRunner, port: str) -> None:
    result = runner.invoke(main, ["web", "serve", "--port", port])
    _assert_clean_failure(result, exit_code=2)
    assert "--port" in result.output


def test_web_serve_reports_bind_failure_cleanly(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _in_use(**_: object) -> None:
        raise OSError(98, "Address already in use")

    monkeypatch.setattr(server_mod, "serve", _in_use)
    result = runner.invoke(main, ["web", "serve"])
    _assert_clean_failure(result)
    assert "Address already in use" in result.output


# --- memory export --------------------------------------------------------


def test_memory_export_to_unwritable_path_is_a_clean_error(
    runner: CliRunner, tmp_path: Path
) -> None:
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("", encoding="utf-8")  # a file where a directory is needed
    result = runner.invoke(main, ["memory", "export", str(blocker / "out.json")])
    _assert_clean_failure(result)
    assert "could not write snapshot" in result.output


# --- --limit must be >= 1 -------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["recall", "tea", "--limit", "0"],
        ["memory", "show", "--limit", "-1"],
        ["memory", "search", "tea", "--limit", "0"],
        ["memory", "family", "--limit", "0"],
        ["memory", "consolidate-sessions", "--limit", "0"],
        ["sessions", "list", "--limit", "0"],
        ["sessions", "search", "tea", "--limit", "0"],
        ["eval", "summary", "--limit", "0"],
    ],
)
def test_limit_below_one_is_rejected(runner: CliRunner, argv: list[str]) -> None:
    result = runner.invoke(main, argv)
    _assert_clean_failure(result, exit_code=2)
    assert "--limit" in result.output


# --- run --dry-run reports every problem ----------------------------------


def test_dry_run_reports_unknown_skill_even_without_credentials(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/nonexistent")
    result = runner.invoke(
        main,
        ["run", "--dry-run", "--no-mcp", "-p", "anthropic", "--with-skills", "no-such-skill", "hi"],
    )
    _assert_clean_failure(result)
    assert "no credentials found" in result.output
    assert "Unresolved --with-skills name(s): no-such-skill" in result.output


# --- budgets must be positive ---------------------------------------------


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("--max-iterations", "0"),
        ("--max-tokens", "0"),
        ("--max-seconds", "0"),
        ("--max-seconds", "-1"),
    ],
)
def test_run_rejects_a_non_positive_budget(runner: CliRunner, flag: str, value: str) -> None:
    # --dry-run used to pass these, and a real run rejected them only after
    # setup (iterations, seconds) or a provider round trip (tokens).
    result = runner.invoke(main, ["run", "--dry-run", "--no-mcp", flag, value, "hi"])
    _assert_clean_failure(result, exit_code=2)
    assert flag in result.output


def test_memory_consolidate_rejects_a_negative_age(runner: CliRunner) -> None:
    # A negative age reads as "older than the future", so it folded every fact.
    result = runner.invoke(main, ["memory", "consolidate", "--age", "-5"])
    _assert_clean_failure(result, exit_code=2)
    assert "--age" in result.output


# --- memory family --------------------------------------------------------


def test_memory_family_unknown_persona_is_a_usage_error(runner: CliRunner) -> None:
    result = runner.invoke(main, ["memory", "family", "--personas", "sakking,nobody"])
    _assert_clean_failure(result, exit_code=2)
    assert "--personas" in result.output
    assert "nobody" in result.output


# --- memory import reads only json snapshots ------------------------------


@pytest.mark.parametrize("facts", [["tea"], ["tea", "coffee"]])
@pytest.mark.parametrize("fmt", ["csv", "jsonl"])
def test_memory_import_of_a_flat_export_says_which_format_works(
    runner: CliRunner, tmp_path: Path, fmt: str, facts: list[str]
) -> None:
    # A one-record jsonl file is valid JSON, so it fails later than a
    # multi-record one; both used to surface a bare parse or version error.
    for fact in facts:
        runner.invoke(main, ["learn", fact])
    snap = tmp_path / f"snap.{fmt}"
    assert runner.invoke(main, ["memory", "export", str(snap), "--format", fmt]).exit_code == 0
    result = runner.invoke(main, ["memory", "import", str(snap)])
    _assert_clean_failure(result)
    assert "--format json" in result.output


# --- learn --kind must not be blank ---------------------------------------


@pytest.mark.parametrize("kind", ["", "   "])
def test_learn_rejects_a_blank_kind(runner: CliRunner, kind: str) -> None:
    result = runner.invoke(main, ["learn", "tea", "--kind", kind])
    _assert_clean_failure(result, exit_code=2)
    assert "--kind" in result.output


def test_learn_strips_the_kind(runner: CliRunner) -> None:
    assert runner.invoke(main, ["learn", "tea", "--kind", " drink "]).exit_code == 0
    assert "[drink] tea" in runner.invoke(main, ["recall", "tea"]).output
