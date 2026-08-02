# Comprehensive Requirements Analysis & Feature Inventory

**Project**: Python Agent Workflow Framework & CLI Tool  
**Author**: Requirements Explorer 2  
**Working Directory**: `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_survey_2`  
**Date**: 2026-08-01  

---

## 1. Executive Summary

This document provides a comprehensive requirements analysis and feature breakdown for the **Python Agent Workflow Framework**. The framework is designed to define, validate, execute, monitor, and inspect multi-step agent workflows. Key capabilities include step dependency resolution via Directed Acyclic Graphs (DAGs), dynamic state passing between steps, parallel execution of independent tasks, configurable step-level retry mechanisms, structured history persistence, a feature-rich CLI, and a self-contained automated verification suite.

The analysis decomposes the primary requirements (**R1**, **R2**, **R3**) from `ORIGINAL_REQUEST.md` into granular functional requirements, implicit technical requirements, edge cases, system constraints, and a complete candidate **Feature Inventory**.

---

## 2. Granular Requirements Breakdown

### R1. Workflow Engine & Execution State

**Core Objective**: Build a Python engine capable of loading workflow definitions, resolving step dependency graphs (DAGs), executing steps with input/output state passing, supporting parallel step execution when dependencies allow, and handling retries/failures gracefully.

#### 2.1 Functional Sub-components & Detailed Analysis

1. **Workflow Definition Schema & Parser**
   - *Explicit Requirement*: Load workflow definitions from file specifications (YAML or JSON format).
   - *Implicit Requirement*: Provide clean data models (`WorkflowDef`, `StepDef`, `RetryPolicy`, `ActionDef`) with schema validation (checking for required keys like step `id`, `action`, `depends_on`, `inputs`, `retry`).
   - *Constraints & Edge Cases*: Malformed YAML/JSON, missing mandatory fields, duplicate step IDs, unsupported action types.

2. **DAG Resolution & Cycle Detection**
   - *Explicit Requirement*: Resolve step dependency graphs (DAGs) and detect circular dependencies.
   - *Implicit Requirement*: Implement graph analysis algorithms (e.g., Kahn's Algorithm or DFS-based cycle detection) to compute topological sorting order and detect cyclic dependency loops prior to execution.
   - *Constraints & Edge Cases*: Self-referential dependencies (`A -> A`), indirect cycles (`A -> B -> C -> A`), disconnected graph components (multiple root nodes or independent execution branches), orphan dependencies (referencing a non-existent step ID).

3. **Execution Planner & Topological Scheduler**
   - *Explicit Requirement*: Execute independent workflow steps in parallel when dependencies permit.
   - *Implicit Requirement*: Maintain dynamic step state progression (`PENDING` -> `READY` -> `RUNNING` -> `COMPLETED` / `FAILED` / `SKIPPED` / `RETRYING`). Manage a ready-queue of steps whose parent dependencies are all satisfied with `COMPLETED` status.
   - *Constraints & Edge Cases*: Deadlocks due to unresolved dependencies, race conditions when multiple parallel steps finish simultaneously.

4. **Step Execution Engine & Action Handlers**
   - *Explicit Requirement*: Execute steps with input/output state passing.
   - *Implicit Requirement*: Support configurable step actions (e.g., Python callables, shell commands, inline scripts, synthetic agent actions). Each step must capture stdout/stderr, return values/dictionaries, execution duration, and unhandled exceptions.
   - *Constraints & Edge Cases*: Step timeouts, non-zero process exit codes, non-serializable step outputs, unhandled runtime exceptions.

5. **Input/Output State Passing Engine**
   - *Explicit Requirement*: Pass outputs from upstream steps as inputs to downstream steps.
   - *Implicit Requirement*: Implement dynamic state template interpolation (e.g., `${steps.step_a.output.key}` or state context mapping). Maintain global and step-local execution context.
   - *Constraints & Edge Cases*: Referencing outputs of steps that failed or were skipped, missing nested keys in output dictionary, type mismatch when passing state across steps, thread-safe access during parallel step executions.

6. **Parallel Step Executor**
   - *Explicit Requirement*: Execute independent workflow steps in parallel when dependencies permit.
   - *Implicit Requirement*: Utilize Python `asyncio` or concurrent worker pools (`ThreadPoolExecutor` / `ProcessPoolExecutor`) to execute non-dependent steps concurrently.
   - *Constraints & Edge Cases*: Thread safety of execution state updates, resource exhaustion under high concurrency, semaphore/concurrency limits.

7. **Error Handling & Configurable Retry System**
   - *Explicit Requirement*: Support configurable retry attempts for failed steps before declaring step or workflow failure.
   - *Implicit Requirement*: Per-step retry configuration (`max_retries`, `retry_delay`, `backoff_factor`). Record attempt index, delay between retries, exception messages, and tracebacks for each attempt.
   - *Constraints & Edge Cases*: Distinguishing transient errors (retryable) from fatal errors, zero retries (`max_retries: 0`), handling step failure after exhausting all retry attempts.

8. **Downstream Failure Propagation & Skipping**
   - *Explicit Requirement*: Handle failures gracefully.
   - *Implicit Requirement*: When an upstream step fails terminally (after retry exhaustion), all downstream steps directly or indirectly dependent on it must be marked as `SKIPPED` without executing. The overall workflow run status must be evaluated as `FAILED`.
   - *Constraints & Edge Cases*: Branch isolation (failure in branch A should skip A's downstream nodes, but independent branch B should continue executing if unaffected).

9. **Structured History Persistence & Log Store**
   - *Explicit Requirement*: Persist structured run histories and step-level execution logs.
   - *Implicit Requirement*: Persist run records (JSON file store or SQLite database) containing `run_id`, workflow name/path, start time, end time, overall status, total execution duration, and per-step logs (inputs, outputs, attempt count, logs, error tracebacks).
   - *Constraints & Edge Cases*: Concurrent run file writes, filesystem permissions, log file corruption prevention, atomic writes.

---

### R2. CLI Interface & Inspection Tools

**Core Objective**: Provide a command-line interface to validate workflow definitions (including detecting circular dependencies), execute workflows with real-time status output, and inspect past execution logs and step state.

#### 2.2 Functional Sub-components & Detailed Analysis

1. **CLI Framework & Command Parser**
   - *Explicit Requirement*: Command-line interface with subcommands.
   - *Implicit Requirement*: Entry point `workflow-cli` (or `python -m framework.cli`) supporting subcommands `validate`, `run`, `inspect` (and sub-actions like `inspect list`, `inspect show`).
   - *Constraints & Edge Cases*: Robust argument parsing, standard POSIX exit codes (0 for success, non-zero for validation/execution errors), clear help text (`--help`).

2. **Validation Command (`validate`)**
   - *Explicit Requirement*: `validate` command that catches syntax errors and cyclic dependency errors prior to run.
   - *Implicit Requirement*: Parse workflow definition, validate syntax and schema compliance, run cycle detection algorithm, and report result. If invalid, display exact error location or cycle path (e.g. `Cycle detected: step_a -> step_b -> step_c -> step_a`). Return exit code 0 if valid, 1 (or 2) if invalid.
   - *Constraints & Edge Cases*: File not found error handling, syntax error formatting, non-blocking check (does NOT execute workflow).

3. **Workflow Execution Command (`run`)**
   - *Explicit Requirement*: `run` command that executes a workflow definition file and displays live step execution progress.
   - *Implicit Requirement*: Load definition, run validation, initialize engine, execute workflow, and display live terminal updates (e.g., using ANSI status updates, spinners, or real-time progress bars showing step states). Upon completion, print summary table and set exit code based on workflow status.
   - *Constraints & Edge Cases*: Terminal compatibility (handling non-TTY environments gracefully), capturing SIGINT (Ctrl+C) for graceful shutdown, displaying execution metrics (total time, step count, pass/fail summary).

4. **Past Run & Step Inspection Commands (`inspect`)**
   - *Explicit Requirement*: Inspection commands to query past run status and step outputs.
   - *Implicit Requirement*:
     - `inspect list`: Display historical runs with `run_id`, timestamp, workflow name, status, duration.
     - `inspect show <run_id>`: Display detailed summary of a specific run and its step breakdown.
     - `inspect step <run_id> <step_id>` (or `--step` flag): View exact step inputs, outputs, attempt history, and error logs.
     - Support `--json` flag for machine-readable stdout output.
   - *Constraints & Edge Cases*: Non-existent `run_id` handling, pagination or clean formatting for large logs, handling partial/corrupted history records.

---

### R3. Automated Verification Suite

**Core Objective**: Provide an automated test suite and verification script that executes a comprehensive set of test workflows (linear, parallel DAG, retry-on-failure, state passing) and programmatically verifies execution correctness and exit codes.

#### 2.3 Functional Sub-components & Detailed Analysis

1. **Scenario 1: Linear Workflow & State Passing Test**
   - *Explicit Requirement*: Verify linear execution and state passing.
   - *Implicit Requirement*: Test workflow with sequential steps (`Step A -> Step B -> Step C`). Step A produces an output value; Step B reads Step A's output, transforms it, and produces a new output; Step C validates the final output state.
   - *Verification Assertions*: Sequential execution order verified via timestamps; state correctly interpolated; final run status = `SUCCESS`; exit code = 0.

2. **Scenario 2: Parallel DAG Execution Test**
   - *Explicit Requirement*: Verify parallel DAG execution.
   - *Implicit Requirement*: Diamond or multi-branch DAG workflow (`Root -> [Branch A, Branch B] -> Join`). Branch A and Branch B must execute concurrently. Join step must wait until both Branch A and Branch B complete before starting, receiving state outputs from both branches.
   - *Verification Assertions*: Execution timestamps confirm concurrency; Join step receives merged output dictionary; final run status = `SUCCESS`; exit code = 0.

3. **Scenario 3: Retry-on-Failure & Failure Recovery Test**
   - *Explicit Requirement*: Verify failure & retry mechanisms.
   - *Implicit Requirement*:
     - *Sub-case A (Recovery)*: Step configured with `max_retries: 2` fails on first execution attempt but succeeds on second attempt. Engine retries step, updates attempt log, and continues workflow to completion.
     - *Sub-case B (Exhaustion & Skipping)*: Step configured with `max_retries: 1` fails on all attempts. Engine marks step `FAILED`, marks downstream steps `SKIPPED`, and marks workflow status `FAILED`.
   - *Verification Assertions*: Retry attempt history correctly logged; transient failure recovers to `SUCCESS`; terminal failure results in skipped dependents and overall `FAILED` exit code.

4. **Scenario 4: Complex State Mutation & Transformation Test**
   - *Explicit Requirement*: Verify complex state mutation and state passing pipeline.
   - *Implicit Requirement*: Workflow with multiple steps mutating shared state or passing structured data objects (lists/dictionaries) across parallel and sequential branches.
   - *Verification Assertions*: State immutability/isolation between steps preserved; thread-safe state merging; final state matching expected analytical computation.

5. **Automated Verification Script (`verify.py`)**
   - *Explicit Requirement*: Automated test suite and verification script that executes automatically and passes with return code 0.
   - *Implicit Requirement*: A self-contained Python script (`verify.py` or `pytest` suite) that programmatically executes all 4 test scenarios, validates engine behaviors, verifies state logs, checks CLI exit codes, prints structured pass/fail results, and exits with code 0 if all tests pass.
   - *Constraints & Edge Cases*: Clean test environment setup/teardown (cleaning up temporary test run persistence directories), no manual prompts required, reproducible and deterministic execution.

---

## 3. Candidate Feature Inventory

The following table provides the complete **Feature Inventory**, categorizing features by domain, mapping them to explicit/implicit requirements, defining their dependencies, and outlining primary constraints.

| Feature ID | Feature Name | Category | Description | Source | Dependencies | Constraints & Edge Cases |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FEAT-ENG-01** | Workflow Definition Schema & Parser | Workflow Engine | Parse YAML/JSON workflow files into validated internal data models (`WorkflowDef`, `StepDef`). | R1 (Explicit) | None | Must validate required keys (`id`, `action`); handle syntax & schema errors gracefully. |
| **FEAT-ENG-02** | DAG Builder & Cycle Detector | Workflow Engine | Build step dependency graph and run cycle detection algorithm (e.g. Kahn's/Tarjan's/DFS). | R1 (Explicit), R2 (Explicit) | FEAT-ENG-01 | Detect simple (`A->B->A`) and complex cyclic loops; return detailed cycle path. |
| **FEAT-ENG-03** | Topological Execution Planner | Workflow Engine | Compute topological order and manage dynamic step state ready-queues (`PENDING`, `READY`, `RUNNING`, etc.). | R1 (Explicit) | FEAT-ENG-02 | Prevent deadlocks; dynamically trigger downstream steps when all dependencies finish. |
| **FEAT-ENG-04** | Step Runner & Action Dispatcher | Workflow Engine | Execute individual step logic (Python callables, shell commands, synthetic actions) and capture results. | R1 (Explicit) | FEAT-ENG-01 | Capture stdout/stderr, return values, execution duration, and unhandled exceptions. |
| **FEAT-ENG-05** | Input/Output State Passing Engine | Execution State & Persistence | Interpolate downstream step inputs using outputs of completed upstream steps (e.g. `${step.output.key}`). | R1 (Explicit) | FEAT-ENG-03, FEAT-ENG-04 | Thread-safe state reading/writing; handle missing keys or null values without engine crash. |
| **FEAT-ENG-06** | Parallel Step Executor | Workflow Engine | Execute non-dependent workflow steps concurrently using `asyncio` or worker thread/process pools. | R1 (Explicit) | FEAT-ENG-03, FEAT-ENG-04, FEAT-ENG-05 | Thread safety for shared state; configurable maximum concurrency limit. |
| **FEAT-ENG-07** | Step Failure & Retry Manager | Workflow Engine | Retry failed steps up to configured `max_retries` with configurable delays before marking step FAILED. | R1 (Explicit) | FEAT-ENG-04 | Record attempt count, delay times, error messages, and tracebacks per attempt. |
| **FEAT-ENG-08** | Downstream Failure Propagation & Skipping | Workflow Engine | Automatically mark downstream steps `SKIPPED` when an upstream dependency fails terminally. | R1 (Implicit) | FEAT-ENG-03, FEAT-ENG-07 | Isolate independent branches so unaffected branches complete successfully. |
| **FEAT-STA-01** | Structured History Persistence Store | Execution State & Persistence | Persist run metadata (`run_id`, timestamps, final status, duration) to JSON files or SQLite store. | R1 (Explicit) | FEAT-ENG-03, FEAT-ENG-05 | Must survive process termination; atomic writes to avoid store corruption. |
| **FEAT-STA-02** | Granular Step Log Recorder | Execution State & Persistence | Record per-step attempt logs, input snapshots, output snapshots, status changes, and error tracebacks. | R1 (Explicit) | FEAT-STA-01, FEAT-ENG-07 | Support log retrieval by `run_id` and `step_id`; capture full stack traces. |
| **FEAT-CLI-01** | CLI Infrastructure & Entrypoint | CLI Interface | Command-line CLI entrypoint (`workflow-cli`) supporting modular subcommand dispatching. | R2 (Explicit) | None | POSIX compliant exit codes (0 for success, non-zero for error); standard `--help` docs. |
| **FEAT-CLI-02** | Workflow Validation Command (`validate`) | CLI Interface | Validate workflow syntax, schema, and check for cyclic dependencies prior to run without executing. | R2 (Explicit) | FEAT-ENG-01, FEAT-ENG-02, FEAT-CLI-01 | Return exit code 0 on valid, non-zero on invalid; print formatted syntax/cycle errors. |
| **FEAT-CLI-03** | Workflow Execution Command (`run`) | CLI Interface | Execute workflow file with live terminal progress output and display execution summary. | R2 (Explicit) | FEAT-ENG-03, FEAT-ENG-06, FEAT-CLI-01 | Real-time progress updates; support non-TTY environments; return exit code 0 on workflow success. |
| **FEAT-CLI-04** | Run Inspection Commands (`inspect`) | CLI Interface | CLI commands to list past runs, inspect run summaries, and view granular step execution outputs. | R2 (Explicit) | FEAT-STA-01, FEAT-STA-02, FEAT-CLI-01 | Support human-readable tabular output and machine-readable `--json` format. |
| **FEAT-VER-01** | Verification Scenario 1: Linear Workflow | Automated Verification | Automated test for sequential step execution and state forwarding across steps. | R3 (Explicit) | FEAT-ENG-03, FEAT-ENG-05 | Assert exact output state transformations and sequential execution timestamps. |
| **FEAT-VER-02** | Verification Scenario 2: Parallel DAG | Automated Verification | Automated test for concurrent branch execution and synchronization at a join step. | R3 (Explicit) | FEAT-ENG-06, FEAT-ENG-05 | Assert concurrent execution window and merged multi-branch state passing. |
| **FEAT-VER-03** | Verification Scenario 3: Failure & Retry | Automated Verification | Automated test for transient failure recovery and terminal failure downstream skipping. | R3 (Explicit) | FEAT-ENG-07, FEAT-ENG-08 | Assert retry attempt logging, successful recovery, and skipped downstream nodes. |
| **FEAT-VER-04** | Verification Scenario 4: State Mutation | Automated Verification | Automated test for complex list/dict data pipeline transformations across branches. | R3 (Explicit) | FEAT-ENG-05, FEAT-ENG-06 | Assert state integrity and thread safety under complex parallel mutations. |
| **FEAT-VER-05** | Automated Verification Runner (`verify.py`) | Automated Verification | Single executable test runner running all 4 scenarios and verifying programmatic correctness. | R3 (Explicit) | FEAT-VER-01, FEAT-VER-02, FEAT-VER-03, FEAT-VER-04 | Clean execution without manual input; returns exit code 0 on overall success. |

---

## 4. Dependencies & System Constraints

### 4.1 Feature Dependency Hierarchy

```
[ FEAT-ENG-01: Definition Parser ]
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[ FEAT-ENG-02: DAG & Cycle Detector ]   [ FEAT-ENG-04: Step Runner ]
       │                                 │
       ▼                                 ├────────────────────────┐
[ FEAT-ENG-03: Topological Planner ]    │                        │
       │                                 ▼                        ▼
       ├─────────────────────────► [ FEAT-ENG-05: State ]  [ FEAT-ENG-07: Retry ]
       │                                 │                        │
       ▼                                 ▼                        ▼
[ FEAT-ENG-06: Parallel Executor ] ───► [ FEAT-STA-01/02 ]   [ FEAT-ENG-08: Skipping ]
       │                                 │
       ├─────────────────────────────────┼────────────────────────┐
       ▼                                 ▼                        ▼
[ FEAT-CLI-02: validate ]        [ FEAT-CLI-03: run ]    [ FEAT-CLI-04: inspect ]
       │                                 │                        │
       └─────────────────────────────────┼────────────────────────┘
                                         ▼
                         [ FEAT-VER-01..05: Verification Suite ]
```

### 4.2 Core System Constraints & Design Principles

1. **Pure Python & Minimal Dependencies**: Framework implementation should rely on standard Python libraries (`asyncio`, `concurrent.futures`, `json`, `sqlite3`, `argparse`/`click`, `dataclasses`, `graphlib` / custom topological sort) to maintain high portability and lightweight benchmarking capabilities.
2. **Deterministic & Thread-Safe State Management**: Execution state passing during parallel execution must use explicit locks or immutable state snapshots to prevent race conditions during dictionary mutations.
3. **Structured Log Immutability**: Historical run records and step execution logs must be immutable once finalized to ensure reliable forensic inspection.
4. **POSIX CLI Compliance**: All CLI tools must conform to POSIX exit code conventions (0 for success, non-zero for validation/execution failures) to allow seamless integration into automated CI/CD pipelines and programmatic test benchmarks.

---

## 5. Verification & Traceability Matrix

| Requirement | Acceptance Criteria Target | Covered Features | Verification Approach |
| :--- | :--- | :--- | :--- |
| **R1 (DAG Resolution)** | Engine resolves & executes step dependency graphs | FEAT-ENG-01, FEAT-ENG-02, FEAT-ENG-03 | FEAT-VER-01, FEAT-VER-02 |
| **R1 (State Passing)** | Passes outputs from upstream steps to downstream inputs | FEAT-ENG-05 | FEAT-VER-01, FEAT-VER-04 |
| **R1 (Parallel Execution)** | Independent steps execute in parallel | FEAT-ENG-06 | FEAT-VER-02, FEAT-VER-04 |
| **R1 (Retry & Recovery)** | Configurable step retries on failure | FEAT-ENG-07, FEAT-ENG-08 | FEAT-VER-03 |
| **R1 (Persistence)** | Structured run history and step logs persisted | FEAT-STA-01, FEAT-STA-02 | FEAT-VER-01..04, FEAT-CLI-04 |
| **R2 (Validation)** | CLI `validate` command detects syntax & cycles | FEAT-CLI-01, FEAT-CLI-02 | Programmatic CLI exit code & error string check |
| **R2 (Live Run)** | CLI `run` command displays live progress | FEAT-CLI-01, FEAT-CLI-03 | CLI execution test against standard workflows |
| **R2 (Inspection)** | CLI `inspect` commands query history & step output | FEAT-CLI-01, FEAT-CLI-04 | CLI inspection test querying generated run IDs |
| **R3 (Automated Suite)** | 4 distinct scenarios (linear, parallel, retry, state) | FEAT-VER-01..04 | Programmatic assertion suite |
| **R3 (Verification Script)** | `verify.py` passes automatically with return code 0 | FEAT-VER-05 | System invocation of verification runner |

---
