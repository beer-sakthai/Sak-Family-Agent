"""Tests for cross-session content search."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.memory.session_search import SessionMatch, search_sessions


def _write_session(
    directory: Path,
    session_id: str,
    *,
    timestamp: int,
    task: str = "",
    result_text: str = "",
    tool_calls: list[dict] | None = None,
) -> None:
    payload = {
        "timestamp": timestamp,
        "task": task,
        "model": "claude-opus-4-8",
        "usage": {"total_tokens": 0},
        "result": {
            "text": result_text,
            "iterations": 1,
            "stop_reason": "end_turn",
            "tool_calls": tool_calls or [],
        },
        "messages": [],
    }
    (directory / f"{session_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_matches_on_task_text(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="Explain quantum physics")
    _write_session(tmp_path, "s2", timestamp=200, task="Bake a cake")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_matches_on_result_text(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="task", result_text="The answer is 42.")

    results = search_sessions("answer", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_matches_on_tool_call_name_and_input(tmp_path: Path) -> None:
    _write_session(
        tmp_path,
        "s1",
        timestamp=100,
        task="task",
        tool_calls=[{"name": "learn", "input": {"value": "uses vim"}, "is_error": False}],
    )

    by_name = search_sessions("learn", sessions_dir=tmp_path)
    by_input = search_sessions("vim", sessions_dir=tmp_path)

    assert [m.session_id for m in by_name] == ["s1"]
    assert [m.session_id for m in by_input] == ["s1"]


def test_and_of_terms_requires_all_terms(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="quantum physics lecture")
    _write_session(tmp_path, "s2", timestamp=200, task="quantum computing")

    results = search_sessions("quantum physics", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_no_match_returns_empty_list(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="bake a cake")

    assert search_sessions("quantum", sessions_dir=tmp_path) == []


def test_case_insensitive_matching(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="Explain QUANTUM Physics")

    results = search_sessions("quantum physics", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_empty_query_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="`query` is required"):
        search_sessions("", sessions_dir=tmp_path)


def test_whitespace_only_query_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="`query` is required"):
        search_sessions("   ", sessions_dir=tmp_path)


def test_missing_sessions_directory_returns_empty_list(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    assert search_sessions("anything", sessions_dir=missing) == []


def test_corrupt_session_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{not valid json", encoding="utf-8")
    _write_session(tmp_path, "s1", timestamp=100, task="quantum physics")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_invalid_utf8_session_file_is_skipped(tmp_path: Path) -> None:
    # An interrupted session write can truncate mid-multibyte-sequence.
    (tmp_path / "bad.json").write_bytes(b'{"task": "quantum\xff\xfe')
    _write_session(tmp_path, "s1", timestamp=100, task="quantum physics")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_results_ordered_by_timestamp_descending(tmp_path: Path) -> None:
    _write_session(tmp_path, "oldest", timestamp=100, task="quantum")
    _write_session(tmp_path, "newest", timestamp=300, task="quantum")
    _write_session(tmp_path, "middle", timestamp=200, task="quantum")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["newest", "middle", "oldest"]


def test_limit_caps_result_count(tmp_path: Path) -> None:
    for i in range(5):
        _write_session(tmp_path, f"s{i}", timestamp=100 + i, task="quantum")

    results = search_sessions("quantum", sessions_dir=tmp_path, limit=2)

    assert len(results) == 2


def test_matched_snippet_contains_query_context(tmp_path: Path) -> None:
    _write_session(
        tmp_path,
        "s1",
        timestamp=100,
        task="A long task description that mentions quantum physics somewhere in the middle",
    )

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert "quantum" in results[0].matched_snippet.lower()


def test_session_match_is_frozen_dataclass() -> None:
    match = SessionMatch(session_id="s1", timestamp=100.0, task="t", matched_snippet="snip")
    with pytest.raises(AttributeError):
        match.session_id = "s2"  # type: ignore[misc]
