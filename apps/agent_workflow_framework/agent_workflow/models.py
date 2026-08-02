"""Data models for the agent workflow framework.

Defines core enums and dataclasses for step status, run status,
step definitions, workflow definitions, step results, and run history.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class StepStatus(str, Enum):
    """Execution status of an individual workflow step."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

    def is_terminal(self) -> bool:
        """Return True if step status is terminal (COMPLETED, FAILED, or SKIPPED)."""
        return self in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)

    def is_successful(self) -> bool:
        """Return True if step completed successfully."""
        return self == StepStatus.COMPLETED


class RunStatus(str, Enum):
    """Overall status of a workflow run."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def is_terminal(self) -> bool:
        """Return True if run status is terminal (COMPLETED or FAILED)."""
        return self in (RunStatus.COMPLETED, RunStatus.FAILED)


@dataclass
class StepDefinition:
    """Dataclass representing a single workflow step definition."""

    id: str
    action: str = "echo"
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    retry: int = 0
    retry_delay: float = 0.0

    def validate_schema(self) -> List[str]:
        """Validate step definition fields. Returns list of error messages."""
        errors: List[str] = []
        if not self.id or not isinstance(self.id, str):
            errors.append("Step ID must be a non-empty string.")
        if not self.action or not isinstance(self.action, str):
            errors.append(f"Step '{self.id}' action must be a non-empty string.")
        if not isinstance(self.params, dict):
            errors.append(f"Step '{self.id}' params must be a dictionary.")
        if not isinstance(self.depends_on, list):
            errors.append(f"Step '{self.id}' depends_on must be a list of step IDs.")
        if not isinstance(self.retry, int) or isinstance(self.retry, bool) or self.retry < 0:
            errors.append(f"Step '{self.id}' retry count must be a non-negative integer.")
        if not isinstance(self.retry_delay, (int, float)) or isinstance(self.retry_delay, bool) or self.retry_delay < 0:
            errors.append(f"Step '{self.id}' retry_delay must be a non-negative number.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert step definition to a dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "params": self.params,
            "depends_on": list(self.depends_on),
            "retry": self.retry,
            "retry_delay": self.retry_delay,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StepDefinition":
        """Construct StepDefinition from dictionary."""
        return cls(
            id=d["id"],
            action=d["action"],
            params=d.get("params", {}),
            depends_on=list(d.get("depends_on", [])),
            retry=int(d.get("retry", 0)),
            retry_delay=float(d.get("retry_delay", 0.0)),
        )


@dataclass
class WorkflowDefinition:
    """Definition of a multi-step workflow."""
    name: str
    description: Optional[str] = None
    steps: List[StepDefinition] = field(default_factory=list)

    def get_step(self, step_id: str) -> Optional[StepDefinition]:
        """Look up a step by its ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    @property
    def step_ids(self) -> List[str]:
        """Return list of all step IDs in the workflow."""
        return [step.id for step in self.steps]

    def validate_schema(self) -> List[str]:
        """Validate workflow definition basic schema. Returns list of error messages."""
        errors: List[str] = []
        if not self.name or not isinstance(self.name, str):
            errors.append("Workflow name must be a non-empty string.")
        if not isinstance(self.steps, list) or len(self.steps) == 0:
            errors.append("Workflow must contain at least one step.")

        seen_ids = set()
        for idx, step in enumerate(self.steps):
            if not isinstance(step, StepDefinition):
                errors.append(f"Element at index {idx} in steps is not a StepDefinition.")
                continue
            step_errors = step.validate_schema()
            errors.extend(step_errors)
            if step.id in seen_ids:
                errors.append(f"Duplicate step ID '{step.id}' found in workflow.")
            seen_ids.add(step.id)

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow definition to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WorkflowDefinition":
        """Construct WorkflowDefinition from dictionary."""
        raw_steps = d.get("steps", [])
        steps = [
            StepDefinition.from_dict(s) if isinstance(s, dict) else s
            for s in raw_steps
        ]
        return cls(
            name=d["name"],
            description=d.get("description"),
            steps=steps,
        )


@dataclass
class StepResult:
    """Execution result of an individual step."""
    step_id: str
    status: StepStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    attempts: int = 1
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step execution duration in seconds if start and end timestamps exist."""
        if not self.start_time or not self.end_time:
            return None
        try:
            start = datetime.datetime.fromisoformat(self.start_time)
            end = datetime.datetime.fromisoformat(self.end_time)
            return max(0.0, (end - start).total_seconds())
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert StepResult to dictionary suitable for JSON serialization."""
        return {
            "step_id": self.step_id,
            "status": self.status.value if isinstance(self.status, StepStatus) else str(self.status),
            "output": self.output,
            "error": self.error,
            "attempts": self.attempts,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StepResult":
        """Construct StepResult from dictionary."""
        status_val = d["status"]
        status = StepStatus(status_val) if isinstance(status_val, str) else status_val
        return cls(
            step_id=d["step_id"],
            status=status,
            output=d.get("output", {}),
            error=d.get("error"),
            attempts=int(d.get("attempts", 1)),
            start_time=d.get("start_time"),
            end_time=d.get("end_time"),
        )


@dataclass
class RunHistory:
    """Complete history of a workflow execution run."""
    run_id: str
    workflow_name: str
    status: RunStatus
    start_time: str
    end_time: Optional[str] = None
    step_results: Dict[str, StepResult] = field(default_factory=dict)

    def add_step_result(self, result: StepResult) -> None:
        """Record or update a step result."""
        self.step_results[result.step_id] = result

    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """Retrieve step result by step ID."""
        return self.step_results.get(step_id)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total workflow run duration in seconds if start and end timestamps exist."""
        if not self.start_time or not self.end_time:
            return None
        try:
            start = datetime.datetime.fromisoformat(self.start_time)
            end = datetime.datetime.fromisoformat(self.end_time)
            return max(0.0, (end - start).total_seconds())
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert RunHistory to dictionary suitable for JSON serialization."""
        return {
            "run_id": self.run_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value if isinstance(self.status, RunStatus) else str(self.status),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "step_results": {
                k: v.to_dict() if hasattr(v, "to_dict") else v
                for k, v in self.step_results.items()
            },
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RunHistory":
        """Construct RunHistory from dictionary."""
        status_val = d["status"]
        status = RunStatus(status_val) if isinstance(status_val, str) else status_val
        raw_results = d.get("step_results", {})
        step_results = {
            k: StepResult.from_dict(v) if isinstance(v, dict) else v
            for k, v in raw_results.items()
        }
        return cls(
            run_id=d["run_id"],
            workflow_name=d["workflow_name"],
            status=status,
            start_time=d["start_time"],
            end_time=d.get("end_time"),
            step_results=step_results,
        )
