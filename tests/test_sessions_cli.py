"""Tests for the sessions CLI commands."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.cli.sessions import parse_duration
from sakthai.config import sessions_dir


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# -- parse_duration unit tests -------------------------------------------


@pytest.mark.parametrize(
    ("val", "expected"),
    [
        ("1d", 86400.0),
        ("2d", 172800.0),
        ("12h", 43200.0),
        ("30m", 1800.0),
        ("90s", 90.0),
        ("0.5d", 43200.0),
    ],
)
def test_parse_duration_valid(val: str, expected: float) -> None:
    assert parse_duration(val) == expected


def test_parse_duration_empty_raises() -> None:
    with pytest.raises(ValueError, match="Empty duration"):
        parse_duration("")


def test_parse_duration_bad_number_raises() -> None:
    with pytest.raises(ValueError, match="Invalid duration format"):
        parse_duration("abcd")


def test_parse_duration_unknown_unit_raises() -> None:
    with pytest.raises(ValueError, match="Unknown duration unit"):
        parse_duration("10w")


def test_sessions_empty(sakthai_home: Path, runner: CliRunner) -> None:
    res = runner.invoke(main, ["sessions", "list"])
    assert res.exit_code == 0
    assert "No sessions found." in res.output


def test_sessions_list_and_show(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)

    # Write a fake session
    sess_id = f"{int(time.time()) - 100}_fake-session-123"
    sess_file = s_dir / f"{sess_id}.json"
    payload = {
        "timestamp": int(time.time()) - 100,
        "task": "Explain quantum physics in simple terms",
        "model": "claude-opus-4-8",
        "usage": {
            "input_tokens": 150,
            "output_tokens": 300,
            "total_tokens": 450,
        },
        "result": {
            "text": "Quantum physics is cool.",
            "iterations": 1,
            "stop_reason": "end_turn",
            "tool_calls": [],
        },
        "messages": [
            {"role": "user", "content": "Explain quantum physics"},
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Quantum physics is cool."}],
            },
        ],
    }
    sess_file.write_text(json.dumps(payload), encoding="utf-8")

    # List
    res_list = runner.invoke(main, ["sessions", "list"])
    assert res_list.exit_code == 0
    assert sess_id in res_list.output
    assert "claude-opus-4-8" in res_list.output
    assert "450" in res_list.output
    assert "Explain quantum physics in simple terms" in res_list.output

    # Show
    res_show = runner.invoke(main, ["sessions", "show", sess_id])
    assert res_show.exit_code == 0
    assert sess_id in res_show.output
    assert "Explain quantum physics in simple terms" in res_show.output
    assert "Quantum physics is cool." in res_show.output
    assert "USER" in res_show.output
    assert "ASSISTANT" in res_show.output


def test_sessions_show_not_found(sakthai_home: Path, runner: CliRunner) -> None:
    res = runner.invoke(main, ["sessions", "show", "nonexistent"])
    assert res.exit_code != 0
    assert "Session 'nonexistent' not found." in res.output


def test_sessions_list_corrupt_json_skipped(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    (s_dir / "bad.json").write_text("{not valid json", encoding="utf-8")
    res = runner.invoke(main, ["sessions", "list"])
    assert res.exit_code == 0
    # Corrupt file is silently skipped; no crash and the header line is printed.
    assert "Session ID" in res.output


def test_sessions_list_truncates_long_task_and_model(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    sess_id = f"{now}_trunc-test"
    payload = {
        "timestamp": now,
        "task": "x" * 60,
        "model": "y" * 25,
        "usage": {"total_tokens": 1},
        "result": {},
        "messages": [],
    }
    (s_dir / f"{sess_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    res = runner.invoke(main, ["sessions", "list"])
    assert res.exit_code == 0
    # Truncation markers appear in the output.
    assert "..." in res.output


def test_sessions_show_tool_blocks(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    sess_id = f"{now}_tool-sess"
    payload = {
        "timestamp": now,
        "task": "do something",
        "model": "claude-sonnet-4-6",
        "usage": {"total_tokens": 10},
        "result": {
            "text": "done",
            "iterations": 2,
            "stop_reason": "end_turn",
            "tool_calls": [],
        },
        "messages": [
            {"role": "user", "content": "do something"},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "learn",
                        "input": {"value": "x"},
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "t1",
                        "content": "learned (id=1)",
                        "is_error": False,
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "done"}],
            },
        ],
    }
    (s_dir / f"{sess_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    res = runner.invoke(main, ["sessions", "show", sess_id])
    assert res.exit_code == 0
    assert "Tool Use: learn" in res.output
    assert "Tool Result" in res.output
    assert "learned (id=1)" in res.output


def test_sessions_show_tool_result_error_flag(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    sess_id = f"{now}_err-sess"
    payload = {
        "timestamp": now,
        "task": "bad call",
        "model": "claude-sonnet-4-6",
        "usage": {"total_tokens": 5},
        "result": {},
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "t2",
                        "content": "RuntimeError: boom",
                        "is_error": True,
                    }
                ],
            }
        ],
    }
    (s_dir / f"{sess_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    res = runner.invoke(main, ["sessions", "show", sess_id])
    assert res.exit_code == 0
    assert "RuntimeError: boom" in res.output


def test_sessions_clean_no_match(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    (s_dir / f"{now}_fresh.json").write_text(
        json.dumps({"timestamp": now, "task": "new"}), encoding="utf-8"
    )
    res = runner.invoke(main, ["sessions", "clean", "--older-than", "1d", "--yes"])
    assert res.exit_code == 0
    assert "No sessions matched" in res.output


def test_sessions_clean_stat_fallback(sakthai_home: Path, runner: CliRunner) -> None:
    """Files whose timestamp can't be extracted fall back to file mtime."""
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    # A file with no numeric prefix AND no valid JSON timestamp
    p = s_dir / "noprefix.json"
    p.write_text("{}", encoding="utf-8")
    import os

    old_mtime = time.time() - 40 * 86400  # 40 days old
    os.utime(p, (old_mtime, old_mtime))
    res = runner.invoke(main, ["sessions", "clean", "--older-than", "30d", "--yes"])
    assert res.exit_code == 0
    assert "deleted" in res.output


def test_sessions_clean(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)

    now = int(time.time())
    # 1. Old session (3 days old)
    old_id = f"{now - 3 * 86400}_old-sess"
    (s_dir / f"{old_id}.json").write_text(
        json.dumps({"timestamp": now - 3 * 86400, "task": "old"}), encoding="utf-8"
    )

    # 2. New session (1 hour old)
    new_id = f"{now - 3600}_new-sess"
    (s_dir / f"{new_id}.json").write_text(
        json.dumps({"timestamp": now - 3600, "task": "new"}), encoding="utf-8"
    )

    # Test clean older than 2d (should match 1 old session)
    # Aborted path
    res_clean_abort = runner.invoke(main, ["sessions", "clean", "--older-than", "2d"], input="n\n")
    assert res_clean_abort.exit_code == 0
    assert "Found 1 session(s) older than 2d." in res_clean_abort.output
    assert "Aborted." in res_clean_abort.output
    assert (s_dir / f"{old_id}.json").exists()

    # Confirmed path
    res_clean = runner.invoke(main, ["sessions", "clean", "--older-than", "2d", "--yes"])
    assert res_clean.exit_code == 0
    assert "Successfully deleted 1 session log file(s)." in res_clean.output
    assert not (s_dir / f"{old_id}.json").exists()
    assert (s_dir / f"{new_id}.json").exists()


def test_sessions_list_empty_dir_no_json_files(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    # Dir exists but has no .json files (only a non-json file)
    (s_dir / "readme.txt").write_text("nothing here", encoding="utf-8")
    res = runner.invoke(main, ["sessions", "list"])
    assert res.exit_code == 0
    assert "No sessions found." in res.output


def test_sessions_list_respects_limit(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    for i in range(5):
        (s_dir / f"{now - i}_sess-{i}.json").write_text(
            json.dumps({"timestamp": now - i, "task": f"task-{i}", "model": "m"}),
            encoding="utf-8",
        )
    res = runner.invoke(main, ["sessions", "list", "--limit", "2"])
    assert res.exit_code == 0
    # Only 2 sessions in output rows (header + separator don't count as sessions)
    task_lines = [line for line in res.output.splitlines() if "task-" in line]
    assert len(task_lines) == 2


def test_sessions_show_corrupt_file_reports_error(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    (s_dir / "corrupt_sess.json").write_text("{ invalid json", encoding="utf-8")
    res = runner.invoke(main, ["sessions", "show", "corrupt_sess"])
    assert res.exit_code != 0
    assert "Failed to read session file" in res.output


def test_sessions_clean_bad_duration_reports_error(sakthai_home: Path, runner: CliRunner) -> None:
    res = runner.invoke(main, ["sessions", "clean", "--older-than", "5x"])
    assert res.exit_code != 0
    assert "Unknown duration unit" in res.output


def test_sessions_clean_no_sessions_dir(sakthai_home: Path, runner: CliRunner) -> None:
    # Don't create the sessions dir — sessions_clean should handle gracefully
    res = runner.invoke(main, ["sessions", "clean", "--older-than", "1d", "--yes"])
    assert res.exit_code == 0
    assert "No sessions directory found." in res.output


def test_sessions_clean_unlink_failure(
    sakthai_home: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    old_ts = int(time.time()) - 60 * 86400
    sess_file = s_dir / f"{old_ts}_old-sess.json"
    sess_file.write_text(json.dumps({"timestamp": old_ts, "task": "old task"}), encoding="utf-8")

    original_unlink = sess_file.__class__.unlink

    def failing_unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name.endswith("old-sess.json"):
            raise OSError("permission denied")
        original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(sess_file.__class__, "unlink", failing_unlink)
    res = runner.invoke(main, ["sessions", "clean", "--older-than", "1d", "--yes"])
    assert res.exit_code == 0
    assert "Failed to delete" in res.output
