# Agent Workflow Framework Improvement and Evaluation Plan

## Scope and path correction

The requested `app/agent_workflow_flamwork` path does not exist in the selected repository. The matching project is `apps/agent_workflow_framework`; this plan targets that directory. No `SKILL.md` file exists there, so this is an application/framework review rather than a skill-authoring review.

## Baseline findings

The first run of `python verify.py` failed before test discovery with `ModuleNotFoundError: No module named 'yaml'`. The framework imports PyYAML at module import time, but the application directory had no local dependency manifest or setup instructions. CI already installs a hash-locked dependency set from `.github/apps-requirements.lock`, so the defect was local reproducibility and developer feedback, not a failing framework behavior.

After installing the pinned dependency set, the existing verification suite passed: 131 unit/integration tests, 5 adversarial tests, four workflow scenarios, and cyclic-validation checks.

## Implemented in this iteration

1. Add `requirements.txt` with the runtime dependency `PyYAML==6.0.3`.
2. Add a concise `README.md` with setup, CLI, and evaluation commands.
3. Keep the current CI lock as the supply-chain-controlled installation path and document the relationship between local setup and CI.

## Next improvements, ordered by value

### P1 — Packaging and import ergonomics

Add a `pyproject.toml` with an installable package and console entry point, then make the CLI usable from any working directory. Add a clean-environment smoke test that installs the package and runs `validate` without relying on the current directory or `PYTHONPATH`.

### P1 — Evaluation isolation

Make `verify.py` create or accept an isolated run-storage directory so test runs cannot depend on or pollute `.workflow_runs`. Add a `--storage-dir` option to the CLI and test parallel invocations with distinct stores.

### P2 — Observability and failure contracts (Complete)

Standardized structured status output and error codes across library and CLI layers:
- Added `DuplicateRunError` and duplicate run ID protection in `RunHistoryStore` and `WorkflowExecutor.execute_workflow(..., allow_duplicate_run_id=False)`.
- Added callback exception isolation in `WorkflowExecutor` with warning logging (`_invoke_callback`) so broken status callbacks do not crash or abort workflows.
- Added strict retry and retry_delay validation in `StepDefinition.from_dict` and `validate_workflow_dag`, rejecting negative values, booleans, and non-numeric types.
- Hardened `RunHistoryStore.load_run_history` against malformed persisted JSON files (empty files, whitespace, corrupted syntax, invalid enums, non-dict step results).
- Added `--json` structured output support for `inspect` and `list` CLI subcommands.
- Comprehensive unit and E2E test suites added in `test_persistence.py`, `test_executor.py`, `test_dag.py`, and `test_cli.py`.

### P2 — Execution resilience

Add cancellation and timeout semantics for long-running steps, plus tests for bounded shutdown and preservation of terminal step state. Document the concurrency contract for `max_workers`.

### P3 — Benchmark quality (Complete)

Added performance baselines for parallel fan-out and retry workloads, and published a machine-readable JSON evaluation summary from `verify.py` with `--json` and `--summary-file` options:
- Added `verify_benchmark_baselines()` testing 10-step parallel fan-out across 4 workers with throughput metrics (steps/s) and transient retry recovery timing.
- Added structured JSON summary generation with UTC timestamp, phase statuses, and benchmark metrics.
- Comprehensive unit test coverage added in `test_cli.py`.

## Acceptance gates

- `python -m pip install -r requirements.txt` succeeds in a clean Python 3.11 environment.
- `python -m unittest discover -s tests` passes.
- `python verify.py` passes with exit code 0.
- CLI validation returns 0 for valid workflows, 1 for runtime workflow failure, and 2 for parse/DAG validation failure.
- No test depends on pre-existing run history or an ambient working directory.
