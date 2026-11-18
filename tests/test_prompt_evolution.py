"""Tests for Phase 3: System Prompt Evolution (evolution.prompts)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from evolution.prompts import (
    EvolvablePromptSections,
    PromptEvalExample,
    PromptEvolutionModule,
    build_synthetic_prompt_dataset,
    evaluate_prompt_behavior,
    evolve_prompts,
    format_prompt_sections,
    parse_evolved_sections,
    prompt_fitness_metric,
    validate_prompt_constraints,
)

from sakthai.agent.prompt_builder import (
    DEFAULT_AGENT_IDENTITY,
    MEMORY_GUIDANCE,
    PLATFORM_HINTS,
    SESSION_SEARCH_GUIDANCE,
    SKILLS_GUIDANCE,
)


def test_prompt_sections_defaults() -> None:
    """Verify default values and dictionary serialization of EvolvablePromptSections."""
    sections = EvolvablePromptSections()
    assert sections.identity == DEFAULT_AGENT_IDENTITY
    assert sections.memory_guidance == MEMORY_GUIDANCE
    assert sections.session_guidance == SESSION_SEARCH_GUIDANCE
    assert sections.skills_guidance == SKILLS_GUIDANCE
    assert sections.platform_hints == PLATFORM_HINTS

    data = sections.to_dict()
    assert isinstance(data, dict)
    assert "identity" in data
    assert "memory_guidance" in data

    restored = EvolvablePromptSections.from_dict(data)
    assert restored == sections


def test_format_and_parse_prompt_sections() -> None:
    """Verify formatting sections into DSPy instructions and parsing them back."""
    custom_sections = EvolvablePromptSections(
        identity="Custom Identity 123",
        memory_guidance="Save everything important.",
        session_guidance="Always search last session.",
        skills_guidance="Follow skills strictly.",
        platform_hints="Format in JSON.",
    )

    formatted = format_prompt_sections(custom_sections)
    assert "[SECTION DEFAULT_AGENT_IDENTITY]" in formatted
    assert "[SECTION MEMORY_GUIDANCE]" in formatted
    assert "[SECTION SESSION_SEARCH_GUIDANCE]" in formatted
    assert "[SECTION SKILLS_GUIDANCE]" in formatted
    assert "[SECTION PLATFORM_HINTS]" in formatted
    assert "Custom Identity 123" in formatted

    parsed = parse_evolved_sections(formatted)
    assert parsed.identity == "Custom Identity 123"
    assert parsed.memory_guidance == "Save everything important."
    assert parsed.session_guidance == "Always search last session."
    assert parsed.skills_guidance == "Follow skills strictly."
    assert parsed.platform_hints == "Format in JSON."


def test_prompt_evolution_module_wiring() -> None:
    """Verify PromptEvolutionModule instructions reflect current prompt sections."""
    module = PromptEvolutionModule()
    assert module.sections.identity == DEFAULT_AGENT_IDENTITY

    mutated_sections = EvolvablePromptSections(
        identity="Evolved Identity Agent",
        memory_guidance="Evolved Memory Guidance",
        session_guidance="Evolved Session Search",
        skills_guidance="Evolved Skills Rules",
        platform_hints="Evolved Platform Guidance",
    )
    module.set_sections(mutated_sections)
    extracted = module.sections
    assert extracted.identity == "Evolved Identity Agent"
    assert extracted.memory_guidance == "Evolved Memory Guidance"
    assert extracted.session_guidance == "Evolved Session Search"


def test_render_full_prompt_integration() -> None:
    """Verify render_full_prompt passes all 5 sections to build_system_prompt."""
    sections = EvolvablePromptSections(
        identity="Unique Agent Identity",
        memory_guidance="Unique Memory Guidance",
        session_guidance="Unique Session Guidance",
        skills_guidance="Unique Skills Guidance",
        platform_hints="Unique Platform Hints",
    )

    full_prompt = sections.render_full_prompt(
        memory_block="FACT: User likes tea.",
        skills_block="SKILL: deploy",
        prefix="SYSTEM HEADER",
        fast=True,
    )

    assert "SYSTEM HEADER" in full_prompt
    assert "Unique Agent Identity" in full_prompt
    assert "FAST-TRACK MODE" in full_prompt
    assert "Unique Memory Guidance" in full_prompt
    assert "Unique Session Guidance" in full_prompt
    assert "Unique Skills Guidance" in full_prompt
    assert "Unique Platform Hints" in full_prompt
    assert "FACT: User likes tea." in full_prompt
    assert "SKILL: deploy" in full_prompt


def test_build_synthetic_prompt_dataset() -> None:
    """Verify synthetic behavioral evaluation dataset structure and coverage."""
    dataset = build_synthetic_prompt_dataset()
    assert len(dataset) >= 5

    sections_covered = {ex.section for ex in dataset}
    expected_sections = {
        "DEFAULT_AGENT_IDENTITY",
        "MEMORY_GUIDANCE",
        "SESSION_SEARCH_GUIDANCE",
        "SKILLS_GUIDANCE",
        "PLATFORM_HINTS",
    }
    assert expected_sections.issubset(sections_covered)


def test_evaluate_prompt_behavior() -> None:
    """Verify rule-based evaluation rewards target keywords and penalizes anti-keywords."""
    example = PromptEvalExample(
        section="MEMORY_GUIDANCE",
        task_input="Remember that I prefer pytest.",
        expected_behavior="Save preference with learn.",
        target_keywords=["learn", "preference"],
        anti_keywords=["forget"],
    )

    good_response = "I will use `learn` to record your preference for future sessions."
    good_score, feedback_good = evaluate_prompt_behavior(good_response, example)
    assert good_score > 0.8
    assert len(feedback_good) == 0

    bad_response = "I will forget this immediately."
    bad_score, feedback_bad = evaluate_prompt_behavior(bad_response, example)
    assert bad_score < good_score
    assert any("Contained undesirable" in f for f in feedback_bad)


def test_prompt_fitness_metric_length_penalty() -> None:
    """Verify length growth penalty kicks in when prompt size exceeds threshold."""
    example = MagicMock()
    example.eval_ex = PromptEvalExample(
        section="TEST",
        task_input="test task",
        expected_behavior="good behavior",
        target_keywords=["valid"],
        anti_keywords=[],
    )

    prediction = MagicMock()
    prediction.agent_response = "This is a valid response."

    # Normal length (no growth)
    score_normal = prompt_fitness_metric(
        example=example,
        prediction=prediction,
        baseline_length=1000,
        current_length=1050,  # 5% growth
        max_growth_ratio=0.20,
    )

    # Excessive length (> 20% growth)
    score_penalized = prompt_fitness_metric(
        example=example,
        prediction=prediction,
        baseline_length=1000,
        current_length=1500,  # 50% growth
        max_growth_ratio=0.20,
    )

    assert score_penalized < score_normal


def test_validate_prompt_constraints() -> None:
    """Verify constraint validation checks required sections and growth threshold."""
    baseline = EvolvablePromptSections()
    baseline_len = len(format_prompt_sections(baseline))

    # Baseline should pass cleanly
    errors = validate_prompt_constraints(baseline, baseline_len, max_growth=0.20)
    assert errors == []

    # Empty identity section should fail
    empty_identity = EvolvablePromptSections(identity="")
    errors = validate_prompt_constraints(empty_identity, baseline_len, max_growth=0.20)
    assert any("DEFAULT_AGENT_IDENTITY cannot be empty" in e for e in errors)

    # Huge prompt exceeding 20% growth should fail
    huge_sections = EvolvablePromptSections(identity="A" * (baseline_len * 2))
    errors = validate_prompt_constraints(huge_sections, baseline_len, max_growth=0.20)
    assert any("growth limit" in e for e in errors)


def test_evolve_prompts_dry_run() -> None:
    """Verify evolve_prompts runs cleanly in dry-run mode and writes JSON output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "prompt_summary.json"
        summary = evolve_prompts(dry_run=True, output_path=str(out_file))

        assert summary["status"] == "success"
        assert summary["dry_run"] is True
        assert summary["baseline_score"] > 0.0
        assert out_file.exists()
