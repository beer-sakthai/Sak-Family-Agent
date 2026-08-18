# Project: Python Agent Workflow Framework

## Architecture
The framework is structured as a modular Python package `agent_workflow` with a CLI entry point, DAG dependency engine, state interpolation engine, async execution engine, persistent log store, and verification suite.

### Module Boundaries
- `agent_workflow/models.py`: Data structures (`WorkflowDefinition`, `StepDefinition`, `StepStatus`, `RunStatus`, `StepResult`, `RunHistory`).
- `agent_workflow/parser.py`: YAML/JSON parsing & schema validation.
- `agent_workflow/dag.py`: Graph construction, topological sorting (`graphlib.TopologicalSorter`), and cycle detection algorithms.
- `agent_workflow/state.py`: Thread-safe execution context and state expression resolution (`${steps.ID.output.KEY}`).
- `agent_workflow/executor.py`: Asynchronous execution engine with parallel task scheduling (`asyncio`), step retry loop with configurable attempts, and failure propagation / short-circuiting.
- `agent_workflow/persistence.py`: Run histories and step-level execution logs written as structured JSON files under `.workflow_runs/`.
- `agent_workflow/cli.py`: Typer / argparse CLI providing `validate`, `run`, and `inspect` subcommands with live progress rendering (`rich`).
- `verify.py`: Top-level automated test suite runner executing 4 comprehensive test scenario workflows and returning exit code 0.

## Feature Inventory
| # | Feature ID | Feature Name | Description | Milestone | Source |
|---|------------|--------------|-------------|-----------|--------|
| 1 | FEAT-ENG-01 | Workflow Definition Schema & Parsing | Parse YAML/JSON workflow definitions into Python dataclasses | M1 | R1 |
| 2 | FEAT-ENG-02 | DAG Dependency Graph & Sorting | Build DAG graph and perform topological sorting | M1 | R1 |
| 3 | FEAT-ENG-03 | Cyclic Dependency & Syntax Validation | Detect cyclic dependencies and syntax errors before execution | M1 | R1, R2 |
| 4 | FEAT-STA-01 | Input/Output State Passing & Interpolation | Pass state across steps using `${steps.ID.output.KEY}` syntax | M2 | R1 |
| 5 | FEAT-STA-02 | History Store & Log Persistence | Save structured run logs and step status to `.workflow_runs/` | M2 | R1 |
| 6 | FEAT-ENG-04 | Parallel Step Execution Engine | Execute independent workflow steps concurrently via `asyncio` | M3 | R1 |
| 7 | FEAT-ENG-05 | Step Retry & Resilience Handling | Retry failed steps up to configured max attempts before failing | M3 | R1 |
| 8 | FEAT-ENG-06 | Downstream Failure Short-Circuiting | Mark downstream dependent steps as SKIPPED when upstream fails | M3 | R1 |
| 9 | FEAT-CLI-01 | CLI `validate` Subcommand | Pre-flight validation of definition files with detailed error output | M4 | R2 |
| 10 | FEAT-CLI-02 | CLI `run` Subcommand | Execute workflow definition files with live progress output | M4 | R2 |
| 11 | FEAT-CLI-03 | CLI `inspect` Subcommand | Query past run history, step execution logs, and state outputs | M4 | R2 |
| 12 | FEAT-CLI-04 | CLI Exit Codes & Error Formatting | Standardized exit codes (0=success, 1=runtime err, 2=validation err) | M4 | R2 |
| 13 | FEAT-VER-01 | Scenario 1: Linear Workflow Test | Automated test verifying sequential execution and state passing | M5 | R3 |
| 14 | FEAT-VER-02 | Scenario 2: Parallel DAG Test | Automated test verifying concurrent fan-out/fan-in DAG execution | M5 | R3 |
| 15 | FEAT-VER-03 | Scenario 3: Failure & Retry Test | Automated test verifying transient retry recovery & terminal failure | M5 | R3 |
| 16 | FEAT-VER-04 | Scenario 4: State Mutation Test | Automated test verifying complex state mutation pipeline | M5 | R3 |
| 17 | FEAT-VER-05 | Automated Verification Script (`verify.py`) | Master test runner executing all scenarios and returning exit code 0 | M5 | R3 |
| 18 | FEAT-HARD-01 | Adversarial Edge Case Hardening | White-box edge case verification & branch coverage hardening | M6 | Quality |
| 19 | FEAT-AUD-01 | Forensic Integrity Audit | Static analysis and runtime verification of authentic implementation | M6 | Quality |

## Code Layout
```
agent_workflow_framework/
├── agent_workflow/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── dag.py
│   ├── state.py
│   ├── executor.py
│   ├── persistence.py
│   └── cli.py
├── tests/
│   ├── __init__.py
│   ├── test_dag.py
│   ├── test_state.py
│   ├── test_executor.py
│   ├── test_cli.py
│   └── test_workflows/
│       ├── linear_workflow.yaml
│       ├── parallel_workflow.yaml
│       ├── retry_workflow.yaml
│       └── mutation_workflow.yaml
├── verify.py
├── pyproject.toml
└── README.md
```

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Workflow Engine Core & DAG Resolution | Definition parsing, models, graph construction, cycle detection | None | DONE |
| M2 | State Passing & Execution Persistence | State context interpolation, run history & log persistence | M1 | DONE |
| M3 | Parallel Execution Engine & Retry System | Async parallel execution, step retries with backoff, short-circuiting | M1, M2 | DONE |
| M4 | CLI Interface & Inspection Tools | Subcommands `validate`, `run` (live progress), `inspect`, exit codes | M1, M2, M3 | DONE |
| M5 | E2E Test Suite & Verification Script Pass | Final integration of tests and `verify.py` runner (Tiers 1-4) | M1, M2, M3, M4 | DONE |
| M6 | Adversarial Hardening & Forensic Audit | White-box Tier 5 adversarial testing & Forensic Integrity Audit | M5 | DONE |

## Interface Contracts

### `agent_workflow.models`
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class StepDefinition:
    id: str
    action: str  # e.g., "echo", "python", "shell"
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    retry: int = 0
    retry_delay: float = 0.0

@dataclass
class WorkflowDefinition:
    name: str
    description: Optional[str] = None
    steps: List[StepDefinition] = field(default_factory=list)

@dataclass
class StepResult:
    step_id: str
    status: StepStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    attempts: int = 1
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@dataclass
class RunHistory:
    run_id: str
    workflow_name: str
    status: RunStatus
    start_time: str
    end_time: Optional[str] = None
    step_results: Dict[str, StepResult] = field(default_factory=dict)
```

### `agent_workflow.dag`
```python
def validate_workflow_dag(workflow: WorkflowDefinition) -> List[str]:
    """Validates workflow step dependencies. Returns a list of validation error strings.
    Empty list indicates valid DAG."""
    ...

def build_topological_batches(workflow: WorkflowDefinition) -> List[List[StepDefinition]]:
    """Returns steps grouped into parallel execution batches in topological order."""
    ...
```

### `agent_workflow.state`
```python
class StateContext:
    def set_step_output(self, step_id: str, output: Dict[str, Any]) -> None: ...
    def get_step_output(self, step_id: str) -> Dict[str, Any]: ...
    def interpolate(self, template: Any) -> Any: ...
    """Interpolates strings like '${steps.step_id.output.key}' using recorded step outputs."""
```

### `agent_workflow.executor`
```python
class WorkflowExecutor:
    async def execute_workflow(self, workflow: WorkflowDefinition, run_id: Optional[str] = None, status_callback: Optional[Any] = None) -> RunHistory:
        ...
```
