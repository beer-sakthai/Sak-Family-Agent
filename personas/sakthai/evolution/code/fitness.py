"""Composite fitness evaluation for evolved tool source code.

Enforces a hard gate on unit tests (100% pass rate required), and scores
performance latency and static code quality into a weighted composite metric.
"""

from __future__ import annotations

import ast
import subprocess  # nosec B404
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .organism import GitBasedOrganism


@dataclass
class CodeFitnessScore:
    """Multi-dimensional fitness score for code mutations.

    Weights:
    - test_score (0.55): Hard gate. If test_score < 1.0 or passed_all_tests is False,
      composite is strictly 0.0.
    - latency_score (0.25): Benchmark speedup or normalized runtime latency score.
    - quality_score (0.20): Static AST cleanliness and exception-handling preservation.
    """

    test_score: float = 0.0
    latency_score: float = 0.0
    quality_score: float = 0.0
    passed_all_tests: bool = False
    execution_time_ms: float = 0.0
    feedback: str = ""

    @property
    def composite(self) -> float:
        """Weighted composite score enforcing test gate."""
        if not self.passed_all_tests or self.test_score < 1.0:
            return 0.0
        raw = 0.55 * self.test_score + 0.25 * self.latency_score + 0.20 * self.quality_score
        return max(0.0, min(1.0, raw))


class CompositeFitnessEvaluator:
    """Evaluates code organisms using unit tests, benchmarks, and AST heuristics."""

    def __init__(
        self,
        baseline_latency_ms: float = 100.0,
        test_fn: Callable[[], bool] | None = None,
        benchmark_fn: Callable[[], float] | None = None,
        test_command: list[str] | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.baseline_latency_ms = max(0.001, baseline_latency_ms)
        self.test_fn = test_fn
        self.benchmark_fn = benchmark_fn
        self.test_command = test_command
        self.timeout_seconds = timeout_seconds

    def evaluate_static_quality(self, code: str) -> float:
        """Score static AST cleanliness, error handling, and structure (0.0 to 1.0)."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.0

        score = 0.5  # Base score for valid syntax

        # Check for exception handling (error handling preservation)
        has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(tree))
        if has_try_except:
            score += 0.25

        # Check for docstrings or function comments
        has_docstring = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                if ast.get_docstring(node):
                    has_docstring = True
                    break
        if has_docstring:
            score += 0.15

        # Check for type annotations
        has_annotations = any(
            isinstance(node, ast.FunctionDef) and (node.returns or any(arg.annotation for arg in node.args.args))
            for node in ast.walk(tree)
        )
        if has_annotations:
            score += 0.10

        return max(0.0, min(1.0, score))

    def run_tests(self) -> tuple[bool, float, str]:
        """Execute test gate via callable or subprocess command."""
        if self.test_fn is not None:
            try:
                res = self.test_fn()
                if isinstance(res, tuple):
                    passed_count, total_count = res
                    passed = passed_count == total_count and total_count > 0
                    ratio = (passed_count / total_count) if total_count > 0 else 0.0
                    return passed, ratio, f"{passed_count}/{total_count} tests passed"
                passed = bool(res)
                return passed, (1.0 if passed else 0.0), ("Pass" if passed else "Fail")
            except Exception as e:
                return False, 0.0, f"Test exception: {e}"

        if self.test_command:
            try:
                proc = subprocess.run(  # nosec B603
                    self.test_command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
                passed = proc.returncode == 0
                return passed, (1.0 if passed else 0.0), proc.stdout[-500:]
            except subprocess.TimeoutExpired:
                return False, 0.0, "Test execution timed out."
            except Exception as e:
                return False, 0.0, f"Subprocess error: {e}"

        # Default fallback if no test runner configured: pass
        return True, 1.0, "No tests configured."

    def run_benchmark(self) -> tuple[float, float]:
        """Measure execution latency and calculate normalized latency score."""
        t0 = time.perf_counter()
        if self.benchmark_fn is not None:
            try:
                measured_latency = self.benchmark_fn()
            except Exception:
                measured_latency = self.baseline_latency_ms * 2.0
        else:
            measured_latency = (time.perf_counter() - t0) * 1000.0

        # Latency score: 1.0 if faster than or equal to baseline, degrades as latency increases
        if measured_latency <= self.baseline_latency_ms:
            latency_score = 1.0
        else:
            latency_score = max(0.0, 1.0 - ((measured_latency - self.baseline_latency_ms) / self.baseline_latency_ms))

        return measured_latency, max(0.0, min(1.0, latency_score))

    def evaluate(self, organism: GitBasedOrganism) -> CodeFitnessScore:
        """Evaluate organism code and compute composite fitness."""
        quality_score = self.evaluate_static_quality(organism.current_content)
        passed_tests, test_score, test_feedback = self.run_tests()
        measured_latency, latency_score = self.run_benchmark()

        feedback = (
            f"Tests: {test_feedback}. Latency: {measured_latency:.2f}ms (score: {latency_score:.2f}). "
            f"Quality: {quality_score:.2f}."
        )

        return CodeFitnessScore(
            test_score=test_score,
            latency_score=latency_score,
            quality_score=quality_score,
            passed_all_tests=passed_tests,
            execution_time_ms=measured_latency,
            feedback=feedback,
        )
