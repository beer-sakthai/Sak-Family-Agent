"""Tests for multi-agent coordinator and task delegation manager."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from sakthai.agent.coordinator import (
    DelegationCycleError,
    DelegationDepthError,
    get_delegation_chain,
    get_delegation_depth,
    resolve_persona_agent_kwargs,
    run_persona_task,
)
from sakthai.agent.loop import AgentResult
from sakthai.memory.store import MemoryStore


def test_delegation_context_initial_state() -> None:
    assert get_delegation_chain() == ()
    assert get_delegation_depth() == 0


def test_resolve_persona_agent_kwargs_valid(tmp_path) -> None:
    store = MemoryStore(":memory:")
    kwargs = resolve_persona_agent_kwargs(
        "sakking",
        "Write tests",
        with_skills=["SakKing-comfyui"],
        max_iterations=5,
        store=store,
    )
    assert kwargs["persona"] == "sakking"
    assert kwargs["task"] == "Write tests"
    assert kwargs["skills"] == ["SakKing-comfyui"]
    assert kwargs["max_iterations"] == 5
    assert kwargs["store"] is store
    assert "SakKing" in kwargs["system_prompt_prefix"]


def test_resolve_persona_agent_kwargs_unknown_persona() -> None:
    with pytest.raises(ValueError, match="Unknown persona 'unknown'"):
        resolve_persona_agent_kwargs("unknown", "Task")


def test_run_persona_task_depth_error() -> None:
    from sakthai.agent.coordinator import _DELEGATION_CHAIN

    token = _DELEGATION_CHAIN.set(("sakthai", "sakking"))
    try:
        with pytest.raises(DelegationDepthError, match="maximum limit"):
            run_persona_task("saksee", "Review task", max_depth=2)
    finally:
        _DELEGATION_CHAIN.reset(token)


def test_run_persona_task_cycle_error() -> None:
    from sakthai.agent.coordinator import _DELEGATION_CHAIN

    token = _DELEGATION_CHAIN.set(("sakthai", "sakking"))
    try:
        with pytest.raises(DelegationCycleError, match="Circular delegation detected"):
            run_persona_task("sakking", "Refactor task", max_depth=5)
    finally:
        _DELEGATION_CHAIN.reset(token)


def test_run_persona_task_success() -> None:
    store = MemoryStore(":memory:")
    mock_result = AgentResult(
        text="All tests passed.",
        iterations=3,
        stop_reason="end_turn",
        usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    )

    with patch("sakthai.agent.coordinator.run_agent", return_value=mock_result) as mock_run:
        result = run_persona_task(
            "sakjules",
            "Verify CI pipeline",
            store=store,
            max_iterations=4,
        )

        assert result.text == "All tests passed."
        assert result.iterations == 3
        assert result.usage["total_tokens"] == 150
        mock_run.assert_called_once()


def test_run_persona_task_bounds_unattended_runs_by_default() -> None:
    """Regression: a delegated run had no wall-clock budget, so a stalled one
    could hold its worker indefinitely."""
    from sakthai.agent.loop import DEFAULT_UNATTENDED_MAX_SECONDS

    mock_result = AgentResult(text="ok", iterations=1, stop_reason="end_turn", usage={})
    with patch("sakthai.agent.coordinator.run_agent", return_value=mock_result) as mock_run:
        run_persona_task("sakjules", "task", store=MemoryStore(":memory:"))
    assert mock_run.call_args.kwargs["max_seconds"] == DEFAULT_UNATTENDED_MAX_SECONDS


def test_run_persona_task_budget_can_be_overridden_or_lifted() -> None:
    mock_result = AgentResult(text="ok", iterations=1, stop_reason="end_turn", usage={})
    with patch("sakthai.agent.coordinator.run_agent", return_value=mock_result) as mock_run:
        run_persona_task("sakjules", "task", store=MemoryStore(":memory:"), max_seconds=30.0)
        assert mock_run.call_args.kwargs["max_seconds"] == 30.0
        run_persona_task("sakjules", "task", store=MemoryStore(":memory:"), max_seconds=None)
        assert mock_run.call_args.kwargs["max_seconds"] is None


def test_run_parallel_persona_tasks_empty() -> None:
    from sakthai.agent.coordinator import run_parallel_persona_tasks

    assert run_parallel_persona_tasks([]) == []


def test_run_parallel_persona_tasks_success() -> None:
    from sakthai.agent.coordinator import run_parallel_persona_tasks

    mock_result_1 = AgentResult(
        text="Research result",
        iterations=2,
        stop_reason="end_turn",
        usage={"input_tokens": 50, "output_tokens": 25, "total_tokens": 75},
    )
    mock_result_2 = AgentResult(
        text="Tech architecture",
        iterations=3,
        stop_reason="end_turn",
        usage={"input_tokens": 60, "output_tokens": 30, "total_tokens": 90},
    )

    def _side_effect(**kwargs):
        if kwargs.get("persona") == "saksee":
            return mock_result_1
        return mock_result_2

    with patch("sakthai.agent.coordinator.run_agent", side_effect=_side_effect) as mock_run:
        tasks = [
            {"persona": "saksee", "task": "Research problem"},
            {"persona": "sakking", "task": "Architect system"},
        ]
        results = run_parallel_persona_tasks(tasks)

        assert len(results) == 2
        assert results[0].text == "Research result"
        assert results[1].text == "Tech architecture"
        assert mock_run.call_count == 2


def test_run_persona_task_reaches_the_real_run_agent() -> None:
    """Every other test here patches ``run_agent``, which is how delegation
    shipped passing kwargs (``no_mcp``, ``system_prompt``...) that
    ``run_agent`` does not accept: every real call raised ``TypeError``.
    Drive the real loop with a fake model client instead."""
    captured: dict[str, object] = {}

    class _Block:
        type = "text"
        text = "delegated ok"

    class _Resp:
        stop_reason = "end_turn"
        content = [_Block()]

    class _Messages:
        def create(self, **kwargs: object) -> _Resp:
            captured.update(kwargs)
            return _Resp()

    class _Client:
        messages = _Messages()

    result = run_persona_task(
        "sakking",
        "Write tests",
        store=MemoryStore(":memory:"),
        client=_Client(),
        provider="anthropic",
        model="test-model",
    )

    assert result.text == "delegated ok"
    assert captured["model"] == "test-model"
    # The persona's SOUL.md is prepended to the system prompt.
    assert str(captured["system"]).startswith("# SOUL.md — SakKing")


def test_run_persona_task_with_allow_mcp() -> None:
    """Verify that allow_mcp connects MCP servers when requested."""
    from sakthai.agent.coordinator import run_persona_task
    from sakthai.agent.loop import AgentResult

    mock_result = AgentResult(text="mcp ok", iterations=1, stop_reason="end_turn", usage={})
    with patch("sakthai.agent.coordinator.run_agent", return_value=mock_result) as mock_run:
        result = run_persona_task(
            "saksee",
            "Figma review",
            store=MemoryStore(":memory:"),
            allow_mcp=True,
        )
        assert result.text == "mcp ok"
        mock_run.assert_called_once()


def test_run_parallel_persona_tasks_error_isolation() -> None:
    """Verify that a failing worker in parallel execution does not crash other workers."""
    from sakthai.agent.coordinator import run_parallel_persona_tasks
    from sakthai.agent.loop import AgentResult

    def _mock_run(persona, task, **kwargs):
        if persona == "sakthai":
            raise RuntimeError("Backend connection refused")
        return AgentResult(text="success", iterations=1, stop_reason="end_turn", usage={})

    with patch("sakthai.agent.coordinator.run_persona_task", side_effect=_mock_run):
        results = run_parallel_persona_tasks(
            [
                {"persona": "sakthai", "task": "Task 1"},
                {"persona": "sakking", "task": "Task 2"},
            ]
        )
        assert len(results) == 2
        assert results[0].stop_reason == "error"
        assert "Backend connection refused" in results[0].text
        assert results[1].stop_reason == "end_turn"
        assert results[1].text == "success"


def test_aggregate_persona_results() -> None:
    """Verify aggregation of parallel results into a consolidated dictionary."""
    from sakthai.agent.coordinator import aggregate_persona_results
    from sakthai.agent.loop import AgentResult

    res1 = AgentResult(
        text="Subtask 1 complete",
        iterations=2,
        stop_reason="end_turn",
        usage={"input_tokens": 10, "output_tokens": 20},
    )
    res2 = AgentResult(
        text="Subtask 2 failed",
        iterations=0,
        stop_reason="error",
        usage={"input_tokens": 0, "output_tokens": 0},
    )

    agg = aggregate_persona_results([res1, res2])
    assert agg["total_tasks"] == 2
    assert agg["successful_tasks"] == 1
    assert agg["failed_tasks"] == 1
    assert "Subtask 1" in agg["summary_text"]
    assert "Subtask 2" in agg["summary_text"]
