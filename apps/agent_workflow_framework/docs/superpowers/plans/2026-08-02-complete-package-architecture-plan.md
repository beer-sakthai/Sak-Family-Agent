# Complete Package Architecture Implementation Plan

## Goal
Promote `agent_workflow` to a complete, standalone Python package by implementing `agent_workflow/executor.py` and `agent_workflow/cli.py`, expanding built-in actions (`shell`, `python`, `http_request`, `file_write`, `file_read`), adding CLI inspection tools, and updating test suites.

## Tasks

### Task 1: Create `agent_workflow/executor.py`
- [ ] Implement `WorkflowExecutor` with built-in action handlers: `echo`, `shell`, `python`, `http_get`, `file_write`, `file_read`.
- [ ] Implement parallel batch execution using `asyncio.gather` and state interpolation.
- [ ] Implement step retry loop with backoff and downstream failure short-circuiting (`SKIPPED`).
- [ ] Verification: `python3 -m unittest tests/test_executor.py` passes cleanly.

### Task 2: Create `agent_workflow/cli.py`
- [ ] Implement Typer / argparse CLI providing `validate`, `run`, `inspect`, and `list` subcommands.
- [ ] Standardize exit codes: 0 (success), 1 (runtime execution error), 2 (validation / syntax error).
- [ ] Add rich formatted terminal table and JSON output rendering.
- [ ] Verification: `python3 -m unittest tests/test_cli.py` passes cleanly.

### Task 3: Update `agent_workflow/__init__.py`
- [ ] Export `WorkflowExecutor`, `main`, `cli_main`, `HistoryStore`, `RunHistoryStore`, `StateContext`, `WorkflowDefinition`, `parse_workflow_file`.
- [ ] Verification: Package imports `from agent_workflow import WorkflowExecutor, main` resolve without error.

### Task 4: Unit Test Suite Expansion
- [ ] Create `tests/test_executor.py` testing all action handlers and edge cases.
- [ ] Create `tests/test_cli.py` testing all CLI subcommands and exit codes.
- [ ] Verification: `python3 -m unittest discover -s tests` runs 130+ tests with 100% PASS.

### Task 5: Master `verify.py` Integration & Final E2E Test
- [ ] Update `verify.py` to import directly from `agent_workflow` package.
- [ ] Verification: `python3 verify.py` passes all phases and E2E scenarios cleanly.
