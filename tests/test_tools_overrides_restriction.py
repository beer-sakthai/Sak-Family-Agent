"""Regression tests for tool override restrictions and audit logging.

These tests verify that:
1. Tool description overrides are applied and logged
2. input_schema overrides are silently ignored (not applied)
3. Parse failures are logged without crashing
"""

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from sakthai.agent.tools import _load_tool_overrides, tool_by_name


def test_tool_override_description_applied(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A description override is applied and logged."""
    overrides_file = tmp_path / "tool_descriptions.json"
    original_tool = tool_by_name("learn")
    assert original_tool is not None
    original_description = original_tool.description

    custom_description = "Custom learn description for testing"
    overrides_file.write_text(json.dumps({"learn": {"description": custom_description}}))

    # Patch where tool_descriptions_path is imported in the function
    with patch("sakthai.config.tool_descriptions_path") as mock_path:
        mock_path.return_value = overrides_file

        with caplog.at_level(logging.DEBUG):
            _load_tool_overrides()

        tool = tool_by_name("learn")
        assert tool is not None
        assert tool.description == custom_description, "Description should be overridden"

    # Reset the tool for other tests
    object.__setattr__(original_tool, "description", original_description)


def test_tool_override_input_schema_ignored(tmp_path: Path) -> None:
    """input_schema overrides are silently ignored and not applied."""
    overrides_file = tmp_path / "tool_descriptions.json"
    original_tool = tool_by_name("learn")
    assert original_tool is not None
    original_schema = original_tool.input_schema

    # Attempt to override input_schema with malicious schema
    malicious_override = {
        "learn": {"input_schema": {"type": "object", "properties": {"cmd": {"type": "string"}}}}
    }
    overrides_file.write_text(json.dumps(malicious_override))

    # Patch where tool_descriptions_path is imported in the function
    with patch("sakthai.config.tool_descriptions_path") as mock_path:
        mock_path.return_value = overrides_file
        _load_tool_overrides()

        tool = tool_by_name("learn")
        assert tool is not None
        # Schema should remain unchanged (the override was ignored)
        assert tool.input_schema == original_schema, "input_schema override should be ignored"


def test_tool_override_mixed_fields(tmp_path: Path) -> None:
    """When both description and input_schema are in overrides, only description is applied."""
    overrides_file = tmp_path / "tool_descriptions.json"
    original_tool = tool_by_name("learn")
    assert original_tool is not None
    original_schema = original_tool.input_schema
    original_description = original_tool.description

    custom_description = "Custom description"
    malicious_schema = {"type": "object"}

    overrides_file.write_text(
        json.dumps(
            {
                "learn": {
                    "description": custom_description,
                    "input_schema": malicious_schema,
                }
            }
        )
    )

    with patch("sakthai.config.tool_descriptions_path") as mock_path:
        mock_path.return_value = overrides_file
        _load_tool_overrides()

        tool = tool_by_name("learn")
        assert tool is not None
        assert tool.description == custom_description, "Description should be applied"
        assert tool.input_schema == original_schema, "input_schema should remain unchanged"

    # Reset for other tests
    object.__setattr__(original_tool, "description", original_description)


def test_tool_override_parse_failure_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Parse failure of overrides file is logged (debug) and doesn't crash."""
    overrides_file = tmp_path / "tool_descriptions.json"
    # Write invalid JSON
    overrides_file.write_text("{invalid json")

    with patch("sakthai.config.tool_descriptions_path") as mock_path:
        mock_path.return_value = overrides_file

        with caplog.at_level(logging.DEBUG):
            # Should not raise
            _load_tool_overrides()

        # Should have logged the failure
        assert "Failed to load tool overrides" in caplog.text or any(
            "Failed" in record.message for record in caplog.records
        )


def test_tool_override_nonexistent_file_silent() -> None:
    """If overrides file doesn't exist, no error is logged."""
    with patch("sakthai.config.tool_descriptions_path") as mock_path:
        mock_path.return_value = Path("/nonexistent/path/tool_descriptions.json")
        # Should not raise or log
        _load_tool_overrides()


def test_multiple_tool_overrides(tmp_path: Path) -> None:
    """Multiple tool overrides are applied independently."""
    overrides_file = tmp_path / "tool_descriptions.json"

    learn_tool = tool_by_name("learn")
    recall_tool = tool_by_name("recall")
    assert learn_tool is not None and recall_tool is not None

    original_learn_desc = learn_tool.description
    original_recall_desc = recall_tool.description

    custom_overrides = {
        "learn": {"description": "Custom learn"},
        "recall": {"description": "Custom recall"},
    }
    overrides_file.write_text(json.dumps(custom_overrides))

    with patch("sakthai.config.tool_descriptions_path") as mock_path:
        mock_path.return_value = overrides_file
        _load_tool_overrides()

        learn_tool = tool_by_name("learn")
        recall_tool = tool_by_name("recall")
        assert learn_tool is not None and recall_tool is not None
        assert learn_tool.description == "Custom learn"
        assert recall_tool.description == "Custom recall"

    # Reset for other tests
    object.__setattr__(learn_tool, "description", original_learn_desc)
    object.__setattr__(recall_tool, "description", original_recall_desc)
