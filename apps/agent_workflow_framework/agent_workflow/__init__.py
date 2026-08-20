"""Agent Workflow Framework package.

Exposes core models, parser functions, and DAG validation/batching utilities.
"""

from agent_workflow.models import (
    StepStatus,
    RunStatus,
    StepDefinition,
    WorkflowDefinition,
    StepResult,
    RunHistory,
)
from agent_workflow.parser import (
    WorkflowParseError,
    parse_workflow_dict,
    parse_workflow_yaml,
    parse_workflow_json,
    parse_workflow_file,
)
from agent_workflow.dag import (
    validate_workflow_dag,
    build_topological_batches,
)

from agent_workflow.state import (
    StateContext,
    StateInterpolationError,
)
from agent_workflow.persistence import (
    RunHistoryStore,
    HistoryStore,
    RunNotFoundError,
    RunCorruptedError,
)
from agent_workflow.executor import (
    WorkflowExecutor,
    ExecutionError,
)
from agent_workflow.cli import (
    cli_main,
    main,
)

__all__ = [
    # Models
    "StepStatus",
    "RunStatus",
    "StepDefinition",
    "WorkflowDefinition",
    "StepResult",
    "RunHistory",
    # Parser
    "WorkflowParseError",
    "parse_workflow_dict",
    "parse_workflow_yaml",
    "parse_workflow_json",
    "parse_workflow_file",
    # DAG
    "validate_workflow_dag",
    "build_topological_batches",
    # State & Persistence
    "StateContext",
    "StateInterpolationError",
    "RunHistoryStore",
    "HistoryStore",
    "RunNotFoundError",
    "RunCorruptedError",
    # Executor & CLI
    "WorkflowExecutor",
    "ExecutionError",
    "cli_main",
    "main",
]
