# Milestone M6: Adversarial Hardening & Security Audit Design Spec

## Overview
This specification details the Tier 5 Adversarial Hardening for `agent_workflow_framework`. It addresses path traversal security vulnerabilities in logging/persistence, circular state interpolation bombs, scale bounds (1,000-node DAGs), and high-concurrency race condition safety.

## Module Hardening Specifications

### 1. `agent_workflow/persistence.py` — Path Traversal Prevention
- **Constraint**: `run_id` parameters passed to `RunHistory` creation or query methods must match `^[a-zA-Z0-9_-]+$`.
- **Behavior**: If `run_id` contains path traversal characters (`..`, `/`, `\`) or invalid symbols, raise `ValueError("Path traversal attempt detected in run_id")`.

### 2. `agent_workflow/state.py` — Interpolation Depth Guard
- **Constraint**: Limit state expression resolution to a maximum depth of 10 recursive levels.
- **Behavior**: Track resolution depth during `${steps.ID.output.KEY}` evaluation. If depth exceeds 10, raise `ValueError("Circular or nested state interpolation depth exceeded")`.

### 3. `agent_workflow/dag.py` — High-Scale Stack Safety
- **Constraint**: Cycle detection and topological sorting for DAGs up to 1,000 nodes must execute without raising `RecursionError`.
- **Behavior**: Use stack-based / iterative graph traversal (`graphlib.TopologicalSorter` or explicit stack).

## Test Suite Specifications (`tests/test_adversarial.py`)

1. `test_path_traversal_attack_vector()`: Verify path traversal payloads fail safely.
2. `test_interpolation_infinite_recursion()`: Verify circular state references fail with `ValueError`.
3. `test_scale_1000_nodes_dag()`: Verify a 1,000-node DAG validates and executes in under 2.0 seconds.
4. `test_high_concurrency_race_condition()`: Verify 50 concurrent async steps updating `StateContext` produce clean results.
5. `test_malformed_definition_fuzzing()`: Verify malformed inputs (invalid types, negative retry counts, empty keys) raise appropriate `WorkflowParseError` or `ValueError`.

## Integration
- Integrate `tests/test_adversarial.py` into `verify.py` as Phase 2.
