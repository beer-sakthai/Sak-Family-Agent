"""Tests for Runtime Evaluator-Optimizer Engine and CLI integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from sakthai.agent.optimizer import (
    DEFAULT_MAX_OPTIMIZER_ITERATIONS,
    EvaluatorOptimizer,
    OptimizationIteration,
    OptimizationResult,
    _extract_xml_tag,
    optimize_solution,
)
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_extract_xml_tag() -> None:
    text = "<thought>Thinking process</thought><response>Final answer</response>"
    assert _extract_xml_tag(text, "thought") == "Thinking process"
    assert _extract_xml_tag(text, "response") == "Final answer"
    assert _extract_xml_tag(text, "nonexistent") == ""
    assert _extract_xml_tag("", "thought") == ""
    assert _extract_xml_tag(None, "thought") == ""

    # Case-insensitivity & multiline
    multiline = "<STATUS>\n  PASS\n</STATUS>\n<Feedback>\nLine 1\nLine 2\n</Feedback>"
    assert _extract_xml_tag(multiline, "status") == "PASS"
    assert _extract_xml_tag(multiline, "feedback") == "Line 1\nLine 2"


def test_dataclasses_and_serialization() -> None:
    it = OptimizationIteration(
        iteration=1,
        thoughts="Let's solve step by step",
        response="def add(a, b): return a + b",
        status="PASS",
        feedback="Looks good",
        latency_s=0.42,
    )
    assert it.iteration == 1
    assert it.thoughts == "Let's solve step by step"
    assert it.response == "def add(a, b): return a + b"
    assert it.status == "PASS"
    assert it.feedback == "Looks good"
    assert it.latency_s == 0.42

    d = it.to_dict()
    assert d["iteration"] == 1
    assert d["status"] == "PASS"
    assert d["latency_s"] == 0.42

    res = OptimizationResult(
        final_response="def add(a, b): return a + b",
        status="PASS",
        iterations=1,
        history=[it],
        total_duration_s=0.45,
    )
    assert res.final_response == "def add(a, b): return a + b"
    assert res.status == "PASS"
    assert res.iterations == 1
    assert len(res.history) == 1
    assert res.total_duration_s == 0.45

    res_d = res.to_dict()
    assert res_d["final_response"] == "def add(a, b): return a + b"
    assert res_d["status"] == "PASS"
    assert len(res_d["history"]) == 1


def test_optimizer_init_defaults_and_custom() -> None:
    opt = EvaluatorOptimizer()
    assert opt.max_iterations == DEFAULT_MAX_OPTIMIZER_ITERATIONS
    assert opt.call_fn is None
    assert opt.model is None
    assert opt.provider is None
    assert opt.evaluator_prompt is None
    assert opt.generator_prompt is None

    # Negative max_iterations clamped to 0
    opt_neg = EvaluatorOptimizer(max_iterations=-5)
    assert opt_neg.max_iterations == 0


def test_generate_standard_tags() -> None:
    def fake_call(prompt: str) -> str:
        assert "Write a python function" in prompt
        return (
            "<thought>Let's write a concise function</thought>\n"
            "<response>def hello(): return 'hello'</response>"
        )

    opt = EvaluatorOptimizer(call_fn=fake_call)
    response, thoughts = opt.generate("Write a python function")
    assert response == "def hello(): return 'hello'"
    assert thoughts == "Let's write a concise function"


def test_generate_alternative_tags() -> None:
    def fake_call(prompt: str) -> str:
        return (
            "<thoughts>Alternative thoughts tag</thoughts>\n"
            "<solution>def answer(): return 42</solution>"
        )

    opt = EvaluatorOptimizer(call_fn=fake_call)
    response, thoughts = opt.generate("Calculate answer")
    assert response == "def answer(): return 42"
    assert thoughts == "Alternative thoughts tag"


def test_generate_malformed_fallbacks() -> None:
    # 1. Plain text without any XML tags
    opt1 = EvaluatorOptimizer(call_fn=lambda p: "Plain text solution without tags")
    resp1, th1 = opt1.generate("Any task")
    assert resp1 == "Plain text solution without tags"
    assert th1 == ""

    # 2. Only thoughts tag, no response tag
    opt2 = EvaluatorOptimizer(
        call_fn=lambda p: "<thought>Internal reasoning</thought>\ndef solve(): return True"
    )
    resp2, th2 = opt2.generate("Any task")
    assert resp2 == "def solve(): return True"
    assert th2 == "Internal reasoning"

    # 3. Empty string output
    opt3 = EvaluatorOptimizer(call_fn=lambda p: "")
    resp3, th3 = opt3.generate("Empty task")
    assert resp3 == ""
    assert th3 == ""


def test_generate_custom_prompt_templates() -> None:
    captured_prompts: list[str] = []

    def fake_call(prompt: str) -> str:
        captured_prompts.append(prompt)
        return "<response>Done</response><thought>Fine</thought>"

    # Template with {task} and {context}
    tmpl = "Custom Generator\nTask is: {task}\nPrior: {context}"
    opt = EvaluatorOptimizer(generator_prompt=tmpl, call_fn=fake_call)
    resp, th = opt.generate("Fix bug", context="Stacktrace line 4")
    assert resp == "Done"
    assert th == "Fine"
    assert "Task is: Fix bug" in captured_prompts[-1]
    assert "Prior: Stacktrace line 4" in captured_prompts[-1]

    # Template without placeholders
    plain_tmpl = "You are a specialized code generator."
    opt_plain = EvaluatorOptimizer(generator_prompt=plain_tmpl, call_fn=fake_call)
    opt_plain.generate("Add logging", context="Previous iteration feedback")
    assert "You are a specialized code generator." in captured_prompts[-1]
    assert "Task:\nAdd logging" in captured_prompts[-1]
    assert "Context and Feedback:\nPrevious iteration feedback" in captured_prompts[-1]


def test_evaluate_standard_tags() -> None:
    # PASS
    opt_pass = EvaluatorOptimizer(
        call_fn=lambda p: "<status>PASS</status><feedback>All tests passed.</feedback>"
    )
    status, feedback = opt_pass.evaluate("Task 1", "Code 1")
    assert status == "PASS"
    assert feedback == "All tests passed."

    # NEEDS_IMPROVEMENT
    opt_imp = EvaluatorOptimizer(
        call_fn=lambda p: (
            "<status>NEEDS_IMPROVEMENT</status><feedback>Missing type annotations.</feedback>"
        )
    )
    status, feedback = opt_imp.evaluate("Task 2", "Code 2")
    assert status == "NEEDS_IMPROVEMENT"
    assert feedback == "Missing type annotations."

    # FAIL
    opt_fail = EvaluatorOptimizer(
        call_fn=lambda p: "<status>FAIL</status><feedback>Syntax error in code.</feedback>"
    )
    status, feedback = opt_fail.evaluate("Task 3", "Code 3")
    assert status == "FAIL"
    assert feedback == "Syntax error in code."


def test_evaluate_status_normalization_and_fallbacks() -> None:
    # Case normalization
    opt1 = EvaluatorOptimizer(call_fn=lambda p: "<status>pass</status><feedback>Good</feedback>")
    assert opt1.evaluate("T", "C")[0] == "PASS"

    opt2 = EvaluatorOptimizer(
        call_fn=lambda p: "<status>needs improvement</status><feedback>Fix</feedback>"
    )
    assert opt2.evaluate("T", "C")[0] == "NEEDS_IMPROVEMENT"

    opt3 = EvaluatorOptimizer(call_fn=lambda p: "<status>fail</status><feedback>Broken</feedback>")
    assert opt3.evaluate("T", "C")[0] == "FAIL"

    # Fallback when status tag is missing
    opt_no_tag_pass = EvaluatorOptimizer(
        call_fn=lambda p: "Status: PASS\nFeedback: The code meets all requirements."
    )
    status_p, fb_p = opt_no_tag_pass.evaluate("T", "C")
    assert status_p == "PASS"
    assert "meets all requirements" in fb_p

    opt_no_tag_fail = EvaluatorOptimizer(
        call_fn=lambda p: "Status: FAIL\nFeedback: Implementation refused."
    )
    status_f, fb_f = opt_no_tag_fail.evaluate("T", "C")
    assert status_f == "FAIL"

    opt_no_tag_imp = EvaluatorOptimizer(
        call_fn=lambda p: "Status: NEEDS_IMPROVEMENT\nFeedback: Needs unit test."
    )
    status_i, fb_i = opt_no_tag_imp.evaluate("T", "C")
    assert status_i == "NEEDS_IMPROVEMENT"

    # Fallback when completely unparseable text
    opt_unknown = EvaluatorOptimizer(call_fn=lambda p: "I am not sure about this.")
    status_u, fb_u = opt_unknown.evaluate("T", "C")
    assert status_u == "NEEDS_IMPROVEMENT"
    assert fb_u == "I am not sure about this."


def test_evaluate_custom_prompt_and_criteria() -> None:
    captured_prompts: list[str] = []

    def fake_call(prompt: str) -> str:
        captured_prompts.append(prompt)
        return "<status>PASS</status><feedback>Verified</feedback>"

    # Custom prompt with {task}, {content}, {criteria}
    tmpl = "Evaluator\nTask: {task}\nSolution: {content}\nCriteria: {criteria}"
    opt = EvaluatorOptimizer(evaluator_prompt=tmpl, call_fn=fake_call)
    status, feedback = opt.evaluate("Refactor", "def code(): pass", criteria="Must be O(1)")
    assert status == "PASS"
    assert feedback == "Verified"
    assert "Task: Refactor" in captured_prompts[-1]
    assert "Solution: def code(): pass" in captured_prompts[-1]
    assert "Criteria: Must be O(1)" in captured_prompts[-1]

    # Custom prompt without format placeholders
    plain_tmpl = "You are a code judge."
    opt_plain = EvaluatorOptimizer(evaluator_prompt=plain_tmpl, call_fn=fake_call)
    opt_plain.evaluate("Task B", "Solution B", criteria="Coverage >= 96%")
    assert "You are a code judge." in captured_prompts[-1]
    assert "Task:\nTask B" in captured_prompts[-1]
    assert "Proposed Solution:\nSolution B" in captured_prompts[-1]
    assert "Evaluation Criteria:\nCoverage >= 96%" in captured_prompts[-1]


def test_optimize_single_iteration_pass() -> None:
    def fake_call(prompt: str) -> str:
        if "You are an expert solution generator" in prompt:
            return "<thought>Immediate perfect solution</thought><response>def square(x): return x * x</response>"
        return "<status>PASS</status><feedback>Perfect implementation.</feedback>"

    opt = EvaluatorOptimizer(call_fn=fake_call, max_iterations=3)
    result = opt.optimize("Implement square function")

    assert result.status == "PASS"
    assert result.iterations == 1
    assert result.final_response == "def square(x): return x * x"
    assert len(result.history) == 1
    assert result.history[0].iteration == 1
    assert result.history[0].status == "PASS"
    assert result.history[0].thoughts == "Immediate perfect solution"
    assert result.history[0].feedback == "Perfect implementation."
    assert result.total_duration_s >= 0.0


def test_optimize_multi_iteration_improvement() -> None:
    call_count = 0
    contexts_received: list[str] = []

    def fake_call(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if "You are an expert solution generator" in prompt:
            if "Context and Feedback" in prompt:
                contexts_received.append(prompt)
                return "<thought>Fixing edge case as requested</thought><response>def divide(a, b): return None if b == 0 else a / b</response>"
            return "<thought>First attempt</thought><response>def divide(a, b): return a / b</response>"
        else:
            # Evaluator call
            if "if b == 0" in prompt:
                return "<status>PASS</status><feedback>ZeroDivisionError now handled.</feedback>"
            return "<status>NEEDS_IMPROVEMENT</status><feedback>Handle zero division.</feedback>"

    opt = EvaluatorOptimizer(call_fn=fake_call, max_iterations=3)
    result = opt.optimize("Implement divide function")

    assert result.status == "PASS"
    assert result.iterations == 2
    assert "return None if b == 0" in result.final_response
    assert len(result.history) == 2
    assert result.history[0].status == "NEEDS_IMPROVEMENT"
    assert result.history[0].feedback == "Handle zero division."
    assert result.history[1].status == "PASS"
    assert len(contexts_received) == 1
    assert "Handle zero division." in contexts_received[0]


def test_optimize_max_iterations_bound() -> None:
    def fake_call(prompt: str) -> str:
        if "You are an expert solution generator" in prompt:
            return "<thought>Attempt</thought><response>Attempt code</response>"
        return "<status>NEEDS_IMPROVEMENT</status><feedback>Still not good enough.</feedback>"

    opt = EvaluatorOptimizer(call_fn=fake_call, max_iterations=3)
    result = opt.optimize("Hard problem")

    assert result.status == "MAX_ITERATIONS"
    assert result.iterations == 3
    assert len(result.history) == 3
    assert all(it.status == "NEEDS_IMPROVEMENT" for it in result.history)


def test_optimize_immediate_fail() -> None:
    def fake_call(prompt: str) -> str:
        if "You are an expert solution generator" in prompt:
            return "<thought>Pondering</thought><response>I cannot do this.</response>"
        return "<status>FAIL</status><feedback>Task refused.</feedback>"

    opt = EvaluatorOptimizer(call_fn=fake_call, max_iterations=3)
    result = opt.optimize("Impossible task")

    assert result.status == "FAIL"
    assert result.iterations == 1
    assert result.final_response == "I cannot do this."
    assert result.history[0].status == "FAIL"


def test_optimize_zero_max_iterations() -> None:
    opt = EvaluatorOptimizer(max_iterations=0)
    result = opt.optimize("Do nothing")
    assert result.status == "MAX_ITERATIONS"
    assert result.iterations == 0
    assert result.final_response == ""
    assert result.history == []


def test_optimize_initial_context() -> None:
    captured: list[str] = []

    def fake_call(prompt: str) -> str:
        captured.append(prompt)
        if "You are an expert solution generator" in prompt:
            return "<thought>T</thought><response>R</response>"
        return "<status>PASS</status><feedback>OK</feedback>"

    opt = EvaluatorOptimizer(call_fn=fake_call, max_iterations=2)
    opt.optimize("Task with context", initial_context="Use numpy arrays only.")
    assert "Use numpy arrays only." in captured[0]


def test_optimize_solution_helper() -> None:
    def fake_call(prompt: str) -> str:
        if "You are an expert solution generator" in prompt:
            return "<thought>Th</thought><response>Solution</response>"
        return "<status>PASS</status><feedback>Passed</feedback>"

    result = optimize_solution(
        "Build widget",
        criteria="Must be fast",
        max_iterations=2,
        call_fn=fake_call,
    )
    assert isinstance(result, OptimizationResult)
    assert result.status == "PASS"
    assert result.final_response == "Solution"
    assert result.iterations == 1


def test_call_fn_default_run_agent_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_run = MagicMock()
    mock_run.return_value.text = "<response>Mocked Agent Response</response>"
    monkeypatch.setattr("sakthai.agent.loop.run_agent", mock_run)

    opt = EvaluatorOptimizer(model="test-model", provider="anthropic")
    raw = opt._call("Test prompt")
    assert raw == "<response>Mocked Agent Response</response>"
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args.kwargs
    assert call_kwargs["model"] == "test-model"
    assert call_kwargs["provider"] == "anthropic"
    assert call_kwargs["fast"] is True
    assert call_kwargs["stateless"] is True
    assert call_kwargs["tools"] == ()


def test_cli_optimize_flag_single_pass(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_iteration = OptimizationIteration(
        iteration=1,
        thoughts="Let me write the function",
        response="def add(a, b): return a + b",
        status="PASS",
        feedback="Code is clean and correct.",
        latency_s=0.25,
    )
    fake_result = OptimizationResult(
        final_response="def add(a, b): return a + b",
        status="PASS",
        iterations=1,
        history=[fake_iteration],
        total_duration_s=0.30,
    )

    mock_optimize = MagicMock(return_value=fake_result)
    monkeypatch.setattr("sakthai.agent.optimizer.optimize_solution", mock_optimize)

    res = runner.invoke(
        main,
        ["run", "--optimize", "Implement add", "--criteria", "must have type annotations"],
    )
    assert res.exit_code == 0
    assert "--- Iteration 1 [PASS]" in res.output
    assert "Thoughts:\nLet me write the function" in res.output
    assert "Candidate Solution:\ndef add(a, b): return a + b" in res.output
    assert "Feedback:\nCode is clean and correct." in res.output
    assert "=== Final Solution [PASS]" in res.output
    assert "def add(a, b): return a + b" in res.output

    mock_optimize.assert_called_once_with(
        task="Implement add",
        criteria="must have type annotations",
        max_iterations=3,
        model="claude-opus-4-8",
        provider=None,
    )


def test_cli_optimize_flag_multi_iteration(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    it1 = OptimizationIteration(
        iteration=1,
        thoughts="Try 1",
        response="resp 1",
        status="NEEDS_IMPROVEMENT",
        feedback="Fix format",
        latency_s=0.2,
    )
    it2 = OptimizationIteration(
        iteration=2,
        thoughts="Try 2",
        response="resp 2",
        status="PASS",
        feedback="Looks good",
        latency_s=0.2,
    )
    res_obj = OptimizationResult(
        final_response="resp 2",
        status="PASS",
        iterations=2,
        history=[it1, it2],
        total_duration_s=0.45,
    )

    monkeypatch.setattr("sakthai.agent.optimizer.optimize_solution", lambda **kw: res_obj)

    res = runner.invoke(main, ["run", "--optimize", "Task"])
    assert res.exit_code == 0
    assert "--- Iteration 1 [NEEDS_IMPROVEMENT]" in res.output
    assert "--- Iteration 2 [PASS]" in res.output
    assert "=== Final Solution [PASS]" in res.output
    assert "resp 2" in res.output


def test_cli_optimize_custom_iterations(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_optimize = MagicMock(
        return_value=OptimizationResult(
            final_response="out", status="PASS", iterations=1, history=[], total_duration_s=0.1
        )
    )
    monkeypatch.setattr("sakthai.agent.optimizer.optimize_solution", mock_optimize)

    res = runner.invoke(main, ["run", "--optimize", "--max-iterations", "5", "Task"])
    assert res.exit_code == 0
    assert mock_optimize.call_args.kwargs["max_iterations"] == 5


def test_cli_optimize_keyboard_interrupt(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def raise_interrupt(**kw: Any) -> Any:
        raise KeyboardInterrupt()

    monkeypatch.setattr("sakthai.agent.optimizer.optimize_solution", raise_interrupt)

    res = runner.invoke(main, ["run", "--optimize", "Task"])
    assert res.exit_code == 130
    assert "Interrupted." in res.output


def test_cli_optimize_exception(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_error(**kw: Any) -> Any:
        raise RuntimeError("LLM provider down")

    monkeypatch.setattr("sakthai.agent.optimizer.optimize_solution", raise_error)

    res = runner.invoke(main, ["run", "--optimize", "Task"])
    assert res.exit_code != 0
    assert "LLM provider down" in res.output


def test_generate_custom_prompt_key_error_fallback() -> None:
    captured: list[str] = []
    opt = EvaluatorOptimizer(
        generator_prompt="Custom {task} {unmatched}",
        call_fn=lambda p: (captured.append(p), "<response>R</response>")[1],
    )
    # With context
    resp, th = opt.generate("MyTask", context="MyContext")
    assert resp == "R"
    assert "Task:\nMyTask" in captured[-1]
    assert "Context and Feedback:\nMyContext" in captured[-1]

    # Without context
    resp2, th2 = opt.generate("MyTask2", context="")
    assert resp2 == "R"
    assert "Task:\nMyTask2" in captured[-1]
    assert "Context and Feedback:" not in captured[-1]

    # Without {task} and without context
    opt_no_task = EvaluatorOptimizer(
        generator_prompt="No task placeholder",
        call_fn=lambda p: (captured.append(p), "<response>R</response>")[1],
    )
    opt_no_task.generate("MyTask3", context="")
    assert "No task placeholder" in captured[-1]
    assert "Context and Feedback:" not in captured[-1]


def test_evaluate_custom_prompt_key_error_and_no_criteria_fallback() -> None:
    captured: list[str] = []
    opt = EvaluatorOptimizer(
        evaluator_prompt="Judge {task} {content} {missing_key}",
        call_fn=lambda p: (captured.append(p), "<status>PASS</status><feedback>OK</feedback>")[1],
    )
    status, fb = opt.evaluate("Task", "Content", criteria="Fast")
    assert status == "PASS"
    assert "Task:\nTask" in captured[-1]
    assert "Proposed Solution:\nContent" in captured[-1]
    assert "Evaluation Criteria:\nFast" in captured[-1]

    # KeyError without criteria
    opt.evaluate("TaskNoCrit", "ContentNoCrit", criteria="")
    assert "Evaluation Criteria:" not in captured[-1]

    # Custom prompt without format placeholders and WITHOUT criteria
    opt_plain = EvaluatorOptimizer(
        evaluator_prompt="Plain Judge",
        call_fn=lambda p: (captured.append(p), "<status>PASS</status><feedback>OK</feedback>")[1],
    )
    opt_plain.evaluate("Task2", "Content2", criteria="")
    assert "Plain Judge" in captured[-1]
    assert "Evaluation Criteria" not in captured[-1]


def test_evaluate_status_variants() -> None:
    # Status with FAIL variant
    opt1 = EvaluatorOptimizer(
        call_fn=lambda p: "<status>HARD_FAIL</status><feedback>Bad</feedback>"
    )
    assert opt1.evaluate("T", "C")[0] == "FAIL"

    # Status with PASS variant
    opt2 = EvaluatorOptimizer(
        call_fn=lambda p: "<status>PASS_WITH_WARNINGS</status><feedback>Acceptable</feedback>"
    )
    assert opt2.evaluate("T", "C")[0] == "PASS"

    # Raw text containing PASS
    opt3 = EvaluatorOptimizer(call_fn=lambda p: "The solution passed without any issues.")
    assert opt3.evaluate("T", "C")[0] == "PASS"

    # Raw text containing FAIL
    opt4 = EvaluatorOptimizer(call_fn=lambda p: "The solution failed the test.")
    assert opt4.evaluate("T", "C")[0] == "FAIL"


def test_optimize_unexpected_status_loop() -> None:
    # 1. Custom status that continues until max_iterations
    opt = EvaluatorOptimizer(
        call_fn=lambda p: "<response>Resp</response>",
        max_iterations=2,
    )
    opt.evaluate = lambda *a, **k: ("CUSTOM_STATUS", "Needs work")  # type: ignore[assignment]
    result = opt.optimize("Task")
    assert result.status == "MAX_ITERATIONS"
    assert result.iterations == 2

    # 2. Custom status with max_iterations=1 (breaks immediately on iteration 1)
    opt1 = EvaluatorOptimizer(
        call_fn=lambda p: "<response>Resp</response>",
        max_iterations=1,
    )
    opt1.evaluate = lambda *a, **k: ("CUSTOM_STATUS", "Needs work")  # type: ignore[assignment]
    result1 = opt1.optimize("Task")
    assert result1.status == "MAX_ITERATIONS"
    assert result1.iterations == 1


def test_call_fn_default_no_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_run = MagicMock()
    mock_run.return_value.text = "<response>Mock Text</response>"
    monkeypatch.setattr("sakthai.agent.loop.run_agent", mock_run)

    opt = EvaluatorOptimizer(model=None, provider=None)
    raw = opt._call("Test prompt")
    assert raw == "<response>Mock Text</response>"
    mock_run.assert_called_once()
    assert "provider" not in mock_run.call_args.kwargs


def test_cli_optimize_empty_thoughts_and_feedback(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    it = OptimizationIteration(
        iteration=1,
        thoughts="",
        response="minimal response",
        status="PASS",
        feedback="",
        latency_s=0.1,
    )
    res_obj = OptimizationResult(
        final_response="minimal response",
        status="PASS",
        iterations=1,
        history=[it],
        total_duration_s=0.1,
    )
    monkeypatch.setattr("sakthai.agent.optimizer.optimize_solution", lambda **kw: res_obj)

    res = runner.invoke(main, ["run", "--optimize", "Simple Task"])
    assert res.exit_code == 0
    assert "Thoughts:" not in res.output
    assert "Feedback:" not in res.output
    assert "Candidate Solution:\nminimal response" in res.output
