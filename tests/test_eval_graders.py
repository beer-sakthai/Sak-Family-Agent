"""Unit tests for evaluation_tasks.graders (CodeGrader, ModelGrader, BenchmarkSuite) and CLI."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from evaluation_tasks.graders import (
    DEFAULT_BENCHMARK_TASKS,
    BenchmarkSuite,
    BenchmarkSuiteResult,
    BenchmarkTask,
    CodeGrader,
    GradeResult,
    ModelGrader,
    load_benchmark_tasks,
)
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# =====================================================================
# 1. CodeGrader Tests
# =====================================================================


def test_code_grader_exact_match() -> None:
    # Exact match default
    res = CodeGrader.exact_match("  Bangkok  ", "Bangkok")
    assert isinstance(res, GradeResult)
    assert res.passed is True
    assert res.score == 1.0
    assert res.grader_type == "code"
    assert "Exact match passed" in res.feedback
    assert res.latency_s >= 0.0

    # Strip = False
    res_no_strip = CodeGrader.exact_match("  Bangkok  ", "Bangkok", strip=False)
    assert res_no_strip.passed is False
    assert res_no_strip.score == 0.0

    # Case insensitive
    res_case = CodeGrader.exact_match("bangkok", "Bangkok", case_sensitive=False)
    assert res_case.passed is True
    assert res_case.score == 1.0

    # Mismatch
    res_mismatch = CodeGrader.exact_match("Chiang Mai", "Bangkok")
    assert res_mismatch.passed is False
    assert res_mismatch.score == 0.0
    assert "Expected 'Bangkok', got 'Chiang Mai'" in res_mismatch.feedback


def test_code_grader_contains_match() -> None:
    # All present
    res = CodeGrader.contains_match("Hello Beer and SakThai", ["Beer", "SakThai"])
    assert res.passed is True
    assert res.score == 1.0
    assert "All expected substrings found" in res.feedback

    # Partial present
    res_partial = CodeGrader.contains_match("Hello Beer", ["Beer", "SakThai"])
    assert res_partial.passed is False
    assert res_partial.score == 0.5
    assert "Missing substrings: ['SakThai']" in res_partial.feedback

    # Empty expected substrings
    res_empty = CodeGrader.contains_match("Hello Beer", [])
    assert res_empty.passed is True
    assert res_empty.score == 1.0


def test_code_grader_regex_match() -> None:
    # Matching pattern
    res = CodeGrader.regex_match("run-12345", r"^run-\d+$")
    assert res.passed is True
    assert res.score == 1.0
    assert "Regex matched pattern" in res.feedback

    # Non-matching pattern
    res_no = CodeGrader.regex_match("invalid-run", r"^run-\d+$")
    assert res_no.passed is False
    assert res_no.score == 0.0
    assert "Output did not match pattern" in res_no.feedback

    # Invalid regex syntax
    res_inv = CodeGrader.regex_match("sample", r"[unclosed-group")
    assert res_inv.passed is False
    assert res_inv.score == 0.0
    assert "Invalid regex pattern" in res_inv.feedback


def test_code_grader_json_schema_valid() -> None:
    # Valid JSON without required keys
    res = CodeGrader.json_schema_valid('{"status": "ok", "count": 5}')
    assert res.passed is True
    assert res.score == 1.0

    # Valid JSON with required keys
    res_keys = CodeGrader.json_schema_valid('{"status": "ok", "count": 5}', ["status", "count"])
    assert res_keys.passed is True
    assert res_keys.score == 1.0

    # Missing one of two required keys
    res_missing = CodeGrader.json_schema_valid('{"status": "ok"}', ["status", "count"])
    assert res_missing.passed is False
    assert res_missing.score == 0.5
    assert "Missing required keys: ['count']" in res_missing.feedback

    # JSON wrapped in markdown code fence
    fence_json = '```json\n{\n  "status": "ok",\n  "count": 5\n}\n```'
    res_fence = CodeGrader.json_schema_valid(fence_json, ["status"])
    assert res_fence.passed is True
    assert res_fence.score == 1.0

    # Parsed JSON is not an object / dict
    res_array = CodeGrader.json_schema_valid("[1, 2, 3]", ["key"])
    assert res_array.passed is False
    assert res_array.score == 0.0
    assert "not an object/dictionary" in res_array.feedback

    # Invalid JSON syntax
    res_bad = CodeGrader.json_schema_valid("{not-json}")
    assert res_bad.passed is False
    assert res_bad.score == 0.0
    assert "JSON parse error" in res_bad.feedback


def test_code_grader_yaml_valid() -> None:
    # Valid YAML without required keys
    res = CodeGrader.yaml_valid("name: sakthai\nversion: 1.0")
    assert res.passed is True
    assert res.score == 1.0

    # Valid YAML with required keys
    res_keys = CodeGrader.yaml_valid("name: sakthai\nversion: 1.0", ["name", "version"])
    assert res_keys.passed is True
    assert res_keys.score == 1.0

    # Missing required keys
    res_missing = CodeGrader.yaml_valid("name: sakthai", ["name", "version"])
    assert res_missing.passed is False
    assert res_missing.score == 0.5
    assert "Missing required keys: ['version']" in res_missing.feedback

    # YAML wrapped in markdown fence
    fence_yaml = "```yaml\nname: sakthai\nversion: 1.0\n```"
    res_fence = CodeGrader.yaml_valid(fence_yaml, ["name"])
    assert res_fence.passed is True
    assert res_fence.score == 1.0

    # Non-dict YAML
    res_list = CodeGrader.yaml_valid("- item1\n- item2", ["key"])
    assert res_list.passed is False
    assert res_list.score == 0.0
    assert "not an object/dictionary" in res_list.feedback

    # Empty / comment-only YAML
    res_empty = CodeGrader.yaml_valid("# only a comment")
    assert res_empty.passed is False
    assert res_empty.score == 0.0

    # Invalid YAML syntax
    res_bad = CodeGrader.yaml_valid("key: [unclosed")
    assert res_bad.passed is False
    assert res_bad.score == 0.0
    assert "YAML parse error" in res_bad.feedback


def test_code_grader_numerical_range() -> None:
    # Within range
    res = CodeGrader.numerical_range("45.5", min_val=20.0, max_val=85.0)
    assert res.passed is True
    assert res.score == 1.0
    assert "within range [20.0, 85.0]" in res.feedback

    # Below min
    res_low = CodeGrader.numerical_range("15.0", min_val=20.0, max_val=85.0)
    assert res_low.passed is False
    assert res_low.score == 0.0
    assert "below minimum 20.0" in res_low.feedback

    # Above max
    res_high = CodeGrader.numerical_range("90.0", min_val=20.0, max_val=85.0)
    assert res_high.passed is False
    assert res_high.score == 0.0
    assert "above maximum 85.0" in res_high.feedback

    # Embedded in string
    res_text = CodeGrader.numerical_range(
        "The measured temperature is 50.2 C", min_val=20.0, max_val=85.0
    )
    assert res_text.passed is True
    assert res_text.score == 1.0

    # Non-numerical output
    res_none = CodeGrader.numerical_range("No numbers here", min_val=0.0, max_val=10.0)
    assert res_none.passed is False
    assert res_none.score == 0.0
    assert "Could not extract numerical value" in res_none.feedback


# =====================================================================
# 2. ModelGrader Tests
# =====================================================================


def test_model_grader_build_prompt() -> None:
    prompt = ModelGrader.build_grader_prompt(
        answer="CI/CD automates pipelines.",
        rubric="Must mention automation.",
        task="Explain CI/CD.",
    )
    assert "<task>\nExplain CI/CD.\n</task>" in prompt
    assert "<student_answer>\nCI/CD automates pipelines.\n</student_answer>" in prompt
    assert "<rubric>\nMust mention automation.\n</rubric>" in prompt
    assert "<thinking>" in prompt
    assert "<correctness>" in prompt


def test_model_grader_correctness_extraction() -> None:
    # Correct response with thinking
    def call_fn_correct(p: str) -> str:
        return (
            "<thinking>The student accurately explained CI/CD.</thinking>"
            "<correctness>correct</correctness>"
        )

    res = ModelGrader.grade(
        output="CI/CD automates deployment.",
        rubric="Must explain CI/CD.",
        call_fn=call_fn_correct,
    )
    assert res.passed is True
    assert res.score == 1.0
    assert res.grader_type == "model"
    assert "The student accurately explained CI/CD." in res.feedback

    # Incorrect response with thinking
    def call_fn_incorrect(p: str) -> str:
        return (
            "<thinking>The student did not address the question.</thinking>"
            "<correctness>incorrect</correctness>"
        )

    res_inc = ModelGrader.grade(
        output="Irrelevant text.",
        rubric="Must explain CI/CD.",
        call_fn=call_fn_incorrect,
    )
    assert res_inc.passed is False
    assert res_inc.score == 0.0
    assert "did not address the question" in res_inc.feedback


def test_model_grader_malformed_output_fallback() -> None:
    # Malformed output containing "correct" without XML tags
    def call_fn_loose_correct(p: str) -> str:
        return "Verdict: The student solution is completely correct."

    res = ModelGrader.grade(
        output="42",
        rubric="Must be 42.",
        call_fn=call_fn_loose_correct,
    )
    assert res.passed is True
    assert res.score == 1.0

    # Malformed output indicating incorrect
    def call_fn_loose_incorrect(p: str) -> str:
        return "The answer is incorrect and incomplete."

    res_inc = ModelGrader.grade(
        output="0",
        rubric="Must be 42.",
        call_fn=call_fn_loose_incorrect,
    )
    assert res_inc.passed is False
    assert res_inc.score == 0.0


def test_model_grader_default_dispatch_failure() -> None:
    # When call_fn is None and agent loop fails
    with patch("sakthai.agent.loop.run_agent", side_effect=RuntimeError("No API Key")):
        res = ModelGrader.grade(output="test", rubric="test", call_fn=None)
        assert res.passed is False
        assert res.score == 0.0
        assert "Model evaluation unavailable" in res.feedback


# =====================================================================
# 3. BenchmarkSuite Tests
# =====================================================================


def test_benchmark_suite_multi_task_run() -> None:
    tasks = [
        BenchmarkTask(
            id="task_exact",
            prompt="What is 2 + 2?",
            golden_answer="4",
            grader_type="code",
            metadata={"match_type": "exact"},
        ),
        BenchmarkTask(
            id="task_contains",
            prompt="Mention Beer and Jules.",
            golden_answer="Beer",
            grader_type="code",
            metadata={"match_type": "contains", "expected_substrings": ["Beer", "Jules"]},
        ),
        BenchmarkTask(
            id="task_human",
            prompt="Manual check prompt.",
            golden_answer="Golden human text",
            grader_type="human",
        ),
        BenchmarkTask(
            id="task_model",
            prompt="Explain automation.",
            golden_answer="",
            grader_type="model",
            rubric="Must mention automation.",
        ),
    ]

    def mock_generate(prompt: str) -> str:
        if "2 + 2" in prompt:
            return "4"
        if "Mention Beer" in prompt:
            return "Beer and Jules are here."
        if "Manual check" in prompt:
            return "Golden human text"
        return "<thinking>Good explanation.</thinking><correctness>correct</correctness>"

    suite = BenchmarkSuite(tasks=tasks, generate_fn=mock_generate)
    result = suite.run()

    assert isinstance(result, BenchmarkSuiteResult)
    assert result.total_tasks == 4
    assert result.passed_tasks == 4
    assert result.failed_tasks == 0
    assert result.accuracy == 1.0
    assert result.average_duration_s >= 0.0
    assert len(result.task_results) == 4

    # Test dictionary export
    d = result.to_dict()
    assert d["total_tasks"] == 4
    assert d["accuracy"] == 1.0

    # Test Markdown formatting
    md = result.format_markdown()
    assert "# Benchmark Suite Results" in md
    assert "- **Accuracy**: 100.0% (4/4)" in md
    assert "| task_exact | code | ✅ | 1.00 |" in md
    assert "| task_contains | code | ✅ | 1.00 |" in md
    assert "| task_human | human | ✅ | 1.00 |" in md
    assert "| task_model | model | ✅ | 1.00 |" in md


def test_benchmark_suite_partial_failure() -> None:
    tasks = [
        BenchmarkTask(id="t1", prompt="p1", golden_answer="A", grader_type="code"),
        BenchmarkTask(id="t2", prompt="p2", golden_answer="B", grader_type="code"),
    ]
    # Generator returns "A" for both
    suite = BenchmarkSuite(tasks=tasks)
    result = suite.run(tasks=tasks, generate_fn=lambda p: "A")
    assert result.total_tasks == 2
    assert result.passed_tasks == 1
    assert result.failed_tasks == 1
    assert result.accuracy == 0.5


def test_default_benchmark_tasks_and_loader() -> None:
    assert len(DEFAULT_BENCHMARK_TASKS) >= 5

    # Load default
    tasks_def = load_benchmark_tasks("default")
    assert len(tasks_def) == len(DEFAULT_BENCHMARK_TASKS)

    # Load from evaluation_tasks dataset
    tasks_soul = load_benchmark_tasks("soul_following")
    assert len(tasks_soul) >= 8
    assert any("SakThai" in t.prompt or "Aria" in t.prompt for t in tasks_soul)

    # Fallback when file doesn't exist
    tasks_unknown = load_benchmark_tasks("nonexistent_suite_xyz")
    assert len(tasks_unknown) == len(DEFAULT_BENCHMARK_TASKS)


# =====================================================================
# 4. CLI command `sakthai eval bench` Tests
# =====================================================================


def test_cli_eval_bench_markdown(runner: CliRunner) -> None:
    mock_result = BenchmarkSuiteResult(
        total_tasks=2,
        passed_tasks=2,
        failed_tasks=0,
        accuracy=1.0,
        average_duration_s=0.015,
        task_results=[
            {
                "task_id": "test_1",
                "grader_type": "code",
                "passed": True,
                "score": 1.0,
                "latency_s": 0.001,
                "feedback": "Passed exact match",
            },
            {
                "task_id": "test_2",
                "grader_type": "model",
                "passed": True,
                "score": 1.0,
                "latency_s": 0.014,
                "feedback": "Passed rubric",
            },
        ],
    )

    with patch.object(BenchmarkSuite, "run", return_value=mock_result):
        res = runner.invoke(main, ["eval", "bench"])
        assert res.exit_code == 0
        assert "# Benchmark Suite Results" in res.output
        assert "- **Accuracy**: 100.0% (2/2)" in res.output
        assert "| test_1 | code | ✅ | 1.00 |" in res.output


def test_cli_eval_bench_json(runner: CliRunner) -> None:
    mock_result = BenchmarkSuiteResult(
        total_tasks=1,
        passed_tasks=1,
        failed_tasks=0,
        accuracy=1.0,
        average_duration_s=0.01,
        task_results=[
            {
                "task_id": "t1",
                "grader_type": "code",
                "passed": True,
                "score": 1.0,
                "latency_s": 0.01,
                "feedback": "ok",
            }
        ],
    )

    with patch.object(BenchmarkSuite, "run", return_value=mock_result):
        res = runner.invoke(main, ["eval", "bench", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["total_tasks"] == 1
        assert data["accuracy"] == 1.0
        assert data["passed_tasks"] == 1


def test_cli_eval_bench_with_suite_and_persona(runner: CliRunner) -> None:
    mock_result = BenchmarkSuiteResult(
        total_tasks=1,
        passed_tasks=1,
        failed_tasks=0,
        accuracy=1.0,
        average_duration_s=0.005,
        task_results=[],
    )

    with patch.object(BenchmarkSuite, "run", return_value=mock_result):
        res = runner.invoke(
            main, ["eval", "bench", "--suite", "default", "--persona", "sakjules", "--json"]
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["total_tasks"] == 1


def test_cli_eval_bench_all_failed_exit_code(runner: CliRunner) -> None:
    mock_result = BenchmarkSuiteResult(
        total_tasks=2,
        passed_tasks=0,
        failed_tasks=2,
        accuracy=0.0,
        average_duration_s=0.01,
        task_results=[],
    )

    with patch.object(BenchmarkSuite, "run", return_value=mock_result):
        res = runner.invoke(main, ["eval", "bench"])
        assert res.exit_code == 1
