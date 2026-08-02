# Handoff Report: DAG Dependency Engine & Validation Design (`agent_workflow/dag.py` & `tests/test_dag.py`)

**Author**: `explorer_m1_3`  
**Milestone**: M1 — Workflow Engine Core & DAG Resolution  
**Target Files**: `agent_workflow/dag.py`, `tests/test_dag.py`  
**Target Features**: `FEAT-ENG-02` (DAG Dependency Graph & Topological Sorting), `FEAT-ENG-03` (Cyclic Dependency & Syntax Validation)

---

## 1. Observation

1. **Project Specification & Interface Contract** (`PROJECT.md` lines 8-9 & lines 133-143):
   - `agent_workflow/dag.py` is tasked with graph construction, topological sorting (`graphlib.TopologicalSorter`), and cycle detection algorithms.
   - Interface contracts defined in `PROJECT.md`:
     ```python
     def validate_workflow_dag(workflow: WorkflowDefinition) -> List[str]:
         """Validates workflow step dependencies. Returns a list of validation error strings.
         Empty list indicates valid DAG."""
         ...

     def build_topological_batches(workflow: WorkflowDefinition) -> List[List[StepDefinition]]:
         """Returns steps grouped into parallel execution batches in topological order."""
         ...
     ```

2. **Milestone 1 Scope & Gate Requirements** (`.agents/sub_orch_m1/SCOPE.md` lines 11-23):
   - Scope includes `agent_workflow/dag.py` and `tests/test_dag.py`.
   - Feature IDs: `FEAT-ENG-02` (DAG sorting via `graphlib.TopologicalSorter`) and `FEAT-ENG-03` (Cyclic dependency & validation error reporting).
   - Gate verification criteria: `python -m unittest discover -s tests` must pass with 0 failures; zero cyclic dependency false positives/negatives.

3. **Test Infrastructure Guidelines** (`TEST_INFRA.md` lines 10-11 & lines 32-35):
   - Tier 1: ≥5 test cases per feature area.
   - Tier 2: ≥5 boundary & corner case tests (cycles, invalid keys, empty graphs, self-deps, duplicate step IDs).
   - Unit test command: `python -m unittest discover -s tests`.

4. **Python Standard Library `graphlib.TopologicalSorter` Behavior**:
   - Available natively in Python 3.9+.
   - Expects a dictionary mapping node IDs to sets of predecessor node IDs (dependencies): `{node_id: {dep1_id, dep2_id}}`.
   - `ts.prepare()` raises `graphlib.CycleError` when a cycle exists. `e.args` contains `('nodes are in a cycle', ['nodeA', 'nodeB', 'nodeA'])`.
   - `ts.get_ready()` returns a tuple of ready node IDs (in-degree 0). Calling `ts.done(node_id)` marks a node complete and unlocks downstream nodes for subsequent `ts.get_ready()` calls.
   - `TopologicalSorter` does **NOT** validate whether referenced predecessor IDs exist in the input keys; missing step IDs are treated as root nodes without dependencies unless validated beforehand.

---

## 2. Logic Chain

1. **Validation Pipeline Requirements (`validate_workflow_dag`)**:
   - *Premise*: `TopologicalSorter` cannot catch missing dependency step IDs or duplicate step IDs by itself (Observation 4).
   - *Step 1*: Before graph sorting, `validate_workflow_dag` must perform static structure checks:
     a. Empty workflow check (`len(workflow.steps) == 0`).
     b. Step ID validation (non-empty, non-whitespace string).
     c. Duplicate step ID detection across `workflow.steps`.
     d. Self-dependency detection (`step.id in step.depends_on`).
     e. Missing dependency step ID detection (`dep_id not in known_step_ids`).
   - *Step 2*: After static checks, build the graph mapping `{step_id: set(step.depends_on)}` for valid step IDs and invoke `graphlib.TopologicalSorter(graph).prepare()`.
   - *Step 3*: Catch `graphlib.CycleError` and format the cycle path cleanly as `"Cyclic dependency detected: stepA -> stepB -> stepA"`.
   - *Step 4*: Accumulate all detected validation errors into a `List[str]` and return it. An empty list indicates a valid DAG.

2. **Parallel Batching Algorithm (`build_topological_batches`)**:
   - *Premise*: Workflow engine parallel execution (M3) requires step execution batches where steps in each batch are independent and can run concurrently.
   - *Step 1*: `build_topological_batches` must first run `validate_workflow_dag(workflow)`. If validation errors exist, raise `ValueError` with detailed error descriptions.
   - *Step 2*: Initialize `graphlib.TopologicalSorter(graph)` with step dependencies.
   - *Step 3*: Loop while `ts.is_active()`: call `ts.get_ready()`, map step IDs back to `StepDefinition` instances, record the batch, and call `ts.done(step_id)` for each step in the batch.
   - *Step 4*: To ensure deterministic test execution across Python versions and dictionary orderings, sort steps within each batch according to their declaration order in `workflow.steps`.

3. **Test Suite Architecture (`tests/test_dag.py`)**:
   - *Premise*: Verification requires zero false positives/negatives and Tier 1 / Tier 2 coverage compliance (Observation 2 & 3).
   - *Test Organization*: Two `unittest.TestCase` test classes:
     - `TestValidateWorkflowDAG`: 12 test scenarios covering linear DAG, parallel DAG, disconnected components, single step, empty workflow, duplicate step IDs, missing dependency IDs, self-dependencies, direct 2-node cycle, indirect 3-node cycle, cycle in sub-component, and multiple aggregated errors.
     - `TestBuildTopologicalBatches`: 8 test scenarios covering linear workflow batching, fan-out batching, fan-in batching, diamond DAG batching, disconnected subgraph batching, single step batching, invalid DAG exception raising, and intra-batch execution order determinism.

---

## 3. Caveats

- **Caveat 1**: `graphlib.TopologicalSorter` returns one cycle per `prepare()` invocation. If a graph contains multiple disjoint cycles, `validate_workflow_dag` will detect the first cycle reported by `TopologicalSorter`. Fixing the reported cycle and re-validating will surface any remaining disjoint cycles.
- **Caveat 2**: `StepDefinition` and `WorkflowDefinition` dataclasses reside in `agent_workflow/models.py`. Implementer worker for `dag.py` should import from `agent_workflow.models`.
- **Caveat 3**: No external dependencies (e.g. `networkx`) should be added to `pyproject.toml` for DAG processing, as `graphlib` is built into Python 3.9+ standard library.

---

## 4. Conclusion & Proposed Code Implementation

`agent_workflow/dag.py` should be implemented using Python's standard library `graphlib.TopologicalSorter` combined with strict pre-validation checks for duplicate IDs, missing dependency IDs, self-dependencies, and empty workflows. `tests/test_dag.py` should implement 20 test cases divided into validation and batching suites.

### Proposed Implementation for `agent_workflow/dag.py`:

```python
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
        if not step.id or not step.id.strip():
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
        if not step.id or not step.id.strip():
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
        if len(e.args) >= 2 and isinstance(e.args[1], list):
            cycle_path = " -> ".join(e.args[1])
            errors.append(f"Cyclic dependency detected: {cycle_path}")
        else:
            errors.append(f"Cyclic dependency detected: {e}")

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
```

### Proposed Implementation for `tests/test_dag.py`:

```python
"""Unit tests for agent_workflow.dag module."""

import unittest
from agent_workflow.models import WorkflowDefinition, StepDefinition
from agent_workflow.dag import validate_workflow_dag, build_topological_batches


class TestValidateWorkflowDAG(unittest.TestCase):
    """Test suite for validate_workflow_dag."""

    def test_valid_linear_dag(self):
        wf = WorkflowDefinition(
            name="linear",
            steps=[
                StepDefinition(id="step1", action="echo"),
                StepDefinition(id="step2", action="echo", depends_on=["step1"]),
                StepDefinition(id="step3", action="echo", depends_on=["step2"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_valid_parallel_dag(self):
        wf = WorkflowDefinition(
            name="parallel",
            steps=[
                StepDefinition(id="start", action="echo"),
                StepDefinition(id="worker1", action="echo", depends_on=["start"]),
                StepDefinition(id="worker2", action="echo", depends_on=["start"]),
                StepDefinition(id="join", action="echo", depends_on=["worker1", "worker2"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_valid_disconnected_dag(self):
        wf = WorkflowDefinition(
            name="disconnected",
            steps=[
                StepDefinition(id="a1", action="echo"),
                StepDefinition(id="a2", action="echo", depends_on=["a1"]),
                StepDefinition(id="b1", action="echo"),
                StepDefinition(id="b2", action="echo", depends_on=["b1"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_single_step_dag(self):
        wf = WorkflowDefinition(
            name="single",
            steps=[StepDefinition(id="lone_step", action="echo")],
        )
        errors = validate_workflow_dag(wf)
        self.assertEqual(errors, [])

    def test_empty_workflow(self):
        wf = WorkflowDefinition(name="empty", steps=[])
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Workflow must contain at least one step" in err for err in errors))

    def test_duplicate_step_ids(self):
        wf = WorkflowDefinition(
            name="dup",
            steps=[
                StepDefinition(id="step1", action="echo"),
                StepDefinition(id="step1", action="echo"),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Duplicate step ID found: 'step1'" in err for err in errors))

    def test_missing_dependency(self):
        wf = WorkflowDefinition(
            name="missing_dep",
            steps=[
                StepDefinition(id="step1", action="echo", depends_on=["non_existent"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(
            any("Step 'step1' depends on non-existent step 'non_existent'" in err for err in errors)
        )

    def test_self_dependency(self):
        wf = WorkflowDefinition(
            name="self_dep",
            steps=[
                StepDefinition(id="step1", action="echo", depends_on=["step1"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Step 'step1' cannot depend on itself" in err for err in errors))

    def test_direct_cyclic_dependency(self):
        wf = WorkflowDefinition(
            name="direct_cycle",
            steps=[
                StepDefinition(id="A", action="echo", depends_on=["B"]),
                StepDefinition(id="B", action="echo", depends_on=["A"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency detected" in err for err in errors))

    def test_indirect_cyclic_dependency(self):
        wf = WorkflowDefinition(
            name="indirect_cycle",
            steps=[
                StepDefinition(id="A", action="echo", depends_on=["C"]),
                StepDefinition(id="B", action="echo", depends_on=["A"]),
                StepDefinition(id="C", action="echo", depends_on=["B"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency detected" in err for err in errors))

    def test_cycle_in_subgraph(self):
        wf = WorkflowDefinition(
            name="subgraph_cycle",
            steps=[
                StepDefinition(id="ok1", action="echo"),
                StepDefinition(id="ok2", action="echo", depends_on=["ok1"]),
                StepDefinition(id="A", action="echo", depends_on=["B"]),
                StepDefinition(id="B", action="echo", depends_on=["A"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertTrue(any("Cyclic dependency detected" in err for err in errors))

    def test_multiple_validation_errors(self):
        wf = WorkflowDefinition(
            name="multi_error",
            steps=[
                StepDefinition(id="dup", action="echo"),
                StepDefinition(id="dup", action="echo"),
                StepDefinition(id="missing", action="echo", depends_on=["ghost"]),
                StepDefinition(id="self", action="echo", depends_on=["self"]),
            ],
        )
        errors = validate_workflow_dag(wf)
        self.assertGreaterEqual(len(errors), 3)


class TestBuildTopologicalBatches(unittest.TestCase):
    """Test suite for build_topological_batches."""

    def test_linear_batches(self):
        s1 = StepDefinition(id="step1", action="echo")
        s2 = StepDefinition(id="step2", action="echo", depends_on=["step1"])
        s3 = StepDefinition(id="step3", action="echo", depends_on=["step2"])
        wf = WorkflowDefinition(name="linear", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1], [s2], [s3]])

    def test_parallel_fan_out_batches(self):
        s1 = StepDefinition(id="start", action="echo")
        s2 = StepDefinition(id="w1", action="echo", depends_on=["start"])
        s3 = StepDefinition(id="w2", action="echo", depends_on=["start"])
        wf = WorkflowDefinition(name="fan_out", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1], [s2, s3]])

    def test_parallel_fan_in_batches(self):
        s1 = StepDefinition(id="w1", action="echo")
        s2 = StepDefinition(id="w2", action="echo")
        s3 = StepDefinition(id="join", action="echo", depends_on=["w1", "w2"])
        wf = WorkflowDefinition(name="fan_in", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1, s2], [s3]])

    def test_diamond_dag_batches(self):
        s1 = StepDefinition(id="A", action="echo")
        s2 = StepDefinition(id="B", action="echo", depends_on=["A"])
        s3 = StepDefinition(id="C", action="echo", depends_on=["A"])
        s4 = StepDefinition(id="D", action="echo", depends_on=["B", "C"])
        wf = WorkflowDefinition(name="diamond", steps=[s1, s2, s3, s4])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1], [s2, s3], [s4]])

    def test_disconnected_subgraphs_batches(self):
        s1 = StepDefinition(id="a1", action="echo")
        s2 = StepDefinition(id="a2", action="echo", depends_on=["a1"])
        s3 = StepDefinition(id="b1", action="echo")
        s4 = StepDefinition(id="b2", action="echo", depends_on=["b1"])
        wf = WorkflowDefinition(name="disconnected", steps=[s1, s2, s3, s4])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1, s3], [s2, s4]])

    def test_single_step_batch(self):
        s1 = StepDefinition(id="single", action="echo")
        wf = WorkflowDefinition(name="single", steps=[s1])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1]])

    def test_invalid_dag_raises_value_error(self):
        s1 = StepDefinition(id="A", action="echo", depends_on=["B"])
        s2 = StepDefinition(id="B", action="echo", depends_on=["A"])
        wf = WorkflowDefinition(name="cyclic", steps=[s1, s2])
        with self.assertRaises(ValueError) as ctx:
            build_topological_batches(wf)
        self.assertIn("Invalid workflow DAG", str(ctx.exception))

    def test_batch_determinism(self):
        s1 = StepDefinition(id="alpha", action="echo")
        s2 = StepDefinition(id="beta", action="echo")
        s3 = StepDefinition(id="gamma", action="echo")
        wf = WorkflowDefinition(name="order", steps=[s1, s2, s3])
        batches = build_topological_batches(wf)
        self.assertEqual(batches, [[s1, s2, s3]])


if __name__ == "__main__":
    unittest.main()
```

---

## 5. Verification Method

Once implementer worker creates `agent_workflow/dag.py` and `tests/test_dag.py`:

1. **Execute Unit Test Suite**:
   ```bash
   python -m unittest discover -s tests
   ```
   *Expected output*: `Ran 20 tests in ...s - OK` with exit code 0.

2. **Direct Module Import Verification**:
   ```bash
   python -c "from agent_workflow.dag import validate_workflow_dag, build_topological_batches; print('Imports successful')"
   ```
   *Expected output*: `Imports successful`.

3. **Invalidation Conditions**:
   - Any false positive where a valid DAG returns non-empty validation errors.
   - Any false negative where a cyclic DAG returns empty error list or builds batches without raising `ValueError`.
   - Any non-deterministic batch ordering where parallel steps swap order across runs.
