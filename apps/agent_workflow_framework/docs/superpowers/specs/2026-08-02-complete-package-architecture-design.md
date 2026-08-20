# Complete Package Architecture Upgrade Design Spec

## Overview
This specification details the extraction and implementation of `agent_workflow/executor.py` and `agent_workflow/cli.py` as first-class, production-grade modules in the `agent_workflow` Python package. It expands action handlers (`echo`, `shell`, `python`, `http_request`, `file_write`, `file_read`), adds CLI `inspect` and `list` subcommands, and integrates complete unit & E2E verification.

## Module Specifications

### 1. `agent_workflow/executor.py`
- **Class `WorkflowExecutor`**:
  - `async execute_workflow(workflow: WorkflowDefinition, run_id: Optional[str] = None, status_callback: Optional[Any] = None) -> RunHistory`
  - Action dispatching:
    - `echo`: Return `{"msg": interpolated_param}`.
    - `shell` / `command`: Execute via `asyncio.create_subprocess_exec` / `shell`, return `{"stdout": ..., "stderr": ..., "exit_code": ...}`.
    - `python`: Execute expression/code block, return `{"result": ...}`.
    - `http_get` / `http_request`: Fetch URL using `urllib.request` / `asyncio`, return `{"status_code": ..., "body": ..., "json": ...}`.
    - `file_write`: Write text to specified file path, return `{"path": ..., "bytes_written": ...}`.
    - `file_read`: Read text from file path, return `{"content": ..., "size": ...}`.

### 2. `agent_workflow/cli.py`
- Entry point `main(args: Optional[List[str]] = None) -> int`.
- Commands:
  - `validate <file>`: Exit code 0 (valid), 2 (invalid DAG/syntax).
  - `run <file> [--run-id ID]`: Exit code 0 (completed), 1 (failed execution), 2 (invalid syntax).
  - `inspect <run_id> [--step STEP_ID]`: Display formatted JSON/table summary of stored run history.
  - `list`: Display table of saved runs in `.workflow_runs/`.

### 3. `agent_workflow/__init__.py`
- Re-export `WorkflowExecutor`, `StateContext`, `RunHistoryStore`, `main`, `cli_main`, `WorkflowDefinition`, `parse_workflow_file`.

### 4. Verification Suite Updates
- `tests/test_executor.py`: Verify all action handlers, retry logic, and short-circuiting.
- `tests/test_cli.py`: Verify CLI subcommands and exit codes.
- `verify.py`: Import directly from `agent_workflow` package.
