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
    assert "SakKing" in (kwargs["system_prompt"] or "")


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
