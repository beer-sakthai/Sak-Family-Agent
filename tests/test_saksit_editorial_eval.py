"""Tests for SakSit Multi-Pass Editorial and Generative Engine Optimization (GEO) Evaluator."""

from __future__ import annotations

import unittest

from sakthai.agent.editorial_eval import (
    EditorialEvalResult,
    _calculate_grade,
    evaluate_editorial_quality,
)


class TestEditorialEval(unittest.TestCase):
    def test_authentic_well_structured_content_scores_high(self) -> None:
        content = """# Release v2.53.0: House of Sak Multi-Agent Architecture

Building from zero budget with free-tier tools, the House of Sak introduces persistent SQLite shards.

### Core Metrics
- Memory Query Latency: < 2ms (local WAL)
- Test Suite: 116 passing tests with >= 96% coverage
- Cost: $0.00 USD Financial Spend

According to the House of Sak architecture, each of the six agents maintains its own local memory shard under `~/.sakthai/`.
"""
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertGreaterEqual(result.total_score, 85.0)
        self.assertIn(result.grade, ("S", "A"))
        self.assertTrue(result.is_publishable)

    def test_hyperbolic_hype_content_penalized(self) -> None:
        content = """This is the most revolutionary, game-changing AI agent ever created!
It destroys all competition and performs unprecedented miracles with zero flaws!"""
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertLess(result.voice_score, 20.0)
        self.assertFalse(result.is_publishable)
        self.assertTrue(
            any("hype" in f.lower() or "buzzword" in f.lower() for f in result.findings)
        )

    def test_unverified_unflagged_metrics_penalized(self) -> None:
        content = "We have exactly 99.999% uptime and 500,000 active daily users on Hugging Face."
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertLess(result.precision_score, 25.0)

    def test_flagged_pending_verification_metrics_accepted(self) -> None:
        content = "We have [PENDING VERIFICATION: UPTIME] and [PENDING VERIFICATION: USER_COUNT]."
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertGreaterEqual(result.precision_score, 30.0)

    def test_calculate_grade_all_tiers(self) -> None:
        self.assertEqual(_calculate_grade(95.0), "S")
        self.assertEqual(_calculate_grade(85.0), "A")
        self.assertEqual(_calculate_grade(75.0), "B")
        self.assertEqual(_calculate_grade(65.0), "C")
        self.assertEqual(_calculate_grade(55.0), "D")
        self.assertEqual(_calculate_grade(45.0), "F")


if __name__ == "__main__":
    unittest.main()
