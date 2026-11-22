"""Tests for tool evaluation rubric, multi-trial benchmark, and CLI commands."""

from __future__ import annotations

import json
from typing import Any

import pytest
from click.testing import CliRunner

from sakthai.agent.eval import (
    TOOL_RUBRIC_CRITERIA,
    ToolBenchmarkMetrics,
    ToolBenchmarkResult,
    _extract_xml_tag,
    evaluate_persona_audit,
    evaluate_persona_tools_health,
    evaluate_tools_benchmark,
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


# ---------------------------------------------------------------------------
# Dynamic Tool Evaluation & Benchmark Tests (Anthropic Cookbook Pattern)
# ---------------------------------------------------------------------------


def test_extract_xml_tag() -> None:
    # Basic extraction
    text = "<summary>Task summary text</summary><feedback>Very good</feedback>"
    assert _extract_xml_tag(text, "summary") == "Task summary text"
    assert _extract_xml_tag(text, "feedback") == "Very good"

    # Multi-line extraction with whitespace stripping
    multiline = """
    <response>
        Line 1
        Line 2
    </response>
    """
    assert _extract_xml_tag(multiline, "response") == "Line 1\n        Line 2"

    # Case insensitivity
    caps = "<SUMMARY>Capitalized Tag</SUMMARY>"
    assert _extract_xml_tag(caps, "summary") == "Capitalized Tag"

    # Empty tag
    empty = "<summary></summary>"
    assert _extract_xml_tag(empty, "summary") == ""

    # Missing tag
    assert _extract_xml_tag(text, "nonexistent") == ""

    # None or empty string
    assert _extract_xml_tag("", "summary") == ""
    assert _extract_xml_tag(None, "summary") == ""


def test_tool_benchmark_metrics() -> None:
    metrics = ToolBenchmarkMetrics(tool_name="test_tool")
    assert metrics.call_count == 0
    assert metrics.success_count == 0
    assert metrics.failure_count == 0
    assert metrics.avg_duration_s == 0.0
    assert metrics.success_rate == 0.0

    # Record success
    metrics.record(duration_s=0.04, success=True)
    assert metrics.call_count == 1
    assert metrics.success_count == 1
    assert metrics.failure_count == 0
    assert metrics.avg_duration_s == 0.04
    assert metrics.success_rate == 1.0

    # Record failure with error
    metrics.record(duration_s=0.06, success=False, error="Invalid arguments")
    assert metrics.call_count == 2
    assert metrics.success_count == 1
    assert metrics.failure_count == 1
    assert metrics.avg_duration_s == 0.05
    assert metrics.success_rate == 0.5
    assert metrics.errors == ["Invalid arguments"]

    # to_dict representation
    d = metrics.to_dict()
    assert d["tool_name"] == "test_tool"
    assert d["call_count"] == 2
    assert d["success_count"] == 1
    assert d["failure_count"] == 1
    assert d["success_rate"] == 0.5
    assert d["avg_duration_s"] == 0.05
    assert d["errors"] == ["Invalid arguments"]


def test_tool_benchmark_result() -> None:
    res = ToolBenchmarkResult(
        task_id="task_1",
        tool_name="learn",
        success=True,
        duration_s=0.012,
        tool_calls=1,
        summary="Learned fact",
        feedback="Clean run",
        response="Success",
    )
    assert res.task_id == "task_1"
    assert res.tool_name == "learn"
    assert res.success is True
    assert res.duration_s == 0.012
    assert res.summary == "Learned fact"

    d = res.to_dict()
    assert d["task_id"] == "task_1"
    assert d["success"] is True
    assert d["duration_s"] == 0.012
    assert d["summary"] == "Learned fact"
    assert d["feedback"] == "Clean run"
    assert d["response"] == "Success"


def test_evaluate_tools_benchmark_default_tasks() -> None:
    bench = evaluate_tools_benchmark(persona="sakthai")
    assert bench["persona"] == "sakthai"
    assert bench["healthy"] is True
    assert bench["accuracy"] == 1.0
    assert bench["successful_tasks"] == 4
    assert bench["failed_tasks"] == 0
    assert bench["total_tasks"] == 4
    assert bench["total_tool_calls"] == 4
    assert bench["average_tool_calls"] == 1.0
    assert bench["average_duration_s"] >= 0.0

    # Per-tool metrics contains default tools
    metrics = bench["per_tool_metrics"]
    for t_name in ("learn", "recall", "search", "read_file"):
        assert t_name in metrics
        assert metrics[t_name]["call_count"] == 1
        assert metrics[t_name]["success_rate"] == 1.0

    # Markdown report formatting
    report = bench["report"]
    assert "# Tool Evaluation Benchmark Report — SAKTHAI" in report
    assert "## Summary Statistics" in report
    assert "- **Total Tasks**: 4" in report
    assert "- **Accuracy**: 100.0%" in report
    assert "## Per-Tool Metrics" in report
    assert "## Task Results" in report
    assert "### [PASS] `task_learn_fact`" in report


def test_evaluate_tools_benchmark_all_personas() -> None:
    for persona in PERSONA_NAMES:
        bench = evaluate_tools_benchmark(persona=persona)
        assert bench["persona"] == persona
        assert bench["healthy"] is True
        assert bench["accuracy"] == 1.0


def test_evaluate_tools_benchmark_unknown_persona_raises() -> None:
    with pytest.raises(ValueError, match="Unknown persona 'invalid_persona'"):
        evaluate_tools_benchmark(persona="invalid_persona")


def test_evaluate_tools_benchmark_custom_tasks_and_xml_parsing() -> None:
    custom_tasks = [
        {
            "task_id": "custom_multi_call",
            "tool_calls": [
                {
                    "tool": "learn",
                    "args": {"value": "Custom benchmark fact", "key": "c_fact"},
                },
                {"tool": "recall", "args": {"limit": 2}},
            ],
            "response": (
                "<summary>Multi-tool call succeeded</summary>"
                "<feedback>Learned and recalled in sequence</feedback>"
                "<response>Sequence done</response>"
            ),
        },
    ]

    bench = evaluate_tools_benchmark(persona="sakthai", sample_tasks=custom_tasks)
    assert bench["healthy"] is True
    assert bench["accuracy"] == 1.0
    assert bench["total_tasks"] == 1
    assert bench["total_tool_calls"] == 2
    assert bench["average_tool_calls"] == 2.0

    result = bench["results"][0]
    assert result["task_id"] == "custom_multi_call"
    assert result["summary"] == "Multi-tool call succeeded"
    assert result["feedback"] == "Learned and recalled in sequence"
    assert result["response"] == "Sequence done"
    assert result["per_tool_counts"] == {"learn": 1, "recall": 1}


def test_evaluate_tools_benchmark_failing_task() -> None:
    tasks_with_failure = [
        {
            "task_id": "missing_tool_task",
            "tool": "nonexistent_ghost_tool",
            "args": {},
        },
        {
            "task_id": "invalid_args_task",
            "tool": "learn",
            "args": {},  # missing required "value"
        },
    ]

    bench = evaluate_tools_benchmark(persona="sakthai", sample_tasks=tasks_with_failure)
    assert bench["healthy"] is False
    assert bench["accuracy"] == 0.0
    assert bench["successful_tasks"] == 0
    assert bench["failed_tasks"] == 2
    assert len(bench["results"]) == 2

    # Verify error reporting
    r0 = bench["results"][0]
    assert r0["success"] is False
    assert any("not found in registry" in err for err in r0["errors"])

    r1 = bench["results"][1]
    assert r1["success"] is False
    assert any("Invalid arguments" in err for err in r1["errors"])


def test_cli_eval_tools_bench(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "--bench"])
    assert result.exit_code == 0
    assert "# Tool Evaluation Benchmark Report — SAKTHAI" in result.output
    assert "## Summary Statistics" in result.output
    assert "**Accuracy**: 100.0%" in result.output
    assert "`learn`" in result.output
    assert "`recall`" in result.output


def test_cli_eval_tools_bench_short_flag(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "-b", "--persona", "sakjules"])
    assert result.exit_code == 0
    assert "# Tool Evaluation Benchmark Report — SAKJULES" in result.output
    assert "`learn`" in result.output


def test_cli_eval_tools_bench_json(runner: CliRunner) -> None:
    result = runner.invoke(main, ["eval", "tools", "--bench", "--json", "--persona", "sakking"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["persona"] == "sakking"
    assert data["healthy"] is True
    assert data["accuracy"] == 1.0
    assert data["total_tasks"] == 4
    assert "report" in data
    assert "results" in data
    assert "per_tool_metrics" in data


def test_evaluate_tools_benchmark_empty_task_and_exception_handling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 1. Task with no tool calls and no XML tags
    bench = evaluate_tools_benchmark(
        persona="sakthai",
        sample_tasks=[
            {"task_id": "empty_task"},
            {
                "task_id": "simple_learn_no_xml",
                "tool": "learn",
                "args": {"value": "Simple value", "key": "k_simple"},
            },
        ],
    )
    assert bench["healthy"] is True
    assert bench["accuracy"] == 1.0
    assert bench["results"][0]["tool_name"] == "none"
    assert "Task empty_task completed" in bench["results"][0]["summary"]
    assert "All tools executed successfully" in bench["results"][1]["feedback"]

    # 2. Tool whose safe_call raises unexpected exception
    from sakthai.agent.tools import Tool

    exploding_tool = Tool(
        name="exploding_tool",
        description="A tool that unexpectedly throws an unhandled exception.",
        input_schema={"type": "object"},
        handler=lambda args, store: "ok",
    )

    orig_safe_call = Tool.safe_call

    def explode(self: Any, args: Any, store: Any) -> Any:
        if self.name == "exploding_tool":
            raise RuntimeError("Boom!")
        return orig_safe_call(self, args, store)

    monkeypatch.setattr(Tool, "safe_call", explode)

    from sakthai.agent.registry import ToolRegistry

    monkeypatch.setattr(
        "sakthai.agent.registry.builtin_registry",
        lambda: ToolRegistry([exploding_tool]),
    )

    bench_err = evaluate_tools_benchmark(
        persona="sakthai",
        sample_tasks=[
            {
                "task_id": "exploding_task",
                "tool": "exploding_tool",
                "args": {},
            }
        ],
    )
    assert bench_err["healthy"] is False
    assert bench_err["accuracy"] == 0.0
    assert any(
        "Exception executing exploding_tool: Boom!" in err
        for err in bench_err["results"][0]["errors"]
    )
    assert "### [FAIL] `exploding_task`" in bench_err["report"]


def test_cli_eval_tools_bench_failure_exits_one(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock evaluate_tools_benchmark to return healthy=False
    mock_unhealthy = {
        "persona": "sakthai",
        "healthy": False,
        "report": "Unhealthy benchmark failure report",
    }
    monkeypatch.setattr(
        "sakthai.cli.eval.evaluate_tools_benchmark", lambda **kwargs: mock_unhealthy
    )

    # Text mode
    res_text = runner.invoke(main, ["eval", "tools", "--bench"])
    assert res_text.exit_code == 1
    assert "Unhealthy benchmark failure report" in res_text.output

    # JSON mode
    res_json = runner.invoke(main, ["eval", "tools", "--bench", "--json"])
    assert res_json.exit_code == 1
    data = json.loads(res_json.output)
    assert data["healthy"] is False
