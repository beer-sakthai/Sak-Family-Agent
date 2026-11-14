"""Data structures for multi-agent declarative pipelines and team orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineStep:
    """A single stage in a multi-agent team workflow."""

    name: str
    persona: str
    prompt_template: str
    with_skills: tuple[str, ...] = ()
    output_key: str = ""
    max_iterations: int = 8
    model: str | None = None
    provider: str | None = None
    parallel_group: str | None = None


@dataclass(frozen=True)
class PipelineDefinition:
    """Complete specification of a multi-agent team pipeline."""

    name: str
    description: str
    steps: tuple[PipelineStep, ...]
    version: str = "1.0"


@dataclass
class StepResult:
    """Execution result from an individual pipeline step."""

    step_name: str
    persona: str
    output: str
    iterations: int
    usage: dict[str, int]
    duration_seconds: float
    is_error: bool = False
    error_message: str | None = None


@dataclass
class PipelineResult:
    """Consolidated outcome of an end-to-end team workflow run."""

    pipeline_name: str
    task: str
    steps: list[StepResult] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    total_duration_seconds: float = 0.0
    total_tokens: int = 0
    success: bool = True
    summary: str = ""
