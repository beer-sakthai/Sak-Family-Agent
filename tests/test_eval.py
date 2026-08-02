"""Tests for sakthai.agent.eval — local model eval/MLOps logging."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from sakthai.agent.eval import EvalRecord, record_eval, summarize_evals, task_preview


def _record(**overrides: object) -> EvalRecord:
    base: dict[str, object] = {
        "timestamp": 1_700_000_000,
        "task_preview": "do a thing",
        "model": "claude-opus-4-8",
        "provider": "anthropic",
        "iterations": 2,
        "stop_reason": "end_turn",
        "latency_s": 1.5,
        "input_tokens": 100,
        "output_tokens": 50,
        "tool_call_count": 1,
        "had_error": False,
    }
    base.update(overrides)
    return EvalRecord(**base)  # type: ignore[arg-type]


class TestTaskPreview:
    def test_short_task_unchanged(self) -> None:
        assert task_preview("hello") == "hello"

    def test_collapses_whitespace(self) -> None:
        assert task_preview("hello   \n\n  world") == "hello world"

    def test_truncates_long_task(self) -> None:
        long_task = "x" * 200
        preview = task_preview(long_task, limit=80)
        assert len(preview) == 80
        assert preview.endswith("…")


class TestRecordEval:
    def test_appends_jsonl_line(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(), path=log_path)
        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["model"] == "claude-opus-4-8"

    def test_appends_multiple_records(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(model="model-a"), path=log_path)
        record_eval(_record(model="model-b"), path=log_path)
        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        log_path = tmp_path / "nested" / "eval.jsonl"
        record_eval(_record(), path=log_path)
        assert log_path.exists()

    def test_never_raises_on_failure(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        # Pointing at a directory (not a file) makes the open() fail; this must
        # be swallowed, matching _save_session_log's best-effort contract.
        bad_path = tmp_path  # a directory, not a file
        with caplog.at_level(logging.WARNING):
            record_eval(_record(), path=bad_path)
        assert any("Failed to record eval" in msg for msg in caplog.messages)


class TestSummarizeEvals:
    def test_empty_log_returns_zero_count(self, tmp_path: Path) -> None:
        summary = summarize_evals(path=tmp_path / "missing.jsonl")
        assert summary == {"count": 0}

    def test_aggregates_counts_and_tokens(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(input_tokens=100, output_tokens=50), path=log_path)
        record_eval(_record(input_tokens=200, output_tokens=75), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 2
        assert summary["total_input_tokens"] == 300
        assert summary["total_output_tokens"] == 125

    def test_error_rate(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(had_error=False), path=log_path)
        record_eval(_record(had_error=True), path=log_path)
        record_eval(_record(had_error=True), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["error_rate"] == 2 / 3

    def test_avg_latency(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(latency_s=1.0), path=log_path)
        record_eval(_record(latency_s=3.0), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["avg_latency_s"] == 2.0

    def test_per_model_breakdown(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(model="model-a", latency_s=1.0), path=log_path)
        record_eval(_record(model="model-a", latency_s=3.0), path=log_path)
        record_eval(_record(model="model-b", latency_s=5.0), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["per_model"]["model-a"]["count"] == 2
        assert summary["per_model"]["model-a"]["avg_latency_s"] == 2.0
        assert summary["per_model"]["model-b"]["count"] == 1

    def test_respects_limit_by_taking_most_recent(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        for i in range(5):
            record_eval(_record(model=f"model-{i}"), path=log_path)

        summary = summarize_evals(path=log_path, limit=2)
        assert summary["count"] == 2
        assert set(summary["per_model"]) == {"model-3", "model-4"}

    def test_tolerates_malformed_lines(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(), path=log_path)
        with log_path.open("a", encoding="utf-8") as f:
            f.write("not json\n")

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 1

    def test_tolerates_blank_lines(self, tmp_path: Path) -> None:
        log_path = tmp_path / "blank_lines.jsonl"
        record_eval(_record(), path=log_path)
        with log_path.open("a", encoding="utf-8") as f:
            f.write("\n\n\n")  # blank lines
        record_eval(_record(), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 2

    def test_path_none_uses_eval_log_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        log_path = tmp_path / "env_eval.jsonl"
        record_eval(_record(model="env-model"), path=log_path)
        monkeypatch.setenv("SAKTHAI_EVAL_LOG", str(log_path))

        summary = summarize_evals(path=None)
        assert summary["count"] == 1
        assert "env-model" in summary["per_model"]

    def test_partial_records_graceful_defaults(self, tmp_path: Path) -> None:
        log_path = tmp_path / "partial_eval.jsonl"
        # Record 1: empty dict
        log_path.write_text(json.dumps({}) + "\n", encoding="utf-8")
        # Record 2: some fields present, some missing/null
        record_2 = {
            "model": "partial-model",
            "had_error": True,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record_2) + "\n")

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 2
        assert summary["error_rate"] == 0.5
        assert summary["total_input_tokens"] == 0
        assert summary["total_output_tokens"] == 0
        assert summary["avg_latency_s"] == 0.0

        per_model = summary["per_model"]
        assert "unknown" in per_model
        assert per_model["unknown"]["count"] == 1
        assert per_model["unknown"]["input_tokens"] == 0
        assert per_model["unknown"]["output_tokens"] == 0
        assert per_model["unknown"]["avg_latency_s"] == 0.0

        assert "partial-model" in per_model
        assert per_model["partial-model"]["count"] == 1
        assert per_model["partial-model"]["input_tokens"] == 0
        assert per_model["partial-model"]["output_tokens"] == 0
        assert per_model["partial-model"]["avg_latency_s"] == 0.0
