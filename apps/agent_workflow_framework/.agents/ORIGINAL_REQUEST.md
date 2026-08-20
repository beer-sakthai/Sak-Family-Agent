# Original User Request

## Initial Request — 2026-08-01T17:22:12Z

Build a Python-based agent workflow framework and CLI tool designed to define, execute, and monitor multi-step agent workflows with step dependency management, state passing, parallel execution, and error handling. Built as an evaluation benchmark for multi-agent system capabilities.

Working directory: ~/teamwork_projects/agent_workflow_framework
Integrity mode: development

## Requirements

### R1. Workflow Engine & Execution State
Build a Python engine capable of loading workflow definitions, resolving step dependency graphs (DAGs), executing steps with input/output state passing, supporting parallel step execution when dependencies allow, and handling retries/failures gracefully.

### R2. CLI Interface & Inspection Tools
Provide a command-line interface to validate workflow definitions (including detecting circular dependencies), execute workflows with real-time status output, and inspect past execution logs and step state.

### R3. Automated Verification Suite
Provide an automated test suite and verification script that executes a comprehensive set of test workflows (linear, parallel DAG, retry-on-failure, state passing) and programmatically verifies execution correctness and exit codes.

## Acceptance Criteria

### Core Workflow Engine
- [ ] Workflow engine resolves and executes step dependency graphs (DAGs).
- [ ] Supports passing outputs from upstream steps as inputs to downstream steps.
- [ ] Executes independent workflow steps in parallel when dependencies permit.
- [ ] Supports configurable retry attempts for failed steps before declaring step or workflow failure.
- [ ] Persists structured run histories and step-level execution logs.

### CLI Usability & Tools
- [ ] CLI provides a `validate` command that catches syntax errors and cyclic dependency errors prior to run.
- [ ] CLI provides a `run` command that executes a workflow definition file and displays live step execution progress.
- [ ] CLI provides inspection commands to query past run status and step outputs.

### Automated Verification
- [ ] Verification suite covers at least 4 distinct workflow scenarios (linear, parallel DAG, failure & retry, state mutation).
- [ ] Running the test/verification script executes automatically and passes with return code 0.
