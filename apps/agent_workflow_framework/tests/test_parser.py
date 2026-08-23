from typing import Any

"""Unit tests for workflow parser.

Comprehensive unit tests including Happy Path, Edge Cases, Error Handling,
and Security-Focused constraints.
"""

import json
from pathlib import Path

import pytest
from agent_workflow.models import WorkflowDefinition
from agent_workflow.parser import (
    WorkflowParseError,
    parse_workflow_dict,
    parse_workflow_file,
    parse_workflow_json,
    parse_workflow_yaml,
)

# --- Dummy Data ---

VALID_WORKFLOW_DICT = {
    "name": "Test Workflow",
    "description": "A valid workflow for testing.",
    "steps": [
        {
            "id": "step1",
            "action": "echo",
            "params": {"message": "Hello"},
            "retry": 3,
            "retry_delay": 1.5,
        },
        {
            "id": "step2",
            "action": "request",
            "depends_on": ["step1"],
            "params": {"url": "http://example.com"},
        },
    ],
}

VALID_WORKFLOW_YAML = """
name: Test Workflow YAML
description: A valid YAML workflow
steps:
  - id: step_yaml_1
    action: echo
    params:
      msg: YAML test
"""

VALID_WORKFLOW_JSON = json.dumps(
    {"name": "Test Workflow JSON", "steps": [{"id": "step_json_1", "action": "echo"}]}
)

# --- Happy Path Tests ---


def test_parse_workflow_dict_happy_path() -> None:
    """Test successful parsing of a valid workflow dictionary."""
    workflow = parse_workflow_dict(VALID_WORKFLOW_DICT)
    assert isinstance(workflow, WorkflowDefinition)
    assert workflow.name == "Test Workflow"
    assert workflow.description == "A valid workflow for testing."
    assert len(workflow.steps) == 2

    assert workflow.steps[0].id == "step1"
    assert workflow.steps[0].action == "echo"
    assert workflow.steps[0].retry == 3
    assert workflow.steps[0].retry_delay == 1.5

    assert workflow.steps[1].id == "step2"
    assert workflow.steps[1].depends_on == ["step1"]


def test_parse_workflow_yaml_happy_path() -> None:
    """Test successful parsing of valid YAML."""
    workflow = parse_workflow_yaml(VALID_WORKFLOW_YAML)
    assert workflow.name == "Test Workflow YAML"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].id == "step_yaml_1"


def test_parse_workflow_json_happy_path() -> None:
    """Test successful parsing of valid JSON."""
    workflow = parse_workflow_json(VALID_WORKFLOW_JSON)
    assert workflow.name == "Test Workflow JSON"
    assert workflow.description is None
    assert len(workflow.steps) == 1


def test_parse_workflow_file_json(tmp_path: Path) -> None:
    """Test successful parsing from a JSON file."""
    file_path = tmp_path / "workflow.json"
    file_path.write_text(VALID_WORKFLOW_JSON)

    workflow = parse_workflow_file(file_path)
    assert workflow.name == "Test Workflow JSON"


def test_parse_workflow_file_yaml(tmp_path: Path) -> None:
    """Test successful parsing from a YAML file."""
    file_path = tmp_path / "workflow.yaml"
    file_path.write_text(VALID_WORKFLOW_YAML)

    workflow = parse_workflow_file(file_path)
    assert workflow.name == "Test Workflow YAML"


# --- Edge Cases Tests ---


def test_parse_workflow_minimal_dict() -> None:
    """Test parsing a minimal valid dictionary without optional fields."""
    data = {"name": "Minimal", "steps": [{"id": "step1"}]}
    workflow = parse_workflow_dict(data)
    assert workflow.name == "Minimal"
    assert workflow.description is None
    assert len(workflow.steps) == 1

    # Check default step values
    step = workflow.steps[0]
    assert step.id == "step1"
    assert step.action == "echo"
    assert step.params == {}
    assert step.depends_on == []
    assert step.retry == 0
    assert step.retry_delay == 0.0


# --- Error Handling Tests ---


def test_parse_empty_or_invalid_type() -> None:
    """Test parsing fails gracefully on None or non-dict inputs."""
    with pytest.raises(WorkflowParseError, match="empty"):
        parse_workflow_dict(None)

    with pytest.raises(WorkflowParseError, match="must be a dictionary/mapping"):
        parse_workflow_dict(["not", "a", "dict"])


def test_parse_unknown_top_level_keys() -> None:
    """Test rejection of unknown top-level keys."""
    data = dict(VALID_WORKFLOW_DICT)
    data["malicious_key"] = "payload"

    with pytest.raises(WorkflowParseError, match="Unknown top-level attribute"):
        parse_workflow_dict(data)


def test_parse_missing_required_fields() -> None:
    """Test missing 'name' or 'steps'."""
    with pytest.raises(WorkflowParseError, match="missing required field 'name'"):
        parse_workflow_dict({"steps": []})

    with pytest.raises(WorkflowParseError, match="missing required field 'steps'"):
        parse_workflow_dict({"name": "No steps"})


def test_parse_invalid_step_format() -> None:
    """Test steps must be a list of dictionaries."""
    with pytest.raises(WorkflowParseError, match="'steps' must be a list"):
        parse_workflow_dict({"name": "Test", "steps": {"id": "1"}})

    with pytest.raises(WorkflowParseError, match="must be a dictionary"):
        parse_workflow_dict({"name": "Test", "steps": ["not_a_dict"]})


def test_parse_duplicate_step_ids() -> None:
    """Test that duplicate step IDs are correctly rejected."""
    data = {"name": "Dupes", "steps": [{"id": "step1"}, {"id": "step1"}]}
    with pytest.raises(WorkflowParseError, match="Duplicate step ID"):
        parse_workflow_dict(data)


def test_parse_invalid_yaml_syntax() -> None:
    """Test parsing invalid YAML strings."""
    with pytest.raises(WorkflowParseError, match="YAML syntax error"):
        parse_workflow_yaml("name: [unclosed list")


def test_parse_invalid_json_syntax() -> None:
    """Test parsing invalid JSON strings."""
    with pytest.raises(WorkflowParseError, match="JSON syntax error"):
        parse_workflow_json("{name: missing quotes}")


def test_parse_workflow_file_not_found(tmp_path: Path) -> None:
    """Test reading a non-existent file."""
    bad_path = tmp_path / "does_not_exist.json"
    with pytest.raises(WorkflowParseError, match="Workflow file not found"):
        parse_workflow_file(bad_path)


def test_parse_workflow_file_read_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test handling of file read permissions or errors."""
    file_path = tmp_path / "unreadable.json"
    file_path.write_text("{}")

    def mock_read_text(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError("Permission denied")

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    with pytest.raises(WorkflowParseError, match="Failed to read workflow file"):
        parse_workflow_file(file_path)


# --- Security Focused Tests ---


def test_parse_step_type_mismatches_security() -> None:
    """Test robust handling of booleans masked as ints or type mismatches (Variant 3)."""
    # Boolean masquerading as int in retry
    data_retry_bool = {"name": "Type Mismatch", "steps": [{"id": "s1", "retry": True}]}
    with pytest.raises(WorkflowParseError, match="'retry' count must be a non-negative integer"):
        parse_workflow_dict(data_retry_bool)

    # Boolean masquerading as float in retry_delay
    data_delay_bool = {"name": "Type Mismatch", "steps": [{"id": "s1", "retry_delay": False}]}
    with pytest.raises(WorkflowParseError, match="'retry_delay' must be a non-negative number"):
        parse_workflow_dict(data_delay_bool)

    # depends_on with invalid inner types
    data_depends = {"name": "Depends Mismatch", "steps": [{"id": "s1", "depends_on": [123]}]}
    with pytest.raises(
        WorkflowParseError, match="depends_on item at index 0 must be a non-empty string"
    ):
        parse_workflow_dict(data_depends)


def test_parse_unknown_step_keys_security() -> None:
    """Test strict rejection of unknown keys in steps to prevent injection (Variant 3)."""
    data = {
        "name": "Injection Test",
        "steps": [{"id": "s1", "malicious_injection": "sudo rm -rf /"}],
    }
    with pytest.raises(WorkflowParseError, match="unknown attribute"):
        parse_workflow_dict(data)


def test_parse_yaml_is_safe() -> None:
    """Verify that YAML parser rejects dangerous tags, proving safe_load is used."""
    # Attempting to use Python object instantiation (which works with yaml.load but not safe_load)
    dangerous_yaml = """
    name: Dangerous YAML
    steps:
      - id: !!python/object/apply:os.system ["echo vulnerable"]
    """
    with pytest.raises(WorkflowParseError, match="YAML syntax error"):
        parse_workflow_yaml(dangerous_yaml)
