"""Tests for ``sakthai memory consolidate-sessions``."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

import sakthai.agent.loop as loop
from sakthai.cli import main
from sakthai.config import memory_db_path
from sakthai.config import sakthai_home as sakthai_home_path
from sakthai.config import sessions_dir
from sakthai.memory.store import MemoryStore


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _write_session(name: str, task: str, text: str) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    (s_dir / f"{name}.json").write_text(
        json.dumps({"task": task, "result": {"text": text}}),
        encoding="utf-8",
    )


def _patch_extraction(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    """Make run_agent return a fixed extraction without any network call."""
    monkeypatch.setattr(
        loop, "run_agent", lambda *a, **k: types.SimpleNamespace(text=text)
    )


def _consolidated_values() -> list[str]:
    with MemoryStore(memory_db_path()) as store:
        return [f.value for f in store.list_facts() if f.kind == "consolidated"]


def test_no_sessions(sakthai_home: Path, runner: CliRunner) -> None:
    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    assert "No local session logs found." in res.output


def test_extracts_and_learns(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_session("0001_s", "what theme?", "set it up")
    _patch_extraction(
        monkeypatch,
        "User prefers dark mode\n- User timezone is GMT+7\n\nNone-ish? no",
    )

    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    assert "learned 3 new fact(s)" in res.output

    values = _consolidated_values()
    assert "User prefers dark mode" in values
    assert "User timezone is GMT+7" in values  # leading "- " stripped
    # state file records the processed log
    state = json.loads(
        (sakthai_home_path() / "consolidated_sessions.json").read_text(encoding="utf-8")
    )
    assert state == ["0001_s.json"]


def test_idempotent_second_run(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_session("0001_s", "q", "a")
    _patch_extraction(monkeypatch, "User likes tea")

    first = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert first.exit_code == 0
    second = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert second.exit_code == 0
    assert "already been consolidated" in second.output
    # no duplicate fact created on the second run
    assert _consolidated_values().count("User likes tea") == 1


def test_corrupt_log_skipped(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    (s_dir / "0001_bad.json").write_text("{ not json", encoding="utf-8")
    _write_session("0002_ok", "q", "a")
    _patch_extraction(monkeypatch, "User runs Linux")

    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    assert "Skipping unreadable session log 0001_bad.json" in res.output
    assert "User runs Linux" in _consolidated_values()


def test_none_extraction_stores_nothing(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_session("0001_s", "q", "a")
    _patch_extraction(monkeypatch, "None")

    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    assert "learned 0 new fact(s)" in res.output
    assert _consolidated_values() == []


def test_corrupted_state_file_resets_to_empty_set(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A malformed consolidated_sessions.json is silently discarded (lines 329-330)."""
    state_file = sakthai_home_path() / "consolidated_sessions.json"
    state_file.write_text("{ not valid json !!!}", encoding="utf-8")
    _write_session("0001_s", "q", "a")
    _patch_extraction(monkeypatch, "User prefers Linux")

    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    # Session was processed despite the corrupt state file
    assert "learned 1 new fact(s)" in res.output


def test_run_agent_error_is_reported_and_continues(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_agent exceptions in the extraction step are caught and reported (lines 359-361)."""
    _write_session("0001_good", "q", "a")
    _write_session("0002_fail", "q2", "a2")

    call_count = 0

    def _patched_run_agent(*args: object, **kwargs: object) -> object:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("LLM unavailable")
        import types

        return types.SimpleNamespace(text="User likes coffee")

    monkeypatch.setattr(loop, "run_agent", _patched_run_agent)

    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    assert "Error extracting from 0001_good.json" in res.output
    assert "learned 1 new fact(s)" in res.output


def test_state_file_write_failure_warns_but_completes(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OSError writing the state file produces a warning but doesn't abort (lines 374-375)."""
    _write_session("0001_s", "q", "a")
    _patch_extraction(monkeypatch, "User uses macOS")

    # Prevent the state file from being written
    state_file = sakthai_home_path() / "consolidated_sessions.json"
    state_file.mkdir()  # directory with same name → write will fail with IsADirectoryError

    res = runner.invoke(main, ["memory", "consolidate-sessions"])
    assert res.exit_code == 0
    assert "Warning: could not save consolidation state" in res.output
    assert "learned 1 new fact(s)" in res.output
