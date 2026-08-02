# Specification Mining Report: Python Agent Workflow Framework

**Author**: Specification Miner 3  
**Date**: 2026-08-01  
**Target Project**: Python Agent Workflow Framework & CLI Tool (`agent_workflow_framework`)  
**Specification Sources**: `ORIGINAL_REQUEST.md`, `DISPATCH.md`, CLI & Python System Conventions  

---

## 1. Overview & Architectural Scope

The Python Agent Workflow Framework is a lightweight, high-reliability Python library and CLI tool designed to define, validate, execute, monitor, and inspect multi-step agent workflows. Workflows are defined as Directed Acyclic Graphs (DAGs) of steps, where steps can execute sequentially or in parallel, exchange input/output state, automatically retry upon failure, and record structured execution logs.

Key System Goals:
1. **DAG Graph Management**: Parse workflow definitions (YAML/JSON), construct dependency graphs, validate acyclicity (detect cycles), detect deadlocks/unreachable nodes, and compute topological execution orders.
2. **State & Context Engine**: Support global workflow context and step-to-step state passing via variable interpolation (e.g., `${steps.step_id.output.key}`).
3. **Execution Runtime**: Asynchronous/concurrent worker pool supporting parallel step execution when dependencies allow, configurable worker limits, and step timeout management.
4. **Resilience & Error Handling**: Configurable step-level retries with backoff, isolation of step failures, short-circuiting downstream dependent steps, and capturing detailed error tracebacks.
5. **CLI Interface**: Standard POSIX CLI commands (`validate`, `run`, `inspect`) with ANSI TTY live progress reporting, structured JSON/YAML output flags, and standard process exit codes (0, 1, 2).
6. **Audit & Log Persistence**: Structured storage (JSON files or SQLite database) recording full workflow run history, step execution timelines, inputs, outputs, and exception reports.
7. **Automated Verification Suite**: Self-contained verification harness (`verify.py`) running automated test scenarios across linear, parallel DAG, failure/retry, and complex state mutation patterns.

---

## 2. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Definition Schema | YAML/JSON Workflow Parser | Load and validate workflow definition files containing workflow metadata, inputs, and step list | File path (YAML/JSON file) | `WorkflowDefinition` model object | Raises `WorkflowValidationError` on syntax error or schema invalidity | `ORIGINAL_REQUEST.md` R1 |
| 2 | DAG Validation | Cyclic Dependency Detection | Detect cycles in step dependency graphs using Kahn's algorithm / Tarjan's SCC / DFS before execution | Step dependency lists (`depends_on`) | Cycle detection report (boolean + cycle path if present) | Prevents run; returns validation error & exit code 2 in CLI | `ORIGINAL_REQUEST.md` R2, AC |
| 3 | DAG Validation | Undefined Dependency Check | Verify that all step IDs listed in `depends_on` exist within the workflow definition | Step dependencies | List of invalid step references | Raises `WorkflowValidationError` listing missing step IDs | `ORIGINAL_REQUEST.md` R1 |
| 4 | DAG Validation | Topological Sorter | Order step execution levels so upstream dependencies always finish before downstream steps execute | Dependency graph | Execution groups / topological order list | Raises error if graph cannot be topologically sorted | Architecture Analysis |
| 5 | State Passing | Variable Interpolation Engine | Resolve downstream step input parameters using `${steps.STEP_ID.output.FIELD}` or `${inputs.PARAM}` syntax | Template string, Execution State Context | Resolved value (str, int, dict, list, bool) | Raises `StateResolutionError` if referenced step/key missing | `ORIGINAL_REQUEST.md` R1, AC |
| 6 | State Passing | Step Output Capture | Capture return values, dictionary outputs, or stdout from step execution into execution state | Step return value / output dict | Keyed output entry in workflow run state | Captures `None` or error message if step fails | `ORIGINAL_REQUEST.md` R1, AC |
| 7 | Concurrency | Parallel Step Execution | Execute independent steps (having all dependencies satisfied) concurrently via Asyncio/ThreadPool | Ready steps pool, worker limit | Concurrent task execution results | Exception in one step does not cancel unrelated parallel steps | `ORIGINAL_REQUEST.md` R1, AC |
| 8 | Concurrency | Worker Limit Control | Restrict maximum simultaneous parallel steps via `--max-workers N` or `concurrency_limit` parameter | `max_workers` integer | Controlled concurrency pool | Rejects `max_workers <= 0` with validation error | Architecture Analysis |
| 9 | Resilience | Step Retry Engine | Re-execute failed steps up to `max_retries` (configurable per step or globally) with optional backoff | `retries` int, `backoff_factor` float | Retry attempts execution history | Exhausting retries marks step `FAILED` and halts dependent steps | `ORIGINAL_REQUEST.md` R1, AC |
| 10 | Resilience | Downstream Short-Circuiting | Automatically skip steps that depend on a `FAILED` step, setting status to `SKIPPED` | Upstream step status | Status `SKIPPED` on downstream steps | Downstream steps skip execution without throwing unhandled exceptions | Architecture Analysis |
| 11 | CLI Interface | `validate` Command | Parse and perform full static analysis on workflow file (syntax, DAG integrity, cycle check) | Path to workflow file | Text/JSON report of validity, exit code 0 or 2 | Exit code 2 on invalid definition; exit code 1 on file not found | `ORIGINAL_REQUEST.md` R2, AC |
| 12 | CLI Interface | `run` Command | Execute workflow definition, bind inputs, display live execution progress, persist run logs | Workflow file path, `--inputs key=value`, `--max-workers N`, `--log-dir PATH` | Live progress display, exit code 0 (success) or 1 (failure) | Exit code 1 on workflow execution failure; 2 on validation failure | `ORIGINAL_REQUEST.md` R2, AC |
| 13 | CLI Interface | `inspect` Command | Query historical run summaries or specific step execution outputs and logs | Run ID or log file path, optional `--step STEP_ID` | Formatted run summary table / JSON output | Exit code 1 if Run ID or log file not found | `ORIGINAL_REQUEST.md` R2, AC |
| 14 | Log Persistence | Structured Run Logger | Record run metadata, step timelines, inputs, outputs, attempt logs to `.workflow_runs/<run_id>.json` | Workflow execution events | JSON persistent file | File write errors handled with fallback stderr notification | `ORIGINAL_REQUEST.md` R1, AC |
| 15 | Live Progress | ANSI Progress Renderer | Render dynamic live status matrix in terminal (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED) | Step state updates | Formatted terminal output / TTY rendering | Automatically falls back to plain text log output in non-TTY environments | `ORIGINAL_REQUEST.md` R2 |
| 16 | Verification | Automated Test Harness (`verify.py`) | Execute comprehensive verification suite (Linear, Parallel DAG, Retry, State Mutation scenarios) | None | Scenario test results, summary output, exit code 0 | Exit code 1 if any scenario fails | `ORIGINAL_REQUEST.md` R3, AC |

---

## 3. Edge Cases & Boundary Conditions

| # | Feature | Input / Condition | Expected / Observed Behavior |
|---|---------|-------------------|------------------------------|
| 1 | DAG Parsing | Empty workflow file or empty `steps` array | Reject during validation with `WorkflowValidationError: Workflow must define at least one step.` |
| 2 | DAG Parsing | Duplicate step IDs in same workflow definition | Reject during validation with `WorkflowValidationError: Duplicate step ID 'step_x' detected.` |
| 3 | DAG Parsing | Self-referencing step (`depends_on: ["step_a"]` on `step_a`) | Detect 1-node cycle during validation; output `Cyclic dependency detected: step_a -> step_a`. Exit code 2. |
| 4 | DAG Parsing | Direct 2-node cycle (`A -> B -> A`) | Detect cycle `A -> B -> A` during validation. Exit code 2. |
| 5 | DAG Parsing | Indirect multi-node cycle (`A -> B -> C -> D -> B`) | Detect cycle `B -> C -> D -> B` during validation; print exact path of cycle. Exit code 2. |
| 6 | DAG Parsing | Reference to non-existent step ID in `depends_on` | Validation failure: `Undefined dependency 'step_missing' referenced by 'step_b'`. Exit code 2. |
| 7 | State Passing | State interpolation references missing upstream step | Runtime failure during state resolution: `StateResolutionError: Step 'step_x' was not executed or found.` |
| 8 | State Passing | State interpolation references missing field in step output | Evaluate to `None` or raise `StateResolutionError` with clear field path error message. |
| 9 | State Passing | Parallel steps writing to state store simultaneously | State store must use thread-safe lock or immutable dict updates to prevent race conditions. |
| 10 | Concurrency | `max_workers=1` (forced sequential execution) | Parallel steps run sequentially in topological order; full workflow still succeeds. |
| 11 | Concurrency | High concurrency (`max_workers=100`) on small DAG | Engine caps active concurrent workers to available ready steps count without crashing. |
| 12 | Retry Engine | Step fails on attempt 1 & 2, succeeds on attempt 3 (when `retries: 3`) | Step marked `COMPLETED` on attempt 3; run context receives output; downstream steps execute normally. |
| 13 | Retry Engine | Step fails on all 4 attempts (1 initial + 3 retries) | Step marked `FAILED`; attempt history logged; downstream dependent steps marked `SKIPPED`; workflow marked `FAILED`. |
| 14 | Resilience | Branch failure in parallel DAG (Branch A fails, Branch B succeeds) | Branch B and its independent downstream steps execute to completion; Branch A's downstream steps marked `SKIPPED`. Overall workflow status: `FAILED`. |
| 15 | CLI Interface | Running `run` on invalid workflow definition | Static validation triggers first; prints validation errors; terminates immediately with exit code 2 (no execution attempted). |
| 16 | CLI Interface | Passing non-existent file path to `validate` or `run` | Print `Error: File not found: <path>`; exit code 1. |
| 17 | CLI Interface | User presses `Ctrl+C` (SIGINT) during workflow run | Gracefully cancel running step tasks, mark run as `CANCELLED`, write run log, print interruption message, exit code 130 or 1. |
| 18 | State Persistence | Persistence directory `.workflow_runs/` does not exist | Automatically create directory with `mode 0755` prior to writing log files. |
| 19 | Inspect Tool | Inspecting invalid / non-existent `run_id` | Print `Error: Run ID 'invalid_id' not found in history store.`; exit code 1. |
| 20 | Step Execution | Step output contains non-JSON-serializable objects (e.g. custom class instance) | Serialization handler converts to `str(obj)` or dict representation before saving to persistent JSON store. |

---

## 4. Subsystem Specifications

### 4.1 Workflow Definition Schema & Step Specifications

Workflows must be representable in **YAML** or **JSON** format.

#### 4.1.1 Workflow Definition Structure
```yaml
name: string            # Human-readable workflow name (required)
description: string     # Optional description
version: string         # Schema version (default: "1.0")
inputs:                 # Global workflow input parameter definitions (optional)
  param_name:
    type: string | int | float | bool | json
    default: any
    description: string
steps:                  # Array of step definitions (required, non-empty)
  - id: string          # Unique step identifier (required, alphanumeric + underscores)
    name: string        # Display name (optional)
    handler: string     # Python function specifier or step type identifier (required)
    depends_on: [str]   # List of upstream step IDs that must complete first (optional, default: [])
    inputs: dict        # Key-value map of input arguments to pass to handler (optional)
    retries: int        # Max retry attempts on failure (optional, default: 0)
    retry_delay: float  # Seconds to wait between retries (optional, default: 1.0)
    timeout: float      # Timeout limit in seconds (optional, default: null)
```

#### 4.1.2 Step Handlers
Supported handler formats:
1. **Python Module Function**: `package.module.function_name` (e.g. `workflow_engine.handlers.echo`).
2. **Built-in Step Types**:
   - `builtin.echo`: Echos input message.
   - `builtin.shell`: Executes shell command.
   - `builtin.transform`: Performs JSON/dict transformation.
   - `builtin.mock_llm`: Mocks an agent/LLM completion.
   - `builtin.fail`: Utility handler that throws an error (for testing retry/failure logic).

---

### 4.2 DAG Validation & Topological Sorting Specs

Validation must execute **statically** before any workflow execution begins.

#### 4.2.1 Validation Rules & Constraints
1. **Schema Integrity**: Workflow must contain non-empty `name` and `steps` list.
2. **Step ID Uniqueness**: All step IDs must be unique within the workflow. Step ID format regex: `^[a-zA-Z0-9_-]+$`.
3. **Dependency Existence**: Every ID listed in `depends_on` must refer to a step defined in the same workflow.
4. **Acyclicity Check (Cycle Detection)**:
   - Construct directed graph $G = (V, E)$ where $V = \text{steps}$ and edge $(u, v) \in E$ means step $v$ depends on step $u$.
   - Execute cycle detection using **Kahn's Algorithm** (in-degree tracking) or **Tarjan's / DFS color-marking algorithm**.
   - If a cycle is detected, report the exact cycle path (e.g., `step_a -> step_b -> step_c -> step_a`).
5. **Validation Output**:
   - Status: `VALID` or `INVALID`.
   - Error List: Detailed diagnostic messages for each validation failure.

---

### 4.3 Step Execution & State Passing Specs

#### 4.3.1 Context State Structure
The global workflow execution state is structured as:
```json
{
  "run_id": "run_20260801_182432_a1b2c3",
  "workflow_name": "example_workflow",
  "status": "RUNNING",
  "inputs": {
    "query": "hello world",
    "batch_size": 10
  },
  "steps": {
    "step_1": {
      "status": "COMPLETED",
      "attempts": 1,
      "output": {
        "processed_text": "HELLO WORLD",
        "count": 11
      },
      "error": null
    }
  }
}
```

#### 4.3.2 Variable Interpolation Engine
Step `inputs` values can use standard string interpolation syntax to reference workflow inputs and prior step outputs:
- Workflow input reference: `${inputs.PARAM_NAME}`
- Upstream step output reference: `${steps.STEP_ID.output.KEY}` or `${steps.STEP_ID.output}`
- Entire upstream output binding: If `inputs: { data: "${steps.step1.output}" }`, the engine evaluates `${steps.step1.output}` to the actual data structure (dict, list, int, etc.), not just string representation.

#### 4.3.3 Output Capture Mechanics
- Each step handler returns a dictionary or serializable object.
- The returned value is saved under `state["steps"][step_id]["output"]`.
- Step outputs are immutable once step completion is recorded.

---

### 4.4 Concurrency & Parallel Execution Mechanics

#### 4.4.1 Parallel Execution Algorithm
1. Build in-degree map for all steps in the DAG.
2. Initialize `ready_queue` with all steps having in-degree 0 (no dependencies).
3. Spawn an asynchronous event loop (or worker pool) limited by `max_workers` (default: 4).
4. When a step completes successfully:
   - Decrement in-degree for all downstream steps that depend on it.
   - If a downstream step's in-degree reaches 0 AND all its upstream dependencies are `COMPLETED`, push it to `ready_queue`.
5. If a step fails (after retries):
   - Mark its downstream dependent steps as `SKIPPED`.
   - Do NOT enqueue dependent steps.
6. Execution terminates when all steps reach a terminal state (`COMPLETED`, `FAILED`, or `SKIPPED`).

---

### 4.5 Retry Mechanics, Failure Handling & Recovery Specs

#### 4.5.1 Retry Parameters
- `retries`: Integer $\ge 0$ (default: 0).
- `retry_delay`: Float seconds $\ge 0.0$ (default: 1.0).
- `backoff_factor`: Multiplier applied to `retry_delay` on consecutive retries (default: 1.0).

#### 4.5.2 Retry Logic
When step execution raises an uncaught exception:
1. Record attempt failure details (attempt number, timestamp, error message, stack trace).
2. If `attempt_count <= retries`:
   - Sleep for `retry_delay * (backoff_factor ** (attempt - 1))` seconds.
   - Re-execute step handler with identical input parameters.
3. If `attempt_count > retries`:
   - Set step status to `FAILED`.
   - Record exception details in step output state.
   - Trigger downstream short-circuiting (`SKIPPED` state for dependent nodes).

---

### 4.6 CLI Interface Specifications

The framework must provide a unified CLI executable named `agent-workflow` (or callable via `python -m workflow_engine.cli`).

#### 4.6.1 Subcommand: `validate`
- **Usage**: `agent-workflow validate <workflow_file> [--json]`
- **Arguments**:
  - `workflow_file` (Required): Path to YAML/JSON workflow definition file.
  - `--json` (Optional): Output validation report in JSON format.
- **Exit Codes**:
  - `0`: Workflow is valid.
  - `1`: File not found or unparseable JSON/YAML.
  - `2`: Workflow validation failed (cyclic dependency, invalid step IDs, schema errors).

#### 4.6.2 Subcommand: `run`
- **Usage**: `agent-workflow run <workflow_file> [--inputs KEY=VAL ...] [--max-workers N] [--log-dir PATH] [--verbose] [--dry-run]`
- **Arguments**:
  - `workflow_file` (Required): Path to YAML/JSON workflow definition.
  - `-i, --inputs KEY=VALUE`: Override/supply workflow input parameters (can be passed multiple times).
  - `-w, --max-workers N`: Maximum concurrent step executions (default: 4).
  - `-l, --log-dir PATH`: Directory for persisting run logs (default: `.workflow_runs`).
  - `-v, --verbose`: Enable detailed step output logging.
  - `--dry-run`: Perform validation and display execution plan without running steps.
- **Exit Codes**:
  - `0`: All workflow steps completed successfully.
  - `1`: Workflow execution failed (one or more steps failed).
  - `2`: Static validation failed prior to run.

#### 4.6.3 Subcommand: `inspect`
- **Usage**: `agent-workflow inspect <run_id_or_log_file> [--step STEP_ID] [--json]`
- **Arguments**:
  - `run_id_or_log_file` (Required): Run ID string or path to a `.json` execution log file.
  - `-s, --step STEP_ID` (Optional): Inspect detailed execution log for a specific step.
  - `--json` (Optional): Output result as formatted JSON.
- **Exit Codes**:
  - `0`: Inspection successful.
  - `1`: Run ID or log file not found.

---

### 4.7 Run Log Persistence Store Specs

Execution history must be written to `.workflow_runs/<run_id>.json` upon completion (or cancellation).

#### 4.7.1 Persistence JSON Schema
```json
{
  "run_id": "run_20260801_182432_a1b2c3",
  "workflow_name": "data_processing_pipeline",
  "start_time": "2026-08-01T18:24:32.100Z",
  "end_time": "2026-08-01T18:24:35.450Z",
  "duration_seconds": 3.35,
  "status": "COMPLETED",
  "inputs": {
    "input_file": "/tmp/data.csv"
  },
  "metrics": {
    "total_steps": 4,
    "completed_steps": 4,
    "failed_steps": 0,
    "skipped_steps": 0
  },
  "steps": {
    "ingest": {
      "step_id": "ingest",
      "handler": "builtin.echo",
      "status": "COMPLETED",
      "start_time": "2026-08-01T18:24:32.110Z",
      "end_time": "2026-08-01T18:24:32.300Z",
      "duration_seconds": 0.19,
      "attempts": 1,
      "inputs": {"msg": "Reading /tmp/data.csv"},
      "output": {"result": "Reading /tmp/data.csv"},
      "error": null
    }
  }
}
```

---

### 4.8 Live Progress Reporting Specs

When running interactively in a TTY:
- Render dynamic step execution table with live status updates.
- Status icons:
  - `⏳ PENDING`: Waiting for upstream dependencies.
  - `🏃 RUNNING`: Currently executing (with active duration display).
  - `✅ COMPLETED`: Successfully finished.
  - `❌ FAILED`: Step failed (with attempt count).
  - `⏭️ SKIPPED`: Skipped due to upstream failure.
- Non-TTY / Verbose Mode: Print line-by-line structured log messages (`[TIMESTAMP] [INFO] [step_id] Status updated to RUNNING`).

---

## 5. Automated Verification Test Suite Requirements

The automated verification suite must be runnable via a single command (e.g. `python -m verification.runner` or `./verify.py`) and return exit code 0 on full success.

### 5.1 Verification Scenarios

| Scenario # | Name | Target Capabilities | Description & Expected Outcome |
|------------|------|---------------------|--------------------------------|
| **Scenario 1** | Linear Workflow Execution | Sequential execution, state passing | 3-step linear DAG (`A -> B -> C`). Step A produces value `X`, Step B transforms `X` to `Y`, Step C transforms `Y` to `Z`. Verify output `Z` and strict sequential timestamps. |
| **Scenario 2** | Parallel DAG Execution | Fan-out / Fan-in, Concurrency | Workflow with Root `R`, parallel branches `B1` and `B2` (both depending on `R`), and Join step `J` (depending on `B1` and `B2`). Verify `B1` and `B2` execute concurrently and `J` receives outputs from both. |
| **Scenario 3** | Retry-on-Failure & Recovery | Step retries, Backoff, Failure propagation | Part A: Step configured with `retries: 2` fails on attempt 1, succeeds on attempt 2 -> verify workflow completion. Part B: Step configured with `retries: 1` fails both attempts -> verify step marked `FAILED`, dependent downstream steps marked `SKIPPED`, workflow exits with code 1. |
| **Scenario 4** | Complex State Mutation Pipeline | Multi-parameter interpolation, dynamic state transformations | Multi-step pipeline processing complex JSON structures, merging outputs, applying arithmetic/string operations via parameter binding `${steps.X.output.field}`. Verify end-to-end data integrity. |

---

## 6. Verification Criteria & Exit Code Rules

1. Static Validation Failure: Exit Code **2**
2. Successful Workflow Execution: Exit Code **0**
3. Failed Workflow Execution: Exit Code **1**
4. Successful CLI Inspection: Exit Code **0**
5. Inspection Target Not Found: Exit Code **1**
6. Automated Verification Runner (`verify.py`): Exit Code **0** on 100% pass, Exit Code **1** on any test failure.
