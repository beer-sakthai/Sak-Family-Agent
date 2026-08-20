# Scope: E2E Testing Track Orchestrator

## Overview
Design and implement the E2E test suite (Tiers 1-4) for the Python Agent Workflow Framework based on requirements in ORIGINAL_REQUEST.md and TEST_INFRA.md, independent of implementation details.

## Target Files
- `tests/test_workflows/linear_workflow.yaml`
- `tests/test_workflows/parallel_workflow.yaml`
- `tests/test_workflows/retry_workflow.yaml`
- `tests/test_workflows/mutation_workflow.yaml`
- `tests/test_e2e_suite.py`
- `verify.py`
- `TEST_READY.md` (publish when test suite is complete)

## Assigned Test Tiers
- Tier 1: Feature Coverage (≥5 tests per feature area)
- Tier 2: Boundary & Corner Cases (≥5 tests for cycles, retries, empty workflows, invalid keys)
- Tier 3: Pairwise Combinations (parallel + retries, parallel + state passing, state passing + failure short-circuiting)
- Tier 4: Real-World Workload Scenarios (Scenario 1 Linear, Scenario 2 Parallel DAG, Scenario 3 Failure & Retry, Scenario 4 State Mutation)

## Iteration Loop
Run Explorer -> Worker (or test_writer) -> Reviewer -> Challenger -> Auditor iteration loop until test suite is complete, valid, and executable via `python verify.py`.

## Publishing Criterion
Publish `TEST_READY.md` at project root once the full test suite and `verify.py` runner are ready.
