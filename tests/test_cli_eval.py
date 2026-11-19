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
    persona: str | None = None,
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
        persona=persona,
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
            "readiness_score": 0.5,
            "mcp_ready": False,
            "working_files": {"SOUL.md": False},
            "has_v9_rubric_soul": False,
            "has_v9_rubric_cycle": False,
            "skill_count": 0,
            "provider": None,
            "model": None,
            "diagnostics": ["Missing working file: SOUL.md"],
        }
    }
    with patch("sakthai.cli.eval.evaluate_all_personas", return_value=incomplete):
        fail_text = runner.invoke(main, ["eval", "personas"])
        assert fail_text.exit_code == 1
        assert "[INCOMPLETE]" in fail_text.output
        assert "Missing working file: SOUL.md" in fail_text.output

        fail_json = runner.invoke(main, ["eval", "personas", "--json"])
        assert fail_json.exit_code == 1


def test_eval_audit_all_and_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "audit"])
    assert result.exit_code == 0
    assert "Sak Family 5-Pillar Fleet Audit" in result.output
    assert "sakthai" in result.output

    res_json = runner.invoke(main, ["eval", "audit", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["all_passed"] is True
    assert data["fleet_average_score"] >= 0.95


def test_eval_audit_single_persona(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "audit", "--persona", "sakthai"])
    assert result.exit_code == 0
    assert "Sak Family Persona Audit: sakthai" in result.output

    res_json = runner.invoke(main, ["eval", "audit", "--persona", "sakthai", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert "sakthai" in data
    assert data["sakthai"]["passed"] is True


def test_eval_audit_failure_exit_code(runner: CliRunner) -> None:
    mock_failed_card = {
        "passed": False,
        "composite_score": 0.5,
        "grade": "F",
        "pillars": {
            "readiness": {"passed": False, "score": 0.5},
            "soul": {"passed": False, "score": 0.5},
            "skills": {"passed": False, "score": 0.5},
            "memory": {"passed": False, "score": 0.5},
            "safety": {"passed": False, "score": 0.5},
        },
        "diagnostics": ["Severe failure"],
    }
    with patch("sakthai.cli.eval.evaluate_persona_audit", return_value=mock_failed_card):
        res = runner.invoke(main, ["eval", "audit", "--persona", "sakking"])
        assert res.exit_code == 1
        assert "Severe failure" in res.output

        res_json = runner.invoke(main, ["eval", "audit", "--persona", "sakking", "--json"])
        assert res_json.exit_code == 1


def test_eval_soul_all_and_single(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "soul"])
    assert result.exit_code == 0
    assert "[ALIGNED]" in result.output

    res_single = runner.invoke(main, ["eval", "soul", "--persona", "sakking"])
    assert res_single.exit_code == 0
    assert "sakking" in res_single.output

    res_json = runner.invoke(main, ["eval", "soul", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert len(data) == 6


def test_eval_skills_all_and_single(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "skills"])
    assert result.exit_code == 0
    assert "[HEALTHY]" in result.output

    res_single = runner.invoke(main, ["eval", "skills", "--persona", "saksee"])
    assert res_single.exit_code == 0
    assert "saksee" in res_single.output

    res_json = runner.invoke(main, ["eval", "skills", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert len(data) == 6


def test_eval_safety_all_and_single(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "safety"])
    assert result.exit_code == 0
    assert "[COMPLIANT]" in result.output

    res_single = runner.invoke(main, ["eval", "safety", "--persona", "sakjules"])
    assert res_single.exit_code == 0
    assert "sakjules" in res_single.output

    res_json = runner.invoke(main, ["eval", "safety", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert len(data) == 6


def test_eval_commands_failure_paths(runner: CliRunner) -> None:
    # 1. Fleet audit failure
    mock_fleet_fail = {
        "all_passed": False,
        "fleet_grade": "F",
        "fleet_average_score": 0.5,
        "personas_audited": 1,
        "scorecards": {
            "saktan": {
                "grade": "F",
                "composite_score": 0.5,
                "passed": False,
                "pillars": {
                    "readiness": {"score": 0.5, "passed": False},
                    "soul": {"score": 0.5, "passed": False},
                    "skills": {"score": 0.5, "passed": False},
                    "memory": {"score": 0.5, "passed": False},
                    "safety": {"score": 0.5, "passed": False},
                },
                "diagnostics": ["Fleet warning issue"],
            }
        },
    }
    with patch("sakthai.cli.eval.summarize_fleet_audit", return_value=mock_fleet_fail):
        res_table = runner.invoke(main, ["eval", "audit"])
        assert res_table.exit_code == 1
        assert "Fleet warning issue" in res_table.output

        res_json = runner.invoke(main, ["eval", "audit", "--json"])
        assert res_json.exit_code == 1

    # 2. Soul failure
    mock_soul_fail = {
        "saktan": {
            "aligned": False,
            "soul_score": 0.4,
            "checks_passed": 2,
            "checks_total": 7,
            "intro_line": None,
            "diagnostics": ["Soul warning issue"],
        }
    }
    with patch(
        "sakthai.cli.eval.evaluate_persona_soul_alignment", return_value=mock_soul_fail["saktan"]
    ):
        res_table = runner.invoke(main, ["eval", "soul"])
        assert res_table.exit_code == 1
        assert "Soul warning issue" in res_table.output

        res_json = runner.invoke(main, ["eval", "soul", "--json"])
        assert res_json.exit_code == 1

    # 3. Skills failure
    mock_skills_fail = {
        "saktan": {
            "healthy": False,
            "skills_score": 0.3,
            "valid_skills": 1,
            "total_skills": 5,
            "primary_skills": [],
            "diagnostics": ["Skill error warning"],
        }
    }
    with patch(
        "sakthai.cli.eval.evaluate_persona_skills_health", return_value=mock_skills_fail["saktan"]
    ):
        res_table = runner.invoke(main, ["eval", "skills"])
        assert res_table.exit_code == 1
        assert "Skill error warning" in res_table.output

        res_json = runner.invoke(main, ["eval", "skills", "--json"])
        assert res_json.exit_code == 1

    # 4. Safety failure
    mock_safety_fail = {
        "saktan": {
            "compliant": False,
            "safety_score": 0.5,
            "checks_passed": 2,
            "checks_total": 4,
            "diagnostics": ["Safety breach warning"],
        }
    }
    with patch(
        "sakthai.cli.eval.evaluate_persona_safety_compliance",
        return_value=mock_safety_fail["saktan"],
    ):
        res_table = runner.invoke(main, ["eval", "safety"])
        assert res_table.exit_code == 1
        assert "Safety breach warning" in res_table.output

        res_json = runner.invoke(main, ["eval", "safety", "--json"])
        assert res_json.exit_code == 1


def test_eval_summary_with_models_and_personas(runner: CliRunner) -> None:
    record_eval(_record(model="model-1", persona="sakthai"))
    record_eval(_record(model="model-2", persona="sakking"))
    res = runner.invoke(main, ["eval", "summary", "--all-personas"])
    assert res.exit_code == 0
    assert "# Per-model" in res.output
    assert "# Per-persona" in res.output
    assert "model-1" in res.output
    assert "sakthai" in res.output
