# Scope: Milestone 3 — Parallel Execution Engine & Retry System

## Overview
Implement the asynchronous workflow execution engine with parallel step scheduling, input/output state passing via StateContext, step action execution, configurable retries with backoff, failure propagation (marking downstream dependent steps as SKIPPED), and persistent run history recording via RunHistoryStore.

## Target Files
- `agent_workflow/executor.py`
- `tests/test_executor.py`

## Assigned Features
- `FEAT-ENG-04`: Parallel Step Execution Engine (Execute independent workflow steps concurrently via `asyncio.gather` or async batch scheduling based on DAG dependency topological batches)
- `FEAT-ENG-05`: Step Retry & Resilience Handling (Retry failed step execution up to configured `retry` attempts with `retry_delay` backoff before marking step as FAILED)
- `FEAT-ENG-06`: Downstream Failure Short-Circuiting (If an upstream step fails after exhausting retries, automatically mark all downstream steps that depend on it directly or transitively as SKIPPED)

## Iteration Loop
Run Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop until all gate criteria pass.

## Verification Requirements
- `python -m unittest discover -s tests` must pass with 0 failures.
- Unit tests verifying parallel timing (e.g. 3 independent 0.5s sleep steps execute concurrently in ~0.5s total time rather than 1.5s).
- Unit tests verifying retry recovery (transient failure succeeds on retry N) and retry exhaustion (terminal failure after max retries).
- Unit tests verifying downstream short-circuiting (dependent step marked SKIPPED when upstream fails).
- Reviewers APPROVE, Challenger APPROVE, Auditor CLEAN.
