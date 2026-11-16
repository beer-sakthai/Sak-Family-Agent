"""Tests for sakthai.agent.eval — local model eval/MLOps logging."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sakthai.agent.eval import (
    EvalRecord,
    evaluate_all_personas,
    evaluate_persona_readiness,
    extract_soul_intro_line,
    persona_eval_log_path,
    record_eval,
    summarize_evals,
    task_preview,
)
from sakthai.config import PERSONA_NAMES


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

    def test_never_raises_on_failure(self, tmp_path: Path) -> None:
        # Pointing at a directory (not a file) makes the open() fail; this must
        # be swallowed, matching _save_session_log's best-effort contract.
        bad_path = tmp_path  # a directory, not a file
        record_eval(_record(), path=bad_path)


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


class TestPersonaAttribution:
    """The persona field exists so the dashboard need not guess who ran what.

    It is a trailing defaulted field because the log is append-only: records
    written before it existed simply lack the key, and must stay readable.
    """

    def test_persona_defaults_to_none(self) -> None:
        assert _record().persona is None

    def test_persona_round_trips_through_the_log(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(persona="saksee"), path=log_path)

        line = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert line["persona"] == "saksee"

    def test_legacy_record_without_the_key_still_parses(self, tmp_path: Path) -> None:
        """A line written before this field existed must not break the reader."""
        log_path = tmp_path / "eval.jsonl"
        legacy = {
            "timestamp": 1_700_000_000,
            "task_preview": "old run",
            "model": "claude-opus-4-8",
            "provider": "anthropic",
            "iterations": 1,
            "stop_reason": "end_turn",
            "latency_s": 1.0,
            "input_tokens": 10,
            "output_tokens": 5,
            "tool_call_count": 0,
            "had_error": False,
        }
        log_path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 1

    def test_mixed_legacy_and_attributed_lines_coexist(self, tmp_path: Path) -> None:
        """The expected steady state: some lines attributed, some not."""
        log_path = tmp_path / "eval.jsonl"
        log_path.write_text(
            json.dumps(
                {
                    "timestamp": 1_700_000_000,
                    "task_preview": "old run",
                    "model": "m",
                    "provider": "anthropic",
                    "iterations": 1,
                    "stop_reason": "end_turn",
                    "latency_s": 1.0,
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "tool_call_count": 0,
                    "had_error": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        record_eval(_record(model="m", persona="sakthai"), path=log_path)

        summary = summarize_evals(path=log_path)
        assert summary["count"] == 2
        assert summary["per_model"]["m"]["count"] == 2
        assert summary["per_persona"]["unattributed"]["count"] == 1
        assert summary["per_persona"]["sakthai"]["count"] == 1


class TestPerPersonaEvaluation:
    def test_filter_summarize_evals_by_persona(self, tmp_path: Path) -> None:
        log_path = tmp_path / "eval.jsonl"
        record_eval(_record(model="m1", persona="sakthai", latency_s=1.0), path=log_path)
        record_eval(_record(model="m2", persona="sakking", latency_s=3.0), path=log_path)
        record_eval(_record(model="m1", persona="sakthai", latency_s=5.0), path=log_path)

        summary = summarize_evals(path=log_path, persona="sakthai")
        assert summary["count"] == 2
        assert summary["avg_latency_s"] == 3.0
        assert set(summary["per_persona"]) == {"sakthai"}

    def test_persona_eval_log_path_and_invalid_persona(self, tmp_path: Path) -> None:
        old_home = os.environ.get("SAKTHAI_HOME")
        os.environ["SAKTHAI_HOME"] = str(tmp_path)
        try:
            path = persona_eval_log_path("sakthai")
            assert path.name == "eval.jsonl"
            assert path.parent.name == "sakthai"
        finally:
            if old_home is None:
                os.environ.pop("SAKTHAI_HOME", None)
            else:
                os.environ["SAKTHAI_HOME"] = old_home

        with pytest.raises(ValueError, match="Unknown persona"):
            persona_eval_log_path("not-a-persona")

        with pytest.raises(ValueError, match="Unknown persona"):
            evaluate_persona_readiness("not-a-persona")

    def test_include_persona_shards_merges_and_attributes_records(self, tmp_path: Path) -> None:
        old_home = os.environ.get("SAKTHAI_HOME")
        os.environ["SAKTHAI_HOME"] = str(tmp_path)
        try:
            shard = persona_eval_log_path("saktan")
            record_eval(_record(model="sakthai", persona=None, latency_s=1.0), path=shard)
            record_eval(_record(model="sakthai", persona="saktan", latency_s=3.0), path=shard)

            summary = summarize_evals(include_persona_shards=True)
            assert summary["count"] == 2
            assert summary["per_persona"]["saktan"]["count"] == 2
        finally:
            if old_home is None:
                os.environ.pop("SAKTHAI_HOME", None)
            else:
                os.environ["SAKTHAI_HOME"] = old_home

    def test_extract_soul_intro_line_missing_returns_none(self) -> None:
        assert extract_soul_intro_line("No intro line here.") is None

    def test_evaluate_persona_readiness_incomplete_dir(self, tmp_path: Path) -> None:
        info = evaluate_persona_readiness("sakthai", personas_dir=tmp_path)
        assert info["all_working_files_present"] is False
        assert info["skill_count"] == 0
        assert info["ready"] is False

    def test_evaluate_all_six_personas_ready(self) -> None:
        report = evaluate_all_personas()
        assert set(report) == set(PERSONA_NAMES)
        for persona, info in report.items():
            assert info["all_working_files_present"] is True, f"{persona} missing working files"
            assert info["has_v9_rubric_soul"] is True, f"{persona} missing v9 rubric in SOUL.md"
            assert info["has_v9_rubric_cycle"] is True, f"{persona} missing v9 rubric in CYCLE.md"
            assert info["intro_line"], f"{persona} missing intro_line"
            assert info["primary_skills_present"] is True, f"{persona} missing primary skills"
            assert info["evolution_ready"] is True, f"{persona} missing evolution engine"
            assert info["ready"] is True, f"{persona} not ready: {info}"
