"""Unit tests for multi-agent goal delegation and dispatch in agent/tools.py."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

from sakthai.agent.tools import Tool, tool_by_name
from sakthai.memory.store import MemoryStore


def test_decompose_and_dispatch_tool_metadata() -> None:
    tool = tool_by_name("decompose_and_dispatch")
    assert tool is not None
    assert isinstance(tool, Tool)
    assert tool.name == "decompose_and_dispatch"
    schema = tool.schema()
    assert "goal" in schema["input_schema"]["properties"]
    assert "stages" in schema["input_schema"]["properties"]
    assert "dry_run" in schema["input_schema"]["properties"]
    assert "goal" in schema["input_schema"]["required"]


def test_decompose_and_dispatch_dry_run_auto(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("decompose_and_dispatch")
    assert tool is not None

    goal = "Release fine-tuned Qwen model with CI verification, model card, and web benchmarks"
    out = tool.handler({"goal": goal, "dry_run": True}, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["dry_run"] is True
    assert data["goal"] == goal
    stages = data["stages"]
    assert len(stages) >= 3
    personas = [s["persona"] for s in stages]
    # Check that appropriate personas are assigned based on goal keywords
    assert "sakthai" in personas or "sakking" in personas

    # Verify memory persistence
    memories = store.search_by_tag("delegation", limit=10)
    assert len(memories) > 0


def test_decompose_and_dispatch_custom_stages(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("decompose_and_dispatch")
    assert tool is not None

    stages = [
        {"persona": "sakking", "task": "Run tests and benchmark execution"},
        {"persona": "sakjules", "task": "Verify CI workflows and bandit security scans"},
    ]

    mock_result1 = MagicMock()
    mock_result1.text = "All tests passed with 98% coverage."
    mock_result1.iterations = 3
    mock_result1.usage = {"total_tokens": 150}

    mock_result2 = MagicMock()
    mock_result2.text = "GitHub Actions workflows green and clean."
    mock_result2.iterations = 2
    mock_result2.usage = {"total_tokens": 120}

    with patch("sakthai.agent.coordinator.run_persona_task") as mock_run:
        mock_run.side_effect = [mock_result1, mock_result2]
        out = tool.handler(
            {
                "goal": "Verify code quality and CI pipeline",
                "stages": stages,
                "dry_run": False,
            },
            store,
        )
        data = json.loads(out)
        assert data["status"] == "ok"
        assert data["dry_run"] is False
        assert len(data["dispatched_stages"]) == 2
        assert mock_run.call_count == 2

        # Check memory recorded
        obs = store.search_by_tag("delegation", limit=10)
        assert len(obs) >= 2
