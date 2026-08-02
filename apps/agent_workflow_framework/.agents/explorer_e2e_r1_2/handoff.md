# E2E Test Suite Round 1 Investigation Report

## 1. Observation

### 1.1 Direct File Observations
- **`ORIGINAL_REQUEST.md`** (Lines 12–38):
  - **R1. Workflow Engine & Execution State**: DAG resolution, input/output state passing, parallel step execution, retry handling, structured history logging.
  - **R2. CLI Interface & Inspection Tools**: `validate` command (detecting circular dependencies and syntax errors), `run` command (real-time status output), `inspect` command (past execution logs and step state).
  - **R3. Automated Verification Suite**: Automated test suite & verification script executing linear, parallel DAG, failure/retry, state mutation test workflows, returning exit code 0.
- **`TEST_INFRA.md`** (Lines 4–37):
  - Philosophy: Opaque-box, requirement-driven. Category-Partition + BVA + Pairwise Combinatorial + Real-World Workload Testing.
  - Feature Inventory: 7 feature areas (Schema & Parsing, DAG & Cycle Detection, State Passing & Interpolation, History Persistence & Log Store, Parallel Step Execution Engine, Step Retries & Downstream Short-Circuiting, CLI Commands).
  - Test Tiers:
    - Tier 1: Feature Coverage (≥5 tests per feature area, 35+ total).
    - Tier 2: Boundary & Corner Cases (≥5 tests: cycles, invalid keys, retry exhaustion, empty graphs).
    - Tier 3: Pairwise Combinations (parallel execution + retries, parallel + state passing, state passing + failure short-circuiting).
    - Tier 4: Real-World Workload Scenarios (Scenario 1 Linear, Scenario 2 Parallel DAG, Scenario 3 Failure & Retry, Scenario 4 State Mutation).
    - Scenario 5: Master Verification Benchmark Suite (`verify.py`).
- **`PROJECT.md`** (Lines 79–160):
  - Interface contracts defined for dataclasses and core modules:
    - `StepDefinition`: `id: str`, `action: str`, `params: Dict[str, Any]`, `depends_on: List[str]`, `retry: int = 0`, `retry_delay: float = 0.0`.
    - `WorkflowDefinition`: `name: str`, `description: Optional[str]`, `steps: List[StepDefinition]`.
    - `StepStatus`: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`.
    - `RunStatus`: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`.
    - `StepResult`: `step_id: str`, `status: StepStatus`, `output: Dict[str, Any]`, `error: Optional[str]`, `attempts: int`, `start_time: Optional[str]`, `end_time: Optional[str]`.
    - `RunHistory`: `run_id: str`, `workflow_name: str`, `status: RunStatus`, `start_time: str`, `end_time: Optional[str]`, `step_results: Dict[str, StepResult]`.
    - `agent_workflow.dag`: `validate_workflow_dag(workflow: WorkflowDefinition) -> List[str]`, `build_topological_batches(workflow: WorkflowDefinition) -> List[List[StepDefinition]]`.
    - `agent_workflow.state`: `StateContext` with `set_step_output`, `get_step_output`, `interpolate`.
    - `agent_workflow.executor`: `WorkflowExecutor.execute_workflow(workflow, run_id, status_callback) -> RunHistory`.
- **Environment**:
  - Python 3.14.4, PyYAML 6.0.3, typer 0.19.2, rich 13.9.4, standard library `unittest`, `asyncio`, `graphlib`.

---

## 2. Logic Chain

1. **Opaque-Box Testing Requirement**:
   - *Observation*: `TEST_INFRA.md` specifies "Opaque-box, requirement-driven. No dependency on implementation design details."
   - *Deduction*: Tests must interact strictly with public module contracts (`agent_workflow.models`, `agent_workflow.parser`, `agent_workflow.dag`, `agent_workflow.state`, `agent_workflow.executor`, `agent_workflow.persistence`, `agent_workflow.cli`) and external interfaces (YAML files, CLI arguments, return exit codes `0`, `1`, `2`, and persistent JSON logs in `.workflow_runs/`).

2. **Fixture YAML Specification**:
   - *Observation*: `SCOPE.md` lists 4 target YAML fixture files in `tests/test_workflows/`.
   - *Deduction*:
     - `linear_workflow.yaml`: 3-step sequential DAG testing linear state passing (`step_start` -> `step_transform` -> `step_finish`).
     - `parallel_workflow.yaml`: Fan-out/fan-in DAG (`root` -> `branch_a` & `branch_b` in parallel -> `join`).
     - `retry_workflow.yaml`: Test transient retry recovery (`flaky_step` retries and succeeds) and terminal failure short-circuiting (`failing_step` exhausts retries, `skipped_downstream` marked `SKIPPED`).
     - `mutation_workflow.yaml`: Multi-step state transformation and data mutation pipeline (`init_data` -> `append_item` -> `compute_summary`).

3. **Assertion Mechanics across Tiers 1-4**:
   - *Observation*: `TEST_INFRA.md` defines coverage thresholds across Tiers 1-4.
   - *Deduction*:
     - Tier 1 asserts basic functional behaviors per feature area (≥5 tests each for parsing, DAG sorting, state interpolation, history logging, parallel execution, retries, CLI).
     - Tier 2 asserts boundary cases (cycle paths, missing expression keys, retry exhaustion, empty/malformed workflows, worker limit bounds).
     - Tier 3 asserts pairwise interactions (parallel + retry, parallel + state passing, state passing + failure short-circuiting).
     - Tier 4 asserts end-to-end workload properties (status enum values, step execution order, output value assertions, timestamp ordering).

4. **CLI Validation & Master Script (`verify.py`)**:
   - *Observation*: `ORIGINAL_REQUEST.md` R3 and `TEST_INFRA.md` Scenario 5 mandate a master verification script `verify.py` returning exit code 0.
   - *Deduction*: `verify.py` must execute both unit/integration tests and CLI invocations (`validate`, `run`, `inspect`), assert process exit codes (0 for success, 1 for execution error, 2 for validation error), and check log store artifacts in `.workflow_runs/`.

---

## 3. Caveats

- **Source Code Pendency**: Source code files in `agent_workflow/` are currently being developed under Milestones M1–M4. Test specifications and fixtures designed here rely strictly on the `PROJECT.md` interface contracts.
- **Handler Naming Alignment**: `PROJECT.md` defines step fields as `action` and `params` (whereas early spec notes used `handler` and `inputs`). All fixture YAMLs and tests must adhere to `action` and `params` per `PROJECT.md` `StepDefinition`.
- **Async Execution Context**: In Python 3.14, `asyncio` event loop management in `unittest` requires `asyncio.run()` or standard `IsolatedAsyncioTestCase`.

---

## 4. Conclusion & Recommendations

### 4.1 Opaque-Box Requirement-Driven Testing Framework

The E2E test suite must test the system solely through public APIs and CLI entrypoints.

#### Public API Contracts:
- `agent_workflow.parser.parse_workflow_file(filepath: str) -> WorkflowDefinition`
- `agent_workflow.dag.validate_workflow_dag(workflow: WorkflowDefinition) -> List[str]`
- `agent_workflow.dag.build_topological_batches(workflow: WorkflowDefinition) -> List[List[StepDefinition]]`
- `agent_workflow.state.StateContext` (`set_step_output`, `get_step_output`, `interpolate`)
- `agent_workflow.executor.WorkflowExecutor.execute_workflow(workflow: WorkflowDefinition, ...) -> RunHistory`
- `agent_workflow.persistence.load_run_history(run_id_or_path: str) -> RunHistory`
- `agent_workflow.cli` (`validate`, `run`, `inspect`)

#### Exit Code Contract:
- `0`: Success (all steps completed / valid workflow / inspection succeeded).
- `1`: Execution error (workflow step failure / missing run log).
- `2`: Validation error (static syntax error, DAG cycle, undefined step dependency).

---

### 4.2 Fixture YAML Definitions (`tests/test_workflows/`)

#### 1. `linear_workflow.yaml`
```yaml
name: linear_workflow
description: Sequential 3-step linear DAG testing sequential state passing
steps:
  - id: step_start
    action: echo
    params:
      message: "Hello World"
      value: 10
  - id: step_transform
    action: python
    depends_on:
      - step_start
    params:
      input_value: "${steps.step_start.output.value}"
      multiplier: 5
  - id: step_finish
    action: echo
    depends_on:
      - step_transform
    params:
      final_result: "${steps.step_transform.output.result}"
```

#### 2. `parallel_workflow.yaml`
```yaml
name: parallel_workflow
description: Fan-out from root to parallel branches A and B, fan-in to join step
steps:
  - id: root
    action: echo
    params:
      base_data: "source_data"
  - id: branch_a
    action: echo
    depends_on:
      - root
    params:
      source: "${steps.root.output.base_data}"
      tag: "branch_a_processed"
  - id: branch_b
    action: echo
    depends_on:
      - root
    params:
      source: "${steps.root.output.base_data}"
      tag: "branch_b_processed"
  - id: join
    action: echo
    depends_on:
      - branch_a
      - branch_b
    params:
      from_a: "${steps.branch_a.output.tag}"
      from_b: "${steps.branch_b.output.tag}"
```

#### 3. `retry_workflow.yaml`
```yaml
name: retry_workflow
description: Tests transient failure recovery via retry and terminal failure short-circuiting
steps:
  - id: flaky_step
    action: python
    retry: 2
    retry_delay: 0.1
    params:
      fail_count: 1
      output_val: "recovered_data"
  - id: dependent_on_flaky
    action: echo
    depends_on:
      - flaky_step
    params:
      input: "${steps.flaky_step.output.output_val}"
  - id: failing_step
    action: python
    retry: 1
    retry_delay: 0.1
    params:
      always_fail: true
  - id: skipped_downstream
    action: echo
    depends_on:
      - failing_step
    params:
      msg: "Should never execute"
```

#### 4. `mutation_workflow.yaml`
```yaml
name: mutation_workflow
description: Multi-step pipeline mutating strings, lists, and dict state across steps
steps:
  - id: init_data
    action: echo
    params:
      items: ["alpha", "beta", "gamma"]
      count: 3
  - id: append_item
    action: python
    depends_on:
      - init_data
    params:
      initial_items: "${steps.init_data.output.items}"
      new_item: "delta"
  - id: compute_summary
    action: python
    depends_on:
      - append_item
    params:
      item_list: "${steps.append_item.output.updated_items}"
      item_count: "${steps.append_item.output.count}"
```

---

### 4.3 `tests/test_e2e_suite.py` Assertion Mechanics (Tiers 1–4)

#### Tier 1: Feature Coverage (35+ Tests across 7 Areas)
- **Feature Area 1 (Parsing & Schema)**:
  - `test_parse_valid_yaml`: Asserts `WorkflowDefinition` object returned with expected `name` and step count.
  - `test_parse_valid_json`: Asserts JSON parsing parity with YAML.
  - `test_missing_required_name`: Asserts validation error raised when `name` is missing.
  - `test_missing_required_steps`: Asserts validation error raised when `steps` key is missing or empty.
  - `test_step_default_values`: Asserts `retry=0`, `retry_delay=0.0`, `depends_on=[]` defaulted properly.
- **Feature Area 2 (DAG Resolution & Sorting)**:
  - `test_topological_batching_linear`: Asserts 3-step linear DAG produces 3 sequential batches `[[step1], [step2], [step3]]`.
  - `test_topological_batching_parallel`: Asserts fan-out DAG produces `[[root], [branch_a, branch_b], [join]]`.
  - `test_single_node_dag`: Asserts 1-step DAG produces `[[node]]`.
  - `test_disconnected_dag`: Asserts disconnected components batched cleanly in parallel.
  - `test_validate_dag_valid`: Asserts `validate_workflow_dag` returns empty error list `[]`.
- **Feature Area 3 (State Passing & Interpolation)**:
  - `test_interpolate_simple_string`: Asserts `${steps.step1.output.key}` expands to stored string.
  - `test_interpolate_type_preservation`: Asserts single expression `${steps.step1.output.dict_val}` retains Python dict type.
  - `test_interpolate_multiple_vars`: Asserts string containing multiple expressions interpolates both.
  - `test_interpolate_nested_keys`: Asserts `${steps.step1.output.data.nested}` resolves nested dict.
  - `test_state_context_thread_safety`: Asserts concurrent reads/writes do not cause race conditions.
- **Feature Area 4 (History Store & Log Persistence)**:
  - `test_execution_generates_log_file`: Asserts `.workflow_runs/<run_id>.json` exists after run.
  - `test_log_file_schema_validity`: Asserts JSON file contains `run_id`, `workflow_name`, `status`, `start_time`, `end_time`, `step_results`.
  - `test_step_result_serialization`: Asserts step status enum, attempts count, output, and error string properly formatted.
  - `test_load_run_history`: Asserts `load_run_history(run_id)` reconstructs accurate `RunHistory` object.
  - `test_auto_create_log_directory`: Asserts `.workflow_runs` directory created if missing.
- **Feature Area 5 (Parallel Step Execution)**:
  - `test_parallel_step_concurrency`: Asserts `branch_a` and `branch_b` execute concurrently (wall-clock time < sum of delays).
  - `test_max_workers_throttling`: Asserts setting `max_workers=1` forces sequential execution without error.
  - `test_fan_in_barrier`: Asserts `join` step waits until both `branch_a` and `branch_b` achieve `StepStatus.COMPLETED`.
  - `test_async_callback_triggering`: Asserts status callbacks receive `PENDING` -> `RUNNING` -> `COMPLETED` events.
  - `test_independent_branch_isolation`: Asserts failure in one branch does not cancel unrelated running parallel branches.
- **Feature Area 6 (Step Retries & Short-Circuiting)**:
  - `test_retry_transient_recovery`: Asserts step failing on attempt 1 succeeds on attempt 2, ending in `StepStatus.COMPLETED` with `attempts=2`.
  - `test_retry_exhaustion`: Asserts step failing all attempts ends in `StepStatus.FAILED` with `attempts=max_retries+1`.
  - `test_downstream_short_circuit`: Asserts downstream steps dependent on a `FAILED` step are set to `StepStatus.SKIPPED`.
  - `test_unaffected_branch_completes`: Asserts steps independent of failed step reach `StepStatus.COMPLETED`.
  - `test_retry_delay_backoff`: Asserts time delay between retries respects `retry_delay`.
- **Feature Area 7 (CLI Interface)**:
  - `test_cli_validate_success`: Asserts `validate` returns exit code 0 for valid workflow file.
  - `test_cli_validate_cycle_failure`: Asserts `validate` returns exit code 2 for cyclic workflow file.
  - `test_cli_run_success`: Asserts `run` returns exit code 0 and logs run history.
  - `test_cli_run_failure`: Asserts `run` returns exit code 1 when workflow steps fail.
  - `test_cli_inspect_run_id`: Asserts `inspect` outputs JSON/table summary and returns exit code 0.

#### Tier 2: Boundary & Corner Cases (≥5 Tests)
- `test_cycle_detection_self_loop`: Asserts cycle error reported for `A -> A` (exit code 2).
- `test_cycle_detection_indirect_loop`: Asserts cycle path reported for `A -> B -> C -> A` (exit code 2).
- `test_invalid_interpolation_missing_step`: Asserts `StateResolutionError` or failed step result when referencing non-existent step.
- `test_invalid_interpolation_missing_key`: Asserts graceful handling of missing dict keys in expression.
- `test_empty_workflow_steps`: Asserts validation error for workflow with `steps: []` (exit code 2).
- `test_undefined_dependency_reference`: Asserts validation error for `depends_on: ["non_existent_step"]` (exit code 2).
- `test_duplicate_step_ids`: Asserts validation error when two steps share the same `id`.

#### Tier 3: Pairwise Combinations
- `test_pairwise_parallel_and_retries`: Branch A retries & succeeds, Branch B succeeds immediately; verifies fan-in join step executes correctly.
- `test_pairwise_parallel_and_state_passing`: Fan-in join step interpolates state from both Branch A and Branch B simultaneously.
- `test_pairwise_state_passing_and_short_circuit`: Upstream step fails after retry exhaustion; downstream interpolation step is marked `SKIPPED` without throwing unhandled state resolution exception.

#### Tier 4: Real-World Workload Scenarios
- `test_scenario_1_linear_pipeline`: Executes `linear_workflow.yaml`, asserts `RunStatus.COMPLETED`, all steps `COMPLETED`, monotonic timestamp progression, correct interpolated result in `step_finish`.
- `test_scenario_2_parallel_dag`: Executes `parallel_workflow.yaml`, asserts concurrent timing for `branch_a` & `branch_b`, verifies `join` receives inputs from both.
- `test_scenario_3_retry_and_short_circuit`: Executes `retry_workflow.yaml`, asserts `flaky_step` completed on attempt 2, `failing_step` failed on attempt 2, `skipped_downstream` skipped, overall run status `RunStatus.FAILED`.
- `test_scenario_4_data_mutation`: Executes `mutation_workflow.yaml`, verifies multi-step item accumulation (`["alpha", "beta", "gamma", "delta"]`) and count summary (`4`).

---

### 4.4 CLI Validation and `verify.py` Master Verification Runner

`verify.py` acts as the master verification benchmark script (Scenario 5 / Requirement R3).

#### Structure of `verify.py`:
1. **Runner Initialization**:
   - Configures test suite using `unittest.TestSuite()` or `unittest.TestLoader()`.
   - Prepares temporary execution environment and `.workflow_runs/` clean workspace.
2. **Phase 1: Programmatic E2E Suite Execution**:
   - Runs `tests/test_e2e_suite.py` covering Tiers 1–4.
   - Captures pass/fail test counts.
3. **Phase 2: CLI Subcommand Validation**:
   - Uses `subprocess.run([sys.executable, "-m", "agent_workflow.cli", ...], capture_output=True, text=True)` or Typer test runner to test CLI commands against fixture files:
     - `validate tests/test_workflows/linear_workflow.yaml` -> Exit code **0**.
     - `validate tests/test_workflows/cyclic_workflow.yaml` (generated on-the-fly or fixture) -> Exit code **2**.
     - `run tests/test_workflows/linear_workflow.yaml` -> Exit code **0**.
     - `run tests/test_workflows/retry_workflow.yaml` -> Exit code **1**.
     - `inspect <run_id>` -> Exit code **0**, outputs valid JSON/table summary.
     - `inspect non_existent_run_id` -> Exit code **1**.
4. **Phase 3: Log Persistence Store Verification**:
   - Inspects generated `.workflow_runs/<run_id>.json` files for schema compliance.
5. **Phase 4: Benchmark Summary & Exit Code**:
   - Prints ANSI / formatted summary matrix of test results.
   - Exits with `sys.exit(0)` if all test suites and CLI checks pass; `sys.exit(1)` if any test fails.

---

## 5. Verification Method

To verify these findings once implementation and tests are written:
1. Execute unit & integration test suite:
   ```bash
   python -m unittest discover -s tests
   ```
2. Execute master verification script:
   ```bash
   python verify.py
   ```
3. Check exit code:
   ```bash
   echo $?
   # Expected output: 0
   ```
4. Verify log persistence files:
   ```bash
   ls -la .workflow_runs/
   ```
5. Invalidation conditions:
   - Any test suite failure.
   - Non-zero exit code from `python verify.py`.
   - Failure to catch cycles statically during `validate` (returning code other than 2).
   - Unhandled exceptions during state interpolation when steps are skipped.
