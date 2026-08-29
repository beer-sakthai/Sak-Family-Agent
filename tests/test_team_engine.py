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


def test_run_pipeline_parallel_batch() -> None:
    def fake_run_persona(persona: str, task: str, **kwargs):
        return AgentResult(
            text=f"Result from {persona}: {task[:15]}",
            iterations=1,
            stop_reason="end_turn",
            usage={"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
        )

    pipeline = PipelineDefinition(
        name="parallel-test",
        description="Parallel batch test",
        steps=(
            PipelineStep(
                name="p1",
                persona="saksee",
                prompt_template="Research: {task}",
                output_key="research",
                parallel_group="group_a",
            ),
            PipelineStep(
                name="p2",
                persona="sakking",
                prompt_template="Arch: {task}",
                output_key="arch",
                parallel_group="group_a",
            ),
            PipelineStep(
                name="synthesis",
                persona="sakthai",
                prompt_template="Combine {research} and {arch}",
                output_key="final",
            ),
        ),
    )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_run_persona):
        result = run_pipeline(pipeline, "Deep analysis")

        assert result.success is True
        assert len(result.steps) == 3
        assert "research" in result.context
        assert "arch" in result.context
        assert "final" in result.context
        assert result.total_tokens == 90


def test_stream_pipeline_events() -> None:
    from sakthai.team.engine import stream_pipeline_events

    def fake_run_persona(persona: str, task: str, **kwargs):
        return AgentResult(
            text=f"Output for {task[:10]}",
            iterations=1,
            stop_reason="end_turn",
            usage={"input_tokens": 10, "output_tokens": 10, "total_tokens": 20},
        )

    pipeline = PipelineDefinition(
        name="stream-test",
        description="Streaming test",
        steps=(
            PipelineStep(
                name="step1",
                persona="sakthai",
                prompt_template="Task: {task}",
                output_key="out",
            ),
        ),
    )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_run_persona):
        events = list(stream_pipeline_events(pipeline, "Stream task"))

        event_names = [e["event"] for e in events]
        assert "pipeline_start" in event_names
        assert "step_start" in event_names
        assert "step_complete" in event_names
        assert "pipeline_complete" in event_names


# --- Parser and loader edge cases -------------------------------------------


def test_load_pipeline_from_dict_skips_non_dict_steps() -> None:
    """Malformed step entries are skipped rather than aborting the whole load."""
    data = {
        "name": "mixed",
        "steps": [
            "not-a-step",
            42,
            {"name": "real", "persona": "sakthai"},
        ],
    }
    pipeline = load_pipeline_from_dict(data)
    assert [s.name for s in pipeline.steps] == ["real"]


def test_load_pipeline_from_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Pipeline file not found"):
        load_pipeline_from_file(tmp_path / "absent.json")


def test_load_pipeline_from_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "pipe.yaml"
    path.write_text(
        "name: yaml-pipe\ndescription: from yaml\nsteps:\n  - name: only\n    persona: saksee\n",
        encoding="utf-8",
    )
    pipeline = load_pipeline_from_file(path)
    assert pipeline.name == "yaml-pipe"
    assert pipeline.steps[0].persona == "saksee"


def test_load_pipeline_from_file_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError, match="Expected top-level object"):
        load_pipeline_from_file(path)


def test_get_pipeline_accepts_a_file_path(tmp_path: Path) -> None:
    """A name that is not a built-in but is a real file loads from disk."""
    path = tmp_path / "custom.json"
    path.write_text(
        json.dumps({"name": "from-disk", "steps": [{"name": "s", "persona": "saktan"}]}),
        encoding="utf-8",
    )
    assert get_pipeline(str(path)).name == "from-disk"


# --- Step grouping ----------------------------------------------------------


def _names(groups: list[list[PipelineStep]]) -> list[list[str]]:
    return [[s.name for s in g] for g in groups]


def test_group_steps_splits_adjacent_distinct_parallel_groups() -> None:
    """Two different parallel groups back to back must not merge into one batch."""
    from sakthai.team.engine import _group_steps

    steps = (
        PipelineStep(name="a", persona="sakthai", prompt_template="{task}", parallel_group="one"),
        PipelineStep(name="b", persona="sakking", prompt_template="{task}", parallel_group="one"),
        PipelineStep(name="c", persona="saksee", prompt_template="{task}", parallel_group="two"),
        PipelineStep(name="d", persona="saksit", prompt_template="{task}", parallel_group="two"),
    )
    assert _names(_group_steps(steps)) == [["a", "b"], ["c", "d"]]


def test_group_steps_flushes_a_trailing_parallel_group() -> None:
    """A parallel group at the very end still gets emitted."""
    from sakthai.team.engine import _group_steps

    steps = (
        PipelineStep(name="seq", persona="sakthai", prompt_template="{task}"),
        PipelineStep(name="p1", persona="sakking", prompt_template="{task}", parallel_group="tail"),
        PipelineStep(name="p2", persona="saksee", prompt_template="{task}", parallel_group="tail"),
    )
    assert _names(_group_steps(steps)) == [["seq"], ["p1", "p2"]]


# --- Parallel execution failure and callback paths --------------------------


def _parallel_pipeline() -> PipelineDefinition:
    return PipelineDefinition(
        name="parallel-fail",
        description="Two personas in one batch",
        steps=(
            PipelineStep(
                name="good",
                persona="sakthai",
                prompt_template="{task}",
                output_key="good_out",
                parallel_group="batch",
            ),
            PipelineStep(
                name="bad",
                persona="sakking",
                prompt_template="{task}",
                output_key="bad_out",
                parallel_group="batch",
            ),
        ),
    )


def test_run_pipeline_parallel_step_failure_is_captured() -> None:
    """A raising step in a parallel batch fails that step, not the whole process."""

    def fake_run_persona(persona: str, task: str, **kwargs):
        if persona == "sakking":
            raise RuntimeError("provider exploded")
        return AgentResult(
            text="fine",
            iterations=1,
            stop_reason="end_turn",
            usage={"total_tokens": 10},
        )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_run_persona):
        result = run_pipeline(_parallel_pipeline(), "go")

    assert result.success is False
    by_name = {s.step_name: s for s in result.steps}
    assert by_name["good"].is_error is False
    assert by_name["bad"].is_error is True
    assert "provider exploded" in (by_name["bad"].error_message or "")
    # The failing step still contributes its (empty) output under its key.
    assert result.context["bad_out"].startswith("ERROR:")
    assert result.context["good_out"] == "fine"
    # Only the healthy step's tokens count toward the total.
    assert result.total_tokens == 10


def test_run_pipeline_parallel_invokes_both_callbacks() -> None:
    """on_step_start/on_step_complete fire for every step in a parallel batch."""
    started: list[str] = []
    completed: list[str] = []

    def fake_run_persona(persona: str, task: str, **kwargs):
        return AgentResult(
            text="ok", iterations=1, stop_reason="end_turn", usage={"total_tokens": 5}
        )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_run_persona):
        result = run_pipeline(
            _parallel_pipeline(),
            "go",
            on_step_start=lambda step, idx, total: started.append(step.name),
            on_step_complete=lambda res, idx, total: completed.append(res.step_name),
        )

    assert result.success is True
    assert sorted(started) == ["bad", "good"]
    assert sorted(completed) == ["bad", "good"]


def test_run_pipeline_seeds_initial_context() -> None:
    """initial_context is available to the first prompt template."""
    seen: list[str] = []

    def fake_run_persona(persona: str, task: str, **kwargs):
        seen.append(task)
        return AgentResult(
            text="ok", iterations=1, stop_reason="end_turn", usage={"total_tokens": 1}
        )

    pipeline = PipelineDefinition(
        name="ctx",
        description="uses seeded context",
        steps=(PipelineStep(name="s", persona="sakthai", prompt_template="Brief: {brief}"),),
    )

    with patch("sakthai.team.engine.run_persona_task", side_effect=fake_run_persona):
        result = run_pipeline(pipeline, "task", initial_context={"brief": "seeded-value"})

    assert result.success is True
    assert seen == ["Brief: seeded-value"]


def test_stream_pipeline_events_emits_pipeline_error() -> None:
    """A crash inside the worker surfaces as a pipeline_error event, not a hang."""
    from sakthai.team.engine import stream_pipeline_events

    pipeline = PipelineDefinition(
        name="boom",
        description="explodes",
        steps=(PipelineStep(name="s", persona="sakthai", prompt_template="{task}"),),
    )

    with patch("sakthai.team.engine.run_pipeline", side_effect=RuntimeError("worker died")):
        events = list(stream_pipeline_events(pipeline, "task"))

    kinds = [e["event"] for e in events]
    assert "pipeline_error" in kinds
    error_event = next(e for e in events if e["event"] == "pipeline_error")
    assert error_event["error"] == "worker died"
    assert error_event["pipeline"] == "boom"
