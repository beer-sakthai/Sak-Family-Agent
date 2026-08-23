"""Unit tests for tool selection optimization components (module, metric, overrides)."""

import json
import pytest
import dspy
from pathlib import Path
from dataclasses import dataclass

from evolution.core.config import EvolutionConfig
from evolution.core.dataset_builder import ToolSelectionExample, EvalDataset
from evolution.core.fitness import tool_selection_metric
from evolution.tools.tool_module import (
    ToolSelectionModule,
    format_baseline_descriptions,
    parse_evolved_descriptions,
)


@dataclass
class MockTool:
    name: str
    description: str
    input_schema: dict


def test_format_baseline_descriptions():
    tools = [
        MockTool(
            name="dummy_tool",
            description="A dummy tool for testing.",
            input_schema={
                "type": "object",
                "properties": {"param1": {"type": "string", "description": "The first parameter."}},
                "required": ["param1"],
            },
        )
    ]
    formatted = format_baseline_descriptions(tools)
    assert "[TOOL dummy_tool]" in formatted
    assert "A dummy tool for testing." in formatted
    assert "- param1: The first parameter. (required)" in formatted


def test_parse_evolved_descriptions():
    evolved_instructions = """
You are an orchestrator selecting the correct tool for the user's task.

[TOOL dummy_tool]
Evolved description for dummy tool.
Parameters:
  - param1: Evolved parameter description. (required)
  - param2: Optional parameter.

[TOOL another_tool]
Another tool description.
"""
    parsed = parse_evolved_descriptions(evolved_instructions)
    assert "dummy_tool" in parsed
    assert parsed["dummy_tool"]["description"] == "Evolved description for dummy tool."
    assert parsed["dummy_tool"]["parameters"]["param1"] == "Evolved parameter description."
    assert parsed["dummy_tool"]["parameters"]["param2"] == "Optional parameter."

    assert "another_tool" in parsed
    assert parsed["another_tool"]["description"] == "Another tool description."


def test_tool_selection_module():
    formatted = "Dummy instructions block."
    module = ToolSelectionModule(formatted)
    assert module.formatted_descriptions == formatted


def test_tool_selection_metric():
    # Test case 1: exact match
    example = dspy.Example(
        expected_tool="search",
        expected_args={"query": "hello"},
    )
    pred_exact = dspy.Prediction(
        predicted_tool="search",
        predicted_args='{"query": "hello"}',
    )
    score = tool_selection_metric(example, pred_exact)
    assert score == 1.0

    # Test case 2: mismatch tool
    pred_wrong_tool = dspy.Prediction(
        predicted_tool="read_file",
        predicted_args='{"query": "hello"}',
    )
    score_wrong_tool = tool_selection_metric(example, pred_wrong_tool)
    assert score_wrong_tool == 0.4  # tool_match=0 (0.0), args_match=1 (0.4)

    # Test case 3: mismatch args
    pred_wrong_args = dspy.Prediction(
        predicted_tool="search",
        predicted_args='{"query": "world"}',
    )
    score_wrong_args = tool_selection_metric(example, pred_wrong_args)
    assert score_wrong_args == 0.6  # tool_match=1 (0.6), args_match=0 (0.0)
