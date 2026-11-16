"""Tests for sakthai.cli.eval."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sakthai.agent.eval import EvalRecord, record_eval
from sakthai.cli import main


@pytest.fixture(autouse=True)
def _isolated_home(sakthai_home: Path) -> Path:
    return sakthai_home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _record(
    model: str = "claude-opus",
    latency: float = 2.0,
    in_tok: int = 10,
    out_tok: int = 5,
    err: bool = False,
) -> EvalRecord:
    return EvalRecord(
        timestamp=1700000000,
        task_preview="do a thing",
        model=model,
        provider="anthropic",
        iterations=1,
        stop_reason="end_turn",
        latency_s=latency,
        input_tokens=in_tok,
        output_tokens=out_tok,
        tool_call_count=1,
        had_error=err,
    )


def test_eval_summary_empty(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "summary"])
    assert result.exit_code == 0
    assert "no eval records yet" in result.output


def test_eval_summary_json(runner: CliRunner) -> None:
    record_eval(_record(model="model-a"))
    result = runner.invoke(main, ["eval", "summary", "--json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["count"] == 1
    assert data["per_model"]["model-a"]["count"] == 1


def test_eval_summary_text(runner: CliRunner) -> None:
    record_eval(_record(model="model-a", latency=2.0, in_tok=10, out_tok=5, err=False))
    record_eval(_record(model="model-b", latency=4.0, in_tok=20, out_tok=10, err=True))

    result = runner.invoke(main, ["eval", "summary"])
    assert result.exit_code == 0

    assert "runs:          2" in result.output
    assert "error rate:    50.0%" in result.output
    assert "avg latency:   3.00s" in result.output
    assert "input tokens:  30" in result.output
    assert "output tokens: 15" in result.output
    assert "model-a" in result.output
    assert "model-b" in result.output


def test_eval_summary_persona_filter(runner: CliRunner) -> None:
    record_eval(
        EvalRecord(
            timestamp=1700000001,
            task_preview="lead task",
            model="deepseek-v4",
            provider="huggingface",
            iterations=1,
            stop_reason="end_turn",
            latency_s=1.5,
            input_tokens=15,
            output_tokens=10,
            tool_call_count=0,
            had_error=False,
            persona="sakthai",
        )
    )
    record_eval(
        EvalRecord(
            timestamp=1700000002,
            task_preview="runner task",
            model="qwen-coder",
            provider="huggingface",
            iterations=1,
            stop_reason="end_turn",
            latency_s=2.5,
            input_tokens=25,
            output_tokens=20,
            tool_call_count=1,
            had_error=False,
            persona="sakking",
        )
    )

    result = runner.invoke(main, ["eval", "summary", "--persona", "sakthai", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["count"] == 1
    assert set(data["per_persona"]) == {"sakthai"}

    text_res = runner.invoke(main, ["eval", "summary", "--persona", "sakthai"])
    assert text_res.exit_code == 0
    assert "# Eval summary (sakthai)" in text_res.output
    assert "# Per-persona" in text_res.output


def test_eval_personas_cli_all_six(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "personas"])
    assert result.exit_code == 0
    for p in ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan"):
        assert p in result.output
        assert "[READY]" in result.output

    single_res = runner.invoke(main, ["eval", "personas", "--persona", "saktan"])
    assert single_res.exit_code == 0
    assert "saktan" in single_res.output

    json_res = runner.invoke(main, ["eval", "personas", "--json"])
    assert json_res.exit_code == 0
    payload = json.loads(json_res.output)
    assert len(payload) == 6
    assert all(info["ready"] for info in payload.values())

    incomplete = {
        "saktan": {
            "persona": "saktan",
            "ready": False,
            "working_files": {"SOUL.md": False},
            "has_v9_rubric_soul": False,
            "has_v9_rubric_cycle": False,
            "skill_count": 0,
            "provider": None,
            "model": None,
        }
    }
    with patch("sakthai.cli.eval.evaluate_all_personas", return_value=incomplete):
        fail_text = runner.invoke(main, ["eval", "personas"])
        assert fail_text.exit_code == 1
        assert "[INCOMPLETE]" in fail_text.output

        fail_json = runner.invoke(main, ["eval", "personas", "--json"])
        assert fail_json.exit_code == 1
