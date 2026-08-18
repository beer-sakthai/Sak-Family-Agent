"""Agent Workflow Framework package.

Exposes core models, parser functions, and DAG validation/batching utilities.
"""

from agent_workflow.cli import (
    cli_main,
    main,
)
from agent_workflow.dag import (
    build_topological_batches,
    validate_workflow_dag,
)
from agent_workflow.executor import (
    ExecutionError,
    WorkflowExecutor,
)
from agent_workflow.models import (
    RunHistory,
    RunStatus,
    StepDefinition,
    StepResult,
    StepStatus,
    WorkflowDefinition,
)
from agent_workflow.parser import (
    WorkflowParseError,
    parse_workflow_dict,
    parse_workflow_file,
    parse_workflow_json,
    parse_workflow_yaml,
)
from agent_workflow.persistence import (
    HistoryStore,
    RunCorruptedError,
    RunHistoryStore,
    RunNotFoundError,
)
from agent_workflow.state import (
    StateContext,
    StateInterpolationError,
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
