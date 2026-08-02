# Scope: Milestone 2 — State Passing & Execution Persistence

## Overview
Implement input/output state context, expression template interpolation (`${steps.ID.output.KEY}`), run history management, and step-level log store persistence under `.workflow_runs/`.

## Target Files
- `agent_workflow/state.py`
- `agent_workflow/persistence.py`
- `tests/test_state.py`
- `tests/test_persistence.py`

## Assigned Features
- `FEAT-STA-01`: Input/Output State Passing & Interpolation (`${steps.ID.output.KEY}` syntax, dictionary & string template resolution, nested path extraction)
- `FEAT-STA-02`: History Store & Log Persistence (Save structured `RunHistory` and `StepResult` to `.workflow_runs/<run_id>.json`, thread-safe/atomic file writes)

## Iteration Loop
Run Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop until all gate criteria pass.

## Verification Requirements
- `python -m unittest discover -s tests` must pass with 0 failures.
- State interpolation unit tests verifying string, dict, list, int, bool, float interpolation and invalid reference exceptions (`KeyError`/`StateInterpolationError`).
- Log persistence unit tests verifying JSON serialization, deserialization, directory creation, and atomic file creation under `.workflow_runs/`.
- Reviewers APPROVE, Challenger APPROVE, Auditor CLEAN.
