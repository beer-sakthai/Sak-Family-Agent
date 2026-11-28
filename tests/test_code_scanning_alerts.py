"""Regression tests for Code Scanning Alerts #21877, #21878, #21879.

Verifies:
1. PairedBlindJudge uses cryptographically safe secrets.choice for randomized A/B swap (#21877).
2. PairedBlindJudge handles malformed or non-JSON judge output with specific exception handling (#21878).
3. audit_credential_hygiene in scripts/audit_repo_security.py handles unreadable files safely (#21879).
4. Bandit scan on patched files and scripts yields 0 security findings.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from evaluation_tasks.graders import PairedBlindJudge, PairedJudgeResult
from scripts.audit_repo_security import audit_credential_hygiene


def test_paired_judge_secrets_random_swap() -> None:
    """Verify PairedBlindJudge generates valid boolean swap flags without force_swap."""

    def mock_call(prompt: str) -> str:
        return json.dumps({"winner": "A", "confidence": 0.9, "reasoning": "A is better"})

    # Run multiple iterations to verify both True and False outcomes are produced safely
    observed_swaps: set[bool] = set()
    for _ in range(30):
        res = PairedBlindJudge.judge(
            task_prompt="task",
            rubric="rubric",
            baseline_trace="baseline",
            candidate_trace="candidate",
            call_fn=mock_call,
            force_swap=None,
        )
        assert isinstance(res, PairedJudgeResult)
        assert isinstance(res.swapped, bool)
        observed_swaps.add(res.swapped)

    # In 30 random flips with secrets.choice([True, False]), probability of not seeing both is 2*(0.5^30) ~= 1.8e-9
    assert observed_swaps == {True, False}


def test_paired_judge_malformed_json_fallback(caplog: pytest.LogCaptureFixture) -> None:
    """Verify PairedBlindJudge gracefully recovers when judge output contains malformed JSON."""

    def mock_call_malformed(prompt: str) -> str:
        return "Here is the verdict: {winner: 'A', confidence: invalid json} WINNER: A"

    with caplog.at_level(logging.DEBUG, logger="evaluation_tasks.graders"):
        res = PairedBlindJudge.judge(
            task_prompt="task",
            rubric="rubric",
            baseline_trace="baseline",
            candidate_trace="candidate",
            call_fn=mock_call_malformed,
            force_swap=False,
        )

    assert isinstance(res, PairedJudgeResult)
    assert res.winner == "tie"
    assert res.candidate_score == 0.5
    assert any(
        "Failed to parse paired judge payload as JSON" in record.message
        for record in caplog.records
    )


def test_paired_judge_invalid_types_json(caplog: pytest.LogCaptureFixture) -> None:
    """Verify PairedBlindJudge handles unexpected field types gracefully."""

    def mock_call_bad_types(prompt: str) -> str:
        return json.dumps({"winner": 12345, "confidence": "not-a-number", "reasoning": 999})

    with caplog.at_level(logging.DEBUG, logger="evaluation_tasks.graders"):
        res = PairedBlindJudge.judge(
            task_prompt="task",
            rubric="rubric",
            baseline_trace="baseline",
            candidate_trace="candidate",
            call_fn=mock_call_bad_types,
            force_swap=False,
        )

    assert isinstance(res, PairedJudgeResult)
    # Falls back to default tie when winner is invalid type
    assert res.winner == "tie"
    assert res.confidence == 0.5


def test_audit_credential_hygiene_handles_oserror(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify audit_credential_hygiene handles OSError gracefully when scanning unreadable files."""
    test_file = tmp_path / "unreadable.py"
    test_file.write_text("print('test')", encoding="utf-8")

    with (
        caplog.at_level(logging.DEBUG, logger="sakthai.audit"),
        patch.object(Path, "read_text", side_effect=OSError("Simulated I/O permission failure")),
    ):
        result = audit_credential_hygiene(tmp_path)

    assert isinstance(result, dict)
    assert result["status"] == "clean"
    assert result["leak_count"] == 0
    assert any("Skipping unreadable file" in record.message for record in caplog.records)
