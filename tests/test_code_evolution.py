"""Tests for Phase 4: Code Evolution via Darwinian Evolver (evolution.code)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from evolution.code import (
    CodeFitnessScore,
    CompositeFitnessEvaluator,
    DarwinianCodeEvolver,
    GitBasedOrganism,
    evolve_tool_code,
)


def test_organism_initialization_and_diff() -> None:
    """Verify GitBasedOrganism baseline loading, mutation, and diff generation."""
    code = 'def compute_total(a: int, b: int) -> int:\n    """Compute sum."""\n    return a + b\n'
    organism = GitBasedOrganism(source_code=code)
    assert organism.baseline_content == code
    assert organism.current_content == code
    assert organism.diff() == ""

    # Apply valid mutation
    mutated = (
        "def compute_total(a: int, b: int) -> int:\n"
        '    """Compute sum with hardened check."""\n'
        "    if a < 0 or b < 0:\n"
        "        raise ValueError('negative')\n"
        "    return a + b\n"
    )
    applied = organism.apply_mutation(mutated, generation=1)
    assert applied is True
    assert organism.current_content == mutated
    assert len(organism.checkpoints) == 2
    assert "ValueError" in organism.diff()

    # Rollback
    organism.rollback()
    assert organism.current_content == code
    assert organism.diff() == ""


def test_organism_syntax_and_signature_safety_gates() -> None:
    """Verify AST safety contracts: invalid syntax or broken function signatures are rejected."""
    code = "def query_database(query: str, limit: int = 10):\n    return [query] * limit\n"
    organism = GitBasedOrganism(source_code=code)

    # 1. Invalid syntax
    bad_syntax = "def broken(:\n    pass"
    applied_bad = organism.apply_mutation(bad_syntax)
    assert applied_bad is False
    assert organism.current_content == code

    # 2. Changed function signature (removed 'limit' argument)
    altered_sig = "def query_database(query: str):\n    return [query]\n"
    applied_altered = organism.apply_mutation(altered_sig)
    assert applied_altered is False
    assert organism.current_content == code

    # 3. Removed baseline function
    missing_fn = "def entirely_different_fn():\n    pass\n"
    applied_missing = organism.apply_mutation(missing_fn)
    assert applied_missing is False
    assert organism.current_content == code


def test_code_fitness_score_hard_gate() -> None:
    """Verify that failure on unit test gate clamps composite fitness to zero."""
    # Tests failed (test_score = 0.5)
    failing_score = CodeFitnessScore(
        test_score=0.5,
        latency_score=1.0,
        quality_score=1.0,
        passed_all_tests=False,
    )
    assert failing_score.composite == 0.0

    # Tests passed 100%
    passing_score = CodeFitnessScore(
        test_score=1.0,
        latency_score=0.8,
        quality_score=0.9,
        passed_all_tests=True,
    )
    expected = 0.55 * 1.0 + 0.25 * 0.8 + 0.20 * 0.9
    assert abs(passing_score.composite - expected) < 1e-4


def test_composite_fitness_evaluator() -> None:
    """Verify CompositeFitnessEvaluator runs tests, benchmarks, and AST quality scoring."""
    sample_code = (
        '"""Sample math helper module."""\n\n'
        "def safe_divide(x: float, y: float) -> float:\n"
        '    """Divide x by y with zero check."""\n'
        "    try:\n"
        "        return x / y\n"
        "    except ZeroDivisionError:\n"
        "        return 0.0\n"
    )
    organism = GitBasedOrganism(source_code=sample_code)

    evaluator = CompositeFitnessEvaluator(
        baseline_latency_ms=10.0,
        test_fn=lambda: (5, 5),  # 5/5 tests passed
        benchmark_fn=lambda: 5.0,  # 5ms (faster than baseline)
    )

    fitness = evaluator.evaluate(organism)
    assert fitness.passed_all_tests is True
    assert fitness.test_score == 1.0
    assert fitness.latency_score == 1.0
    assert fitness.quality_score > 0.7  # Has docstrings, try/except, annotations
    assert fitness.composite > 0.85


def test_darwinian_code_evolver_run() -> None:
    """Verify end-to-end generational evolution loop and selection."""
    code = "def calculate(n: int) -> int:\n    return n * 2\n"
    organism = GitBasedOrganism(source_code=code)
    evaluator = CompositeFitnessEvaluator(
        baseline_latency_ms=10.0,
        test_fn=lambda: True,
        benchmark_fn=lambda: 8.0,
    )

    evolver = DarwinianCodeEvolver(
        organism=organism,
        evaluator=evaluator,
        population_size=3,
        tool_name="test_tool",
    )

    result = evolver.run(generations=3, dry_run=True)
    assert result.success is True
    assert result.baseline_fitness.passed_all_tests is True
    assert result.final_fitness.passed_all_tests is True
    assert len(result.generations) == 3
    assert result.final_fitness.composite >= result.baseline_fitness.composite


def test_evolve_tool_code_convenience_helper() -> None:
    """Verify evolve_tool_code helper runs on a file path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tool_file = Path(tmp_dir) / "tool_sample.py"
        tool_file.write_text(
            "def run_action(payload: dict) -> bool:\n    return bool(payload)\n",
            encoding="utf-8",
        )

        result = evolve_tool_code(
            tool_file=tool_file,
            test_fn=lambda: True,
            generations=2,
            population_size=2,
            dry_run=True,
        )

        assert result.success is True
        assert result.tool_name == "tool_sample"
