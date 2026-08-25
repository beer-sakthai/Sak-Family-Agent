"""Execution engine for declarative multi-agent pipelines."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..agent.coordinator import run_persona_task
from ..memory.store import MemoryStore
from .builtin_pipelines import BUILTIN_PIPELINES
from .models import PipelineDefinition, PipelineResult, PipelineStep, StepResult

logger = logging.getLogger(__name__)


def list_builtin_pipelines() -> dict[str, PipelineDefinition]:
    """Return map of all registered built-in pipelines."""
    return dict(BUILTIN_PIPELINES)


def load_pipeline_from_dict(data: dict[str, Any]) -> PipelineDefinition:
    """Parse a dictionary into a PipelineDefinition."""
    name = str(data.get("name", "custom-pipeline"))
    description = str(data.get("description", ""))
    version = str(data.get("version", "1.0"))

    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("Pipeline must contain at least one step in 'steps'.")

    steps: list[PipelineStep] = []
    for step_data in raw_steps:
        if not isinstance(step_data, dict):
            continue
        step = PipelineStep(
            name=str(step_data.get("name", "step")),
            persona=str(step_data.get("persona", "sakthai")),
            prompt_template=str(step_data.get("prompt_template", "{task}")),
            with_skills=tuple(step_data.get("with_skills", ())),
            output_key=str(step_data.get("output_key", "")),
            max_iterations=int(step_data.get("max_iterations", 8)),
            model=step_data.get("model"),
            provider=step_data.get("provider"),
        )
        steps.append(step)

    return PipelineDefinition(
        name=name, description=description, steps=tuple(steps), version=version
    )


def load_pipeline_from_file(path: Path | str) -> PipelineDefinition:
    """Load and parse a pipeline from a YAML or JSON file."""
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Pipeline file not found: {p}")

    text = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level object in {p}")
    return load_pipeline_from_dict(data)


def get_pipeline(name_or_path: str) -> PipelineDefinition:
    """Retrieve a built-in pipeline by name or load from a file path."""
    if name_or_path in BUILTIN_PIPELINES:
        return BUILTIN_PIPELINES[name_or_path]

    p = Path(name_or_path)
    if p.is_file():
        return load_pipeline_from_file(p)

    available = ", ".join(BUILTIN_PIPELINES.keys())
    raise ValueError(f"Unknown pipeline '{name_or_path}'. Built-ins: {available}")


def interpolate_prompt(template: str, context: dict[str, Any]) -> str:
    """Safely format prompt template using context variables."""
    # Convert all context values to string representation
    str_context = {k: str(v) if v is not None else "" for k, v in context.items()}
    try:
        return template.format_map(str_context)
    except KeyError:
        # Fallback for missing keys: format available ones without crashing
        result = template
        for k, v in str_context.items():
            result = result.replace(f"{{{k}}}", v)
        return result


def run_pipeline(
    pipeline: PipelineDefinition | str,
    task: str,
    *,
    initial_context: dict[str, Any] | None = None,
    store: MemoryStore | None = None,
    client: Any = None,
    on_step_start: Callable[[PipelineStep, int, int], None] | None = None,
    on_step_complete: Callable[[StepResult, int, int], None] | None = None,
    verbose: bool = False,
) -> PipelineResult:
    """Execute a multi-agent team pipeline sequentially.

    Passes outputs of earlier stages into subsequent prompt templates.
    """
    definition = get_pipeline(pipeline) if isinstance(pipeline, str) else pipeline

    context: dict[str, Any] = {"task": task}
    if initial_context:
        context.update(initial_context)

    pipeline_start = time.time()
    step_results: list[StepResult] = []
    total_tokens = 0
    all_success = True

    total_steps = len(definition.steps)
    for idx, step in enumerate(definition.steps, 1):
        if on_step_start:
            on_step_start(step, idx, total_steps)

        step_prompt = interpolate_prompt(step.prompt_template, context)
        step_start = time.time()

        try:
            agent_res = run_persona_task(
                persona=step.persona,
                task=step_prompt,
                with_skills=step.with_skills,
                max_iterations=step.max_iterations,
                store=store,
                model=step.model,
                provider=step.provider,
                client=client,
                verbose=verbose,
            )
            duration = time.time() - step_start
            step_tokens = agent_res.usage.get("total_tokens", 0)
            total_tokens += step_tokens

            step_res = StepResult(
                step_name=step.name,
                persona=step.persona,
                output=agent_res.text,
                iterations=agent_res.iterations,
                usage=agent_res.usage,
                duration_seconds=duration,
                is_error=False,
            )
            if step.output_key:
                context[step.output_key] = agent_res.text

        except Exception as exc:  # noqa: BLE001
            duration = time.time() - step_start
            logger.error("Step '%s' (%s) failed: %s", step.name, step.persona, exc)
            all_success = False
            step_res = StepResult(
                step_name=step.name,
                persona=step.persona,
                output="",
                iterations=0,
                usage={"total_tokens": 0},
                duration_seconds=duration,
                is_error=True,
                error_message=str(exc),
            )
            if step.output_key:
                context[step.output_key] = f"ERROR: {exc}"

        step_results.append(step_res)
        if on_step_complete:
            on_step_complete(step_res, idx, total_steps)

        if step_res.is_error:
            # Stop pipeline execution on failure
            break

    total_duration = time.time() - pipeline_start

    # Generate summary report
    summary_lines = [
        f"## Team Workflow Summary: {definition.name}",
        f"**Task:** {task}",
        f"**Status:** {'Success ✅' if all_success else 'Failed ❌'}",
        f"**Total Duration:** {total_duration:.2f}s | **Total Tokens:** {total_tokens:,}",
        "",
        "### Step Breakdown:",
    ]
    for s in step_results:
        status_icon = "❌" if s.is_error else "✅"
        summary_lines.append(
            f"- **[{s.step_name}]** ({s.persona.upper()}) {status_icon} — {s.duration_seconds:.2f}s, {s.iterations} iters, {s.usage.get('total_tokens', 0):,} tokens"
        )
        if s.is_error and s.error_message:
            summary_lines.append(f"  *Error:* {s.error_message}")

    summary_lines.append("\n### Final Deliverable:")
    if step_results and not step_results[-1].is_error:
        summary_lines.append(step_results[-1].output)
    else:
        summary_lines.append("Pipeline execution halted due to error.")

    return PipelineResult(
        pipeline_name=definition.name,
        task=task,
        steps=step_results,
        context=context,
        total_duration_seconds=total_duration,
        total_tokens=total_tokens,
        success=all_success,
        summary="\n".join(summary_lines),
    )
