"""Tests for tool evaluation rubric, multi-trial benchmark, and CLI commands."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from sakthai.agent.eval import (
    TOOL_RUBRIC_CRITERIA,
    evaluate_persona_audit,
    evaluate_persona_tools_health,
    evaluate_tools_trials,
)
from sakthai.agent.tools import Tool
from sakthai.cli import main
from sakthai.config import PERSONA_NAMES


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_tool_rubric_criteria_constants() -> None:
    expected = (
        "schemas_valid",
        "descriptions_actionable",
        "handlers_callable",
        "names_valid",
        "argument_validation",
        "registry_integrity",
    )
    assert expected == TOOL_RUBRIC_CRITERIA


def test_evaluate_persona_tools_health_all_personas() -> None:
    for persona in PERSONA_NAMES:
        report = evaluate_persona_tools_health(persona)
        assert report["persona"] == persona
        assert report["healthy"] is True
        assert report["tools_score"] >= 0.95
        assert report["total_tools"] >= 19
        assert report["valid_tools"] == report["total_tools"]
        assert len(report["diagnostics"]) == 0
        for criterion in TOOL_RUBRIC_CRITERIA:
            assert report["dimensions_breakdown"][criterion] >= 19


def test_evaluate_persona_tools_health_default_all() -> None:
    report = evaluate_persona_tools_health(None)
    assert report["persona"] == "all"
    assert report["healthy"] is True
    assert report["tools_score"] == 1.0
    assert report["total_tools"] >= 19


def test_evaluate_persona_tools_health_unknown_persona_raises() -> None:
    with pytest.raises(ValueError, match="Unknown persona 'not_a_persona'"):
        evaluate_persona_tools_health("not_a_persona")


def test_evaluate_persona_tools_health_detects_malformed_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sakthai.agent.registry import ToolRegistry

    # Create a registry with deliberately broken tools
    broken_tools = [
        Tool(
            name="Bad_Name",  # not snake_case
            description="short",  # < 20 chars
            input_schema={"type": "invalid"},  # not object
            handler="not_callable",  # type: ignore[arg-type]
        ),
        Tool(
            name="missing_req_test",
            description="A valid description of the tool behavior.",
            input_schema={
                "type": "object",
                "properties": {"req": {"type": "string"}},
                "required": ["req"],
            },
            handler=lambda args, store: "ok",
        ),
    ]

    monkeypatch.setattr(
        "sakthai.agent.registry.builtin_registry",
        lambda: ToolRegistry(broken_tools),
    )

    report = evaluate_persona_tools_health("sakthai")
    assert report["healthy"] is False
    assert report["tools_score"] < 1.0
    assert len(report["diagnostics"]) > 0
    # Missing core tools diagnostic should also be present
    assert any("Missing core built-in tools" in d for d in report["diagnostics"])


def test_evaluate_tools_trials_benchmark() -> None:
    trials_res = evaluate_tools_trials(trials=5)
    assert trials_res["trials"] == 5
    assert trials_res["target"] == "ALL PERSONAS"
    assert trials_res["consistency"] == 1.0
    assert trials_res["deterministic"] is True
    assert trials_res["all_healthy"] is True
    assert trials_res["status"] == "HEALTHY"

    stats = trials_res["latency_stats"]
    assert stats["avg_ms"] >= 0.0
    assert stats["min_ms"] <= stats["max_ms"]
    assert stats["jitter_ms"] >= 0.0
    assert len(trials_res["trial_history"]) == 5


def test_evaluate_tools_trials_specific_persona() -> None:
    trials_res = evaluate_tools_trials(persona="sakking", trials=3)
    assert trials_res["trials"] == 3
    assert trials_res["target"] == "sakking"
    assert trials_res["consistency"] == 1.0
    assert trials_res["deterministic"] is True


def test_evaluate_tools_trials_unknown_persona_raises() -> None:
    with pytest.raises(ValueError, match="Unknown persona"):
        evaluate_tools_trials(persona="unknown_bot", trials=2)


def test_audit_includes_tools_pillar() -> None:
    audit = evaluate_persona_audit("sakthai")
    assert "tools" in audit["pillars"]
    tools_pillar = audit["pillars"]["tools"]
    assert tools_pillar["score"] == 1.0
    assert tools_pillar["passed"] is True
    assert tools_pillar["total"] >= 19
    assert tools_pillar["valid"] >= 19
    assert audit["grade"] in ("A+", "A")


# ---------------------------------------------------------------------------
# CLI Command Tests: `sakthai eval tools`
# ---------------------------------------------------------------------------


def test_cli_eval_tools_text_all(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools"])
    assert result.exit_code == 0
    assert "# Sak Family Tool Health & Schema Evaluation" in result.output
    for persona in PERSONA_NAMES:
        assert persona in result.output
        assert "score=100%" in result.output


def test_cli_eval_tools_detailed(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "--detailed"])
    assert result.exit_code == 0
    assert "6-factor rubric: schemas_valid=" in result.output
    assert "descriptions_actionable=" in result.output
    assert "handlers_callable=" in result.output


def test_cli_eval_tools_single_persona(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "--persona", "sakjules"])
    assert result.exit_code == 0
    assert "sakjules" in result.output
    assert "sakthai" not in result.output


def test_cli_eval_tools_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "sakthai" in data
    assert data["sakthai"]["healthy"] is True
    assert data["sakthai"]["tools_score"] == 1.0
    assert data["sakthai"]["valid_tools"] >= 19


def test_cli_eval_tools_benchmark_trials(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "-t", "3"])
    assert result.exit_code == 0
    assert "# Sak Family Tools Evaluation — 3 Trials Benchmark" in result.output
    assert "Consistency:  100% (deterministic)" in result.output
    assert "Fleet Status: [HEALTHY]" in result.output


def test_cli_eval_tools_benchmark_trials_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "-t", "2", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["trials"] == 2
    assert data["consistency"] == 1.0
    assert data["status"] == "HEALTHY"
