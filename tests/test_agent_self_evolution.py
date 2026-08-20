"""Tests for Multi-Agent Self-Evolution and Prompt Optimization."""

import pytest

from sakthai.evolution.evolver import PersonaEvolver
from sakthai.evolution.feedback import FeedbackCollector
from sakthai.evolution.registry import EvolutionRegistry


@pytest.fixture
def registry() -> EvolutionRegistry:
    return EvolutionRegistry(db_path=":memory:")


@pytest.fixture
def feedback() -> FeedbackCollector:
    return FeedbackCollector(db_path=":memory:")


@pytest.fixture
def evolver(registry: EvolutionRegistry, feedback: FeedbackCollector) -> PersonaEvolver:
    return PersonaEvolver(registry=registry, feedback=feedback)


def test_initialize_persona_checkpoint(registry: EvolutionRegistry) -> None:
    chk = registry.initialize_persona(
        "sakjules", "You are SakJules, Master of Automation.", base_score=0.88
    )
    assert chk.persona == "sakjules"
    assert chk.generation == 0
    assert chk.composite_score == 0.88
    assert chk.is_active is True

    active = registry.get_active_checkpoint("sakjules")
    assert active is not None
    assert active.checkpoint_id == chk.checkpoint_id


def test_record_feedback_and_metrics(feedback: FeedbackCollector) -> None:
    feedback.record_feedback(
        persona="sakking",
        task_type="code_review",
        success=True,
        tool_errors=0,
        duration_sec=3.2,
        user_rating=5.0,
    )
    feedback.record_feedback(
        persona="sakking",
        task_type="bug_fix",
        success=False,
        tool_errors=2,
        duration_sec=8.5,
        user_rating=3.0,
        error_summary="Tool execution timeout",
    )

    metrics = feedback.get_persona_metrics("sakking")
    assert metrics["persona"] == "sakking"
    assert metrics["total_trajectories"] == 2
    assert metrics["success_rate"] == 0.5
    assert metrics["total_tool_errors"] == 2
    assert metrics["avg_duration_sec"] == 5.85


def test_generate_mutation_with_diff(evolver: PersonaEvolver) -> None:
    evolver.registry.initialize_persona("sakthai", "You are SakThai, the household core agent.")
    variant = evolver.generate_mutation("sakthai", focus_area="tool_discipline")

    assert variant.persona == "sakthai"
    assert variant.generation == 1
    assert "Strict Tool Discipline" in variant.mutated_prompt
    assert "generation_0" in variant.prompt_diff
    assert "generation_1" in variant.prompt_diff


def test_evaluate_and_promote_variant(evolver: PersonaEvolver) -> None:
    evolver.registry.initialize_persona(
        "saksee", "You are SakSee, research specialist.", base_score=0.75
    )
    variant, promoted = evolver.auto_evolve_step("saksee", focus_area="tool_discipline")

    assert promoted is True
    assert variant.status == "promoted"
    assert variant.score is not None
    assert variant.score.passed_safety_gate is True

    # Active checkpoint is now generation 1
    active = evolver.registry.get_active_checkpoint("saksee")
    assert active is not None
    assert active.generation == 1
    assert active.composite_score > 0.75


def test_rollback_checkpoint(evolver: PersonaEvolver) -> None:
    evolver.registry.initialize_persona("saksit", "You are SakSit, copywriter.", base_score=0.70)
    evolver.auto_evolve_step("saksit", focus_area="conciseness")

    # Current is generation 1
    active_g1 = evolver.registry.get_active_checkpoint("saksit")
    assert active_g1 is not None
    assert active_g1.generation == 1

    # Rollback to generation 0
    rolled_back = evolver.registry.rollback_to_generation("saksit", target_generation=0)
    assert rolled_back.generation == 0
    assert rolled_back.is_active is True

    current = evolver.registry.get_active_checkpoint("saksit")
    assert current is not None
    assert current.generation == 0
