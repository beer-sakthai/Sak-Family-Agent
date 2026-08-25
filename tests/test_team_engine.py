"""Tests for declarative team workflow engine and pipeline execution."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sakthai.agent.loop import AgentResult
from sakthai.team import (
    PipelineDefinition,
    PipelineStep,
    get_pipeline,
    list_builtin_pipelines,
    load_pipeline_from_dict,
    load_pipeline_from_file,
    run_pipeline,
)
from sakthai.team.engine import interpolate_prompt


def test_list_builtin_pipelines() -> None:
    pipelines = list_builtin_pipelines()
    assert "feature-delivery" in pipelines
    assert "code-review" in pipelines
    assert "research-brief" in pipelines
    assert "daily-sync" in pipelines


def test_get_pipeline_by_name() -> None:
    p = get_pipeline("feature-delivery")
    assert p.name == "feature-delivery"
    assert len(p.steps) == 4
    assert [s.persona for s in p.steps] == ["sakthai", "sakking", "saksee", "sakjules"]


def test_get_pipeline_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown pipeline 'nonexistent'"):
        get_pipeline("nonexistent")


def test_interpolate_prompt() -> None:
    template = "Plan: {plan}\nTask: {task}\nExtra: {missing}"
    context = {"plan": "My Plan", "task": "My Task"}
    res = interpolate_prompt(template, context)
    assert "Plan: My Plan" in res
    assert "Task: My Task" in res


def test_load_pipeline_from_dict_valid() -> None:
    data = {
        "name": "custom-test",
        "description": "Test custom pipeline",
        "steps": [
            {
                "name": "step1",
                "persona": "sakthai",
                "prompt_template": "Task: {task}",
                "output_key": "step1_out",
            }
        ],
    }
    pipeline = load_pipeline_from_dict(data)
    assert pipeline.name == "custom-test"
    assert len(pipeline.steps) == 1
    assert pipeline.steps[0].name == "step1"
    assert pipeline.steps[0].output_key == "step1_out"


def test_load_pipeline_from_dict_empty_steps() -> None:
    with pytest.raises(ValueError, match="must contain at least one step"):
        load_pipeline_from_dict({"name": "empty", "steps": []})


def test_load_pipeline_from_json_file(tmp_path: Path) -> None:
    pipeline_file = tmp_path / "pipeline.json"
    pipeline_file.write_text(
        json.dumps(
            {
                "name": "file-pipeline",
                "description": "File pipeline description",
                "steps": [
                    {
                        "name": "step_a",
                        "persona": "sakking",
                        "prompt_template": "Build: {task}",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_pipeline_from_file(pipeline_file)
    assert loaded.name == "file-pipeline"
    assert len(loaded.steps) == 1


def test_run_pipeline_success() -> None:
    def fake_run_persona(persona: str, task: str, **kwargs):
        return AgentResult(
            text=f"Output from {persona} for: {task[:20]}",
            iterations=2,
            stop_reason="end_turn",
            usage={"input_tokens": 50, "output_tokens": 25, "total_tokens": 75},
        )

    pipeline = PipelineDefinition(
        name="test-pipe",
        description="Testing execution",
        steps=(
            PipelineStep(
                name="step1",
                persona="sakthai",
                prompt_template="Scope: {task}",
                output_key="plan",
            ),
            PipelineStep(
                name="step2",
                persona="sakking",
                prompt_template="Code based on: {plan}",
                output_key="code",
            ),
        ),
    )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_run_persona):
        result = run_pipeline(pipeline, "Build a widget")

        assert result.success is True
        assert len(result.steps) == 2
        assert result.total_tokens == 150
        assert "plan" in result.context
        assert "code" in result.context
        assert "Team Workflow Summary: test-pipe" in result.summary


def test_run_pipeline_step_failure() -> None:
    def fake_failing_persona(persona: str, task: str, **kwargs):
        raise RuntimeError("LLM rate limit reached")

    pipeline = PipelineDefinition(
        name="failing-pipe",
        description="Testing failure",
        steps=(
            PipelineStep(
                name="step1",
                persona="sakthai",
                prompt_template="Task: {task}",
                output_key="plan",
            ),
            PipelineStep(
                name="step2",
                persona="sakking",
                prompt_template="Never reached: {plan}",
            ),
        ),
    )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_failing_persona):
        result = run_pipeline(pipeline, "Will fail")

        assert result.success is False
        assert len(result.steps) == 1
        assert result.steps[0].is_error is True
        assert "LLM rate limit reached" in (result.steps[0].error_message or "")
