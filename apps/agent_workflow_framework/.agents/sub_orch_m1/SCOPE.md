# Scope: Milestone 1 — Workflow Engine Core & DAG Resolution

## Overview
Implement the core data models, definition parser, DAG construction graph, topological sorting, and cyclic dependency / syntax validation.

## Target Files
- `agent_workflow/__init__.py`
- `agent_workflow/models.py`
- `agent_workflow/parser.py`
- `agent_workflow/dag.py`
- `tests/test_dag.py`

## Assigned Features
- `FEAT-ENG-01`: Workflow Definition Schema & Parsing (YAML & JSON definitions into dataclasses)
- `FEAT-ENG-02`: DAG Dependency Graph & Topological Sorting (`graphlib.TopologicalSorter`)
- `FEAT-ENG-03`: Cyclic Dependency & Syntax Validation (Kahn's / DFS cycle detection, invalid dependency error reporting)

## Iteration Loop
Run Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop until all gate criteria pass.

## Verification Requirements
- `python -m unittest discover -s tests` must pass with 0 failures.
- Zero cyclic dependency false positives/negatives.
- Reviewers APPROVE, Challenger APPROVE, Auditor CLEAN.
