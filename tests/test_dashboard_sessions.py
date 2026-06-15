"""Tests for the dashboard session-data layer (collect_session_data)."""

from __future__ import annotations

import json
from pathlib import Path

from sakthai.dashboard.data import collect_session_data


def _write_session(directory: Path, name: str, **fields: object) -> None:
    payload = {
        "timestamp": fields.get("timestamp", 0),
        "task": fields.get("task", ""),
        "model": fields.get("model", "unknown"),
        "usage": fields.get("usage", {}),
        "result": fields.get("result", {}),
    }
    (directory / name).write_text(json.dumps(payload), encoding="utf-8")


def test_collect_session_data_empty_when_no_dir(tmp_path: Path) -> None:
    data = collect_session_data(tmp_path / "missing")
    assert data["source"] == "empty"
    assert data["totals"]["sessions"] == 0
    assert data["by_model"] == []
    assert data["recent_sessions"] == []


def test_collect_session_data_aggregates_by_model_and_day(tmp_path: Path) -> None:
    # Two days, two models.
    day1 = 1_700_000_000  # 2023-11-14
    day2 = day1 + 86_400
    _write_session(
        tmp_path,
        "1.json",
        timestamp=day1,
        model="claude-opus-4-8",
        task="first task",
        usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        result={"iterations": 2, "stop_reason": "end_turn"},
    )
    _write_session(
        tmp_path,
        "2.json",
        timestamp=day1 + 60,
        model="claude-opus-4-8",
        task="second task",
        usage={"input_tokens": 5, "output_tokens": 5, "total_tokens": 10},
        result={"iterations": 1, "stop_reason": "end_turn"},
    )
    _write_session(
        tmp_path,
        "3.json",
        timestamp=day2,
        model="gpt-4o",
        task="third task",
        usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
        result={"iterations": 1, "stop_reason": "end_turn"},
    )

    data = collect_session_data(tmp_path)
    assert data["source"] == "live"
    assert data["totals"]["sessions"] == 3
    assert data["totals"]["total_tokens"] == 43
    assert data["totals"]["input_tokens"] == 16

    # by_model sorted by total tokens desc: opus (40) before gpt-4o (3).
    models = [m["model"] for m in data["by_model"]]
    assert models == ["claude-opus-4-8", "gpt-4o"]
    assert data["by_model"][0]["sessions"] == 2
    assert data["by_model"][0]["total_tokens"] == 40

    # by_day has two labels, ascending.
    assert len(data["by_day"]["labels"]) == 2
    assert data["by_day"]["labels"] == sorted(data["by_day"]["labels"])
    assert sum(data["by_day"]["tokens"]) == 43

    # recent_sessions newest first.
    assert data["recent_sessions"][0]["model"] == "gpt-4o"


def test_collect_session_data_skips_malformed(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    _write_session(
        tmp_path,
        "ok.json",
        timestamp=1_700_000_000,
        model="m",
        usage={"total_tokens": 7},
        result={"iterations": 1, "stop_reason": "end_turn"},
    )
    data = collect_session_data(tmp_path)
    assert data["totals"]["sessions"] == 1
    assert data["totals"]["total_tokens"] == 7


def test_collect_session_data_truncates_long_task(tmp_path: Path) -> None:
    _write_session(
        tmp_path,
        "1.json",
        timestamp=1_700_000_000,
        model="m",
        task="x" * 200,
        usage={"total_tokens": 1},
    )
    data = collect_session_data(tmp_path)
    assert data["recent_sessions"][0]["task"].endswith("…")
    assert len(data["recent_sessions"][0]["task"]) <= 81
