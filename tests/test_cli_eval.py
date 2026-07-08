"""Tests for sakthai.cli.eval."""

from __future__ import annotations

import json
from pathlib import Path

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
    err: bool = False
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
        had_error=err
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
