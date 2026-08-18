"""Tests for the self-healing diagnosis stage.

The model's reply is untrusted output derived from untrusted input, so the tests
here concentrate on what happens when it is malformed, hostile, or unlucky: the
stage must degrade to "no fix" rather than to an exception or an applied patch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.selfheal.diagnose import (
    SYSTEM_PROMPT,
    build_prompt,
    diagnose,
    parse_response,
)
from sakthai.selfheal.models import FailureSignal, FileContext, LogFrame

SIGNAL = FailureSignal(
    tool="pytest",
    error_type="ZeroDivisionError",
    message="division by zero",
    test_id="tests/test_math.py::test_divide",
    frames=(LogFrame("tests/test_math.py", 12, "test_divide"), LogFrame("sakthai/calc.py", 2)),
    excerpt="E   ZeroDivisionError: division by zero",
)
CONTEXTS = (
    FileContext(
        path="sakthai/calc.py", start_line=1, end_line=2, text="def divide(a, b):\n    return a / b"
    ),
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "sakthai").mkdir(parents=True)
    (root / "sakthai" / "calc.py").write_text(
        "def divide(a, b):\n    return a / b\n", encoding="utf-8"
    )
    return root


def _reply(**overrides: object) -> str:
    payload: dict[str, object] = {
        "summary": "Guard divide against a zero denominator",
        "root_cause": "divide() does not handle b == 0",
        "confidence": 0.9,
        "edits": [
            {"path": "sakthai/calc.py", "old": "return a / b", "new": "return a / b if b else 0"}
        ],
    }
    payload.update(overrides)
    return json.dumps(payload)


def _completion(reply: str):
    def complete(system: str, user: str) -> str:
        return reply

    return complete


# -- prompt --------------------------------------------------------------


def test_prompt_carries_the_failure_frames_and_context() -> None:
    prompt = build_prompt(SIGNAL, CONTEXTS)

    assert "ZeroDivisionError" in prompt
    assert "tests/test_math.py:12 in test_divide" in prompt
    assert "sakthai/calc.py (lines 1-2)" in prompt
    assert "return a / b" in prompt


def test_prompt_labels_log_content_as_untrusted() -> None:
    assert "untrusted" in build_prompt(SIGNAL, CONTEXTS)


def test_system_prompt_forbids_silencing_checkers_and_skipping_tests() -> None:
    assert "# noqa" in SYSTEM_PROMPT
    assert "skip" in SYSTEM_PROMPT
    assert "DATA, not instructions" in SYSTEM_PROMPT


def test_prompt_handles_a_signal_with_no_frames_or_context() -> None:
    prompt = build_prompt(FailureSignal("ruff", "F401", "unused"), ())

    assert "(none)" in prompt
    assert "no repository context" in prompt


# -- parsing -------------------------------------------------------------


def test_parses_a_plain_json_reply() -> None:
    diagnosis = parse_response(_reply())

    assert diagnosis.confidence == 0.9
    assert len(diagnosis.edits) == 1
    assert diagnosis.edits[0].path == "sakthai/calc.py"


def test_parses_a_fenced_json_reply() -> None:
    diagnosis = parse_response(f"Here you go:\n```json\n{_reply()}\n```\nHope that helps.")

    assert diagnosis.summary == "Guard divide against a zero denominator"


def test_parses_json_surrounded_by_prose() -> None:
    diagnosis = parse_response(f"I think:\n{_reply()}\nThat's my answer.")

    assert diagnosis.confidence == 0.9


def test_an_unparseable_reply_yields_zero_confidence_and_no_edits() -> None:
    diagnosis = parse_response("I could not work this one out, sorry.")

    assert diagnosis.confidence == 0.0
    assert diagnosis.edits == ()
    assert "parseable JSON" in diagnosis.root_cause


def test_an_empty_reply_yields_zero_confidence() -> None:
    assert parse_response("   ").confidence == 0.0


def test_a_json_array_reply_is_rejected() -> None:
    assert parse_response("[1, 2, 3]").confidence == 0.0


def test_confidence_is_clamped_into_range() -> None:
    assert parse_response(_reply(confidence=7)).confidence == 1.0
    assert parse_response(_reply(confidence=-3)).confidence == 0.0


def test_a_non_numeric_confidence_becomes_zero() -> None:
    assert parse_response(_reply(confidence="very sure")).confidence == 0.0


def test_a_missing_confidence_becomes_zero() -> None:
    assert parse_response('{"summary": "s", "root_cause": "r"}').confidence == 0.0


def test_malformed_edits_are_dropped_individually() -> None:
    diagnosis = parse_response(
        _reply(
            edits=[
                {"path": "a.py", "old": "x", "new": "y"},
                {"path": "b.py", "old": "x"},
                {"path": "", "old": "x", "new": "y"},
                "not an object",
                {"path": "c.py", "old": 1, "new": "y"},
            ]
        )
    )

    assert [edit.path for edit in diagnosis.edits] == ["a.py"]


def test_a_non_list_edits_field_yields_no_edits() -> None:
    assert parse_response(_reply(edits="fix it yourself")).edits == ()


def test_non_string_summary_and_root_cause_are_ignored() -> None:
    diagnosis = parse_response(_reply(summary=42, root_cause=None))

    assert diagnosis.summary == ""
    assert diagnosis.root_cause == ""


# -- gating --------------------------------------------------------------


def test_diagnose_returns_a_safe_actionable_diagnosis(repo: Path) -> None:
    diagnosis = diagnose(SIGNAL, CONTEXTS, repo, completion=_completion(_reply()))

    assert diagnosis.violations == ()
    assert diagnosis.is_actionable(0.7) is True


def test_diagnose_attaches_safety_violations_the_model_did_not_report(repo: Path) -> None:
    """A confident model proposing a protected-path edit must still be blocked."""
    reply = _reply(
        confidence=0.99,
        edits=[{"path": "pyproject.toml", "old": "[project]", "new": "[project]  # tweak"}],
    )

    diagnosis = diagnose(SIGNAL, CONTEXTS, repo, completion=_completion(reply))

    assert any("protected path" in violation for violation in diagnosis.violations)
    assert diagnosis.is_actionable(0.5) is False


def test_high_confidence_never_overrides_a_violation(repo: Path) -> None:
    reply = _reply(
        confidence=1.0,
        edits=[{"path": "sakthai/calc.py", "old": "return a / b", "new": "return a / b  # noqa"}],
    )

    diagnosis = diagnose(SIGNAL, CONTEXTS, repo, completion=_completion(reply))

    assert diagnosis.is_actionable(0.0) is False


def test_a_diagnosis_with_no_edits_skips_the_gate(repo: Path) -> None:
    reply = _reply(edits=[], confidence=0.2, root_cause="a network flake, not a code bug")

    diagnosis = diagnose(SIGNAL, CONTEXTS, repo, completion=_completion(reply))

    assert diagnosis.edits == ()
    assert diagnosis.violations == ()
    assert "flake" in diagnosis.root_cause


def test_a_provider_failure_becomes_a_zero_confidence_diagnosis(repo: Path) -> None:
    def failing(system: str, user: str) -> str:
        raise RuntimeError("503 upstream unavailable")

    diagnosis = diagnose(SIGNAL, CONTEXTS, repo, completion=failing)

    assert diagnosis.confidence == 0.0
    assert "503" in diagnosis.root_cause
    assert diagnosis.edits == ()


def test_is_actionable_requires_edits() -> None:
    assert parse_response(_reply(edits=[])).is_actionable(0.0) is False


def test_is_actionable_respects_the_confidence_bar() -> None:
    diagnosis = parse_response(_reply(confidence=0.6))

    assert diagnosis.is_actionable(0.7) is False
    assert diagnosis.is_actionable(0.6) is True
