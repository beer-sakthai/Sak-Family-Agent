"""DAG dependency resolution, topological batching, and cycle/syntax validation."""

import graphlib
from typing import List, Dict, Set
from agent_workflow.models import WorkflowDefinition, StepDefinition


def validate_workflow_dag(workflow: WorkflowDefinition) -> List[str]:
    """Validates workflow step dependencies.

    Returns:
        List[str]: A list of validation error messages. An empty list indicates a valid DAG.
    """
    errors: List[str] = []

    if not workflow.steps:
        errors.append("Workflow must contain at least one step.")
        return errors

    seen_ids: Set[str] = set()
    duplicate_ids: Set[str] = set()
    step_map: Dict[str, StepDefinition] = {}

    # Check 1: Empty/Invalid IDs and Duplicate IDs
    for step in workflow.steps:
        if not step.id or not isinstance(step.id, str) or not step.id.strip():
            errors.append(f"Step has empty or invalid ID: '{step.id}'")
            continue

        if step.id in seen_ids:
            if step.id not in duplicate_ids:
                duplicate_ids.add(step.id)
                errors.append(f"Duplicate step ID found: '{step.id}'")
        else:
            seen_ids.add(step.id)
            step_map[step.id] = step

    # Check 2: Self-dependencies and Missing Dependencies
    for step in workflow.steps:
        if not step.id or not isinstance(step.id, str) or not step.id.strip():
            continue
        for dep in step.depends_on:
            if dep == step.id:
                errors.append(f"Step '{step.id}' cannot depend on itself")
            elif dep not in seen_ids:
                errors.append(f"Step '{step.id}' depends on non-existent step '{dep}'")

    # Check 3: Cyclic Dependency Detection via TopologicalSorter
    graph: Dict[str, Set[str]] = {}
    for step_id, step in step_map.items():
        # Include only valid, known step dependencies in graph to isolate structural cycles
        valid_deps = {dep for dep in step.depends_on if dep in seen_ids and dep != step_id}
        graph[step_id] = valid_deps

    try:
        ts = graphlib.TopologicalSorter(graph)
        ts.prepare()
    except graphlib.CycleError as e:
        errors.append(f"Cyclic dependency detected in workflow: {e}")

    return errors


def build_topological_batches(workflow: WorkflowDefinition) -> List[List[StepDefinition]]:
    """Groups workflow steps into parallel execution batches in topological order.

    Steps within the same batch have all dependencies satisfied by prior batches and
    can be executed concurrently.

    Args:
        workflow: The workflow definition to batch.

    Returns:
        List[List[StepDefinition]]: Batches of steps ordered sequentially.

    Raises:
        ValueError: If the workflow DAG is invalid.
    """
    errors = validate_workflow_dag(workflow)
    if errors:
        raise ValueError(f"Invalid workflow DAG: {'; '.join(errors)}")

    step_map: Dict[str, StepDefinition] = {step.id: step for step in workflow.steps}
    graph: Dict[str, Set[str]] = {step.id: set(step.depends_on) for step in workflow.steps}

    ts = graphlib.TopologicalSorter(graph)
    ts.prepare()

    batches: List[List[StepDefinition]] = []
    # Map step ID to original list index to enforce intra-batch deterministic ordering
    step_order_index = {step.id: idx for idx, step in enumerate(workflow.steps)}

    while ts.is_active():
        ready_ids = ts.get_ready()
        if not ready_ids:
            break
        # Preserve original declaration order for steps within the same batch
        sorted_ready_ids = sorted(ready_ids, key=lambda s_id: step_order_index[s_id])
        batch = [step_map[s_id] for s_id in sorted_ready_ids]
        batches.append(batch)
        for s_id in ready_ids:
            ts.done(s_id)

    return batches
