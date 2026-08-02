"""Workflow definition parser module.

Provides functionality for parsing YAML and JSON workflow definition files
or dictionary structures into validated WorkflowDefinition dataclasses.
"""

from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import json
import yaml

try:
    from agent_workflow.models import WorkflowDefinition, StepDefinition
except ImportError:
    try:
        from .proposed_models import WorkflowDefinition, StepDefinition  # type: ignore
    except ImportError:
        from proposed_models import WorkflowDefinition, StepDefinition  # type: ignore


class WorkflowParseError(Exception):
    """Raised when workflow parsing or schema validation fails."""
    pass


ALLOWED_TOP_LEVEL_KEYS = {"name", "description", "steps"}
ALLOWED_STEP_KEYS = {"id", "action", "params", "depends_on", "retry", "retry_delay"}


def parse_workflow_dict(data: Any) -> WorkflowDefinition:
    """Validate a raw dictionary structure and parse it into a WorkflowDefinition.

    Args:
        data: Raw dict expected to conform to the workflow schema.

    Returns:
        WorkflowDefinition instance.

    Raises:
        WorkflowParseError: If schema validation fails or data structure is invalid.
    """
    if data is None:
        raise WorkflowParseError("Workflow definition content is empty.")
    if not isinstance(data, dict):
        raise WorkflowParseError(
            f"Workflow definition must be a dictionary/mapping, got '{type(data).__name__}'."
        )

    # Check unknown top-level keys
    unknown_keys = set(data.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_keys:
        raise WorkflowParseError(
            f"Unknown top-level attribute(s) in workflow definition: {', '.join(sorted(unknown_keys))}."
        )

    # Validate 'name'
    if "name" not in data:
        raise WorkflowParseError("Workflow definition missing required field 'name'.")
    name = data["name"]
    if not isinstance(name, str) or not name.strip():
        raise WorkflowParseError("Workflow 'name' must be a non-empty string.")

    # Validate 'description'
    description = data.get("description")
    if description is not None and not isinstance(description, str):
        raise WorkflowParseError("Workflow 'description' must be a string if provided.")

    # Validate 'steps'
    if "steps" not in data:
        raise WorkflowParseError("Workflow definition missing required field 'steps'.")
    raw_steps = data["steps"]
    if not isinstance(raw_steps, list):
        raise WorkflowParseError("Workflow 'steps' must be a list.")
    if len(raw_steps) == 0:
        raise WorkflowParseError("Workflow must contain at least one step.")

    parsed_steps: List[StepDefinition] = []
    seen_step_ids = set()

    for idx, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            raise WorkflowParseError(
                f"Step at index {idx} must be a dictionary, got '{type(raw_step).__name__}'."
            )

        # Check unknown step keys
        unknown_step_keys = set(raw_step.keys()) - ALLOWED_STEP_KEYS
        if unknown_step_keys:
            raise WorkflowParseError(
                f"Step at index {idx} has unknown attribute(s): {', '.join(sorted(unknown_step_keys))}."
            )

        # Validate step 'id'
        if "id" not in raw_step:
            raise WorkflowParseError(f"Step at index {idx} missing required field 'id'.")
        step_id = raw_step["id"]
        if not isinstance(step_id, str) or not step_id.strip():
            raise WorkflowParseError(f"Step at index {idx} 'id' must be a non-empty string.")

        if step_id in seen_step_ids:
            raise WorkflowParseError(f"Duplicate step ID '{step_id}' found in workflow.")
        seen_step_ids.add(step_id)

        # Validate step 'action'
        if "action" not in raw_step:
            raise WorkflowParseError(f"Step '{step_id}' missing required field 'action'.")
        action = raw_step["action"]
        if not isinstance(action, str) or not action.strip():
            raise WorkflowParseError(f"Step '{step_id}' 'action' must be a non-empty string.")

        # Validate 'params'
        params = raw_step.get("params", {})
        if not isinstance(params, dict):
            raise WorkflowParseError(f"Step '{step_id}' 'params' must be a dictionary.")

        # Validate 'depends_on'
        depends_on = raw_step.get("depends_on", [])
        if not isinstance(depends_on, list):
            raise WorkflowParseError(f"Step '{step_id}' 'depends_on' must be a list of step IDs.")
        for dep_idx, dep in enumerate(depends_on):
            if not isinstance(dep, str) or not dep.strip():
                raise WorkflowParseError(
                    f"Step '{step_id}' depends_on item at index {dep_idx} must be a non-empty string."
                )

        # Validate 'retry'
        retry = raw_step.get("retry", 0)
        if isinstance(retry, bool) or not isinstance(retry, int) or retry < 0:
            raise WorkflowParseError(f"Step '{step_id}' 'retry' count must be a non-negative integer.")

        # Validate 'retry_delay'
        retry_delay = raw_step.get("retry_delay", 0.0)
        if isinstance(retry_delay, bool) or not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            raise WorkflowParseError(f"Step '{step_id}' 'retry_delay' must be a non-negative number.")

        parsed_step = StepDefinition(
            id=step_id,
            action=action,
            params=params,
            depends_on=depends_on,
            retry=retry,
            retry_delay=float(retry_delay),
        )
        parsed_steps.append(parsed_step)

    workflow = WorkflowDefinition(
        name=name,
        description=description,
        steps=parsed_steps,
    )

    return workflow


def parse_workflow_yaml(yaml_content: str) -> WorkflowDefinition:
    """Parse YAML string content into a WorkflowDefinition.

    Args:
        yaml_content: String containing YAML workflow definition.

    Returns:
        WorkflowDefinition instance.

    Raises:
        WorkflowParseError: If YAML syntax is invalid or schema validation fails.
    """
    if not isinstance(yaml_content, str):
        raise WorkflowParseError(f"Expected YAML content as string, got '{type(yaml_content).__name__}'.")

    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as exc:
        raise WorkflowParseError(f"YAML syntax error: {exc}") from exc

    return parse_workflow_dict(data)


def parse_workflow_json(json_content: str) -> WorkflowDefinition:
    """Parse JSON string content into a WorkflowDefinition.

    Args:
        json_content: String containing JSON workflow definition.

    Returns:
        WorkflowDefinition instance.

    Raises:
        WorkflowParseError: If JSON syntax is invalid or schema validation fails.
    """
    if not isinstance(json_content, str):
        raise WorkflowParseError(f"Expected JSON content as string, got '{type(json_content).__name__}'.")

    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as exc:
        raise WorkflowParseError(f"JSON syntax error: {exc}") from exc

    return parse_workflow_dict(data)


def parse_workflow_file(file_path: Union[str, Path]) -> WorkflowDefinition:
    """Parse a workflow definition file (YAML or JSON) into a WorkflowDefinition.

    Args:
        file_path: Path to the workflow file (str or Path object).

    Returns:
        WorkflowDefinition instance.

    Raises:
        WorkflowParseError: If file cannot be read, syntax is invalid, or schema validation fails.
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists():
        raise WorkflowParseError(f"Workflow file not found: '{path}'")
    if not path.is_file():
        raise WorkflowParseError(f"Workflow path is not a file: '{path}'")

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise WorkflowParseError(f"Failed to read workflow file '{path}': {exc}") from exc

    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_workflow_json(content)
    elif suffix in (".yaml", ".yml"):
        return parse_workflow_yaml(content)
    else:
        return parse_workflow_yaml(content)
