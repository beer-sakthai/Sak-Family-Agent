"""Tests for the self-healing PR walkthrough.

The structured half of the report is generated from the pipeline's records, so
the tests pin that it cannot overstate what happened — a rolled-back run must
say the tests failed, and a missing narrative must not remove any section a
reviewer relies on.
"""

from __future__ import annotations

from sakthai.selfheal.models import Diagnosis, FailureSignal, ProposedEdit, VerificationResult
from sakthai.selfheal.walkthrough import (
    DEFAULT_WALKTHROUGH_MODEL,
    build_narrative_prompt,
    narrate,
    render_abort_report,
    render_report,
)

SIGNAL = FailureSignal(
    tool="pytest",
    error_type="ZeroDivisionError",
    message="division by zero",
    test_id="tests/test_math.py::test_divide",
)
DIAGNOSIS = Diagnosis(
    summary="Guard divide against a zero denominator",
    root_cause="divide() does not handle b == 0",
    confidence=0.91,
    edits=(ProposedEdit("sakthai/calc.py", "return a / b", "return a / b if b else 0"),),
)
PASSED = VerificationResult(
    passed=True, returncode=0, command=("uv", "run", "pytest", "tests/"), output=""
)
FAILED = VerificationResult(
    passed=False, returncode=1, command=("uv", "run", "pytest", "tests/"), output="1 failed"
)


def test_report_carries_every_section_a_reviewer_needs() -> None:
    report = render_report(
        SIGNAL, DIAGNOSIS, test_outcome=PASSED, changed_files=["sakthai/calc.py"]
    )

    for heading in ("Root cause", "Change", "Verification", "Safety review"):
        assert f"### {heading}" in report


def test_report_shows_the_diff_and_the_files_changed() -> None:
    report = render_report(
        SIGNAL, DIAGNOSIS, test_outcome=PASSED, changed_files=["sakthai/calc.py"]
    )

    assert "- return a / b" in report
    assert "+ return a / b if b else 0" in report
    assert "files changed: sakthai/calc.py" in report


def test_report_states_the_confidence_and_that_the_gate_found_nothing() -> None:
    report = render_report(SIGNAL, DIAGNOSIS, test_outcome=PASSED)

    assert "confidence: 0.91" in report
    assert "gate violations: _none_" in report


def test_report_links_the_failed_run_when_one_is_known() -> None:
    report = render_report(SIGNAL, DIAGNOSIS, run_url="https://github.com/o/r/actions/runs/1")

    assert "https://github.com/o/r/actions/runs/1" in report


def test_report_omits_the_run_line_when_there_is_no_url() -> None:
    assert "**Failed run**" not in render_report(SIGNAL, DIAGNOSIS)


def test_a_failed_verification_is_reported_as_failed_with_its_output() -> None:
    """The report must never read as a success when the tests went red."""
    report = render_report(SIGNAL, DIAGNOSIS, test_outcome=FAILED)

    assert "**FAILED (exit 1)**" in report
    assert "1 failed" in report


def test_a_passing_verification_does_not_dump_output() -> None:
    report = render_report(
        SIGNAL,
        DIAGNOSIS,
        test_outcome=VerificationResult(True, 0, ("uv", "run", "pytest"), "lots of output"),
    )

    assert "lots of output" not in report


def test_report_says_so_when_verification_never_ran() -> None:
    assert "verification did not run" in render_report(SIGNAL, DIAGNOSIS)


def test_report_says_so_when_nothing_was_edited() -> None:
    bare = Diagnosis(summary="s", root_cause="r", confidence=0.5)

    assert "no edits were applied" in render_report(SIGNAL, bare)


def test_report_falls_back_when_no_root_cause_was_reported() -> None:
    bare = Diagnosis(summary="s", root_cause="", confidence=0.5)

    assert "_not reported_" in render_report(SIGNAL, bare)


def test_narrative_is_labelled_as_model_generated() -> None:
    report = render_report(SIGNAL, DIAGNOSIS, narrative="It divides by zero.")

    assert "### Walkthrough _(model-generated)_" in report
    assert "It divides by zero." in report


def test_report_without_a_narrative_has_no_walkthrough_section() -> None:
    assert "### Walkthrough" not in render_report(SIGNAL, DIAGNOSIS)


def test_report_is_attributed_to_the_agent() -> None:
    assert "sakthai heal" in render_report(SIGNAL, DIAGNOSIS)


def test_report_redacts_secrets_that_reach_it() -> None:
    leaky = Diagnosis(
        summary="s",
        root_cause="the token ghp_abcdefghijklmnopqrstuvwxyz0123456789 was wrong",
        confidence=0.5,
    )

    assert "ghp_abcdefghijklmnopqrstuvwxyz0123456789" not in render_report(SIGNAL, leaky)


def test_long_edits_are_truncated_in_the_report() -> None:
    long_edit = Diagnosis(
        summary="s",
        root_cause="r",
        confidence=0.9,
        edits=(ProposedEdit("a.py", "old", "\n".join(f"line {i}" for i in range(50))),),
    )

    assert "… (truncated)" in render_report(SIGNAL, long_edit)


# -- narration -----------------------------------------------------------


def test_narrative_prompt_carries_the_before_and_after() -> None:
    prompt = build_narrative_prompt(SIGNAL, DIAGNOSIS, ["sakthai/calc.py"])

    assert "--- before ---" in prompt
    assert "return a / b if b else 0" in prompt
    assert "sakthai/calc.py" in prompt


def test_narrate_returns_the_model_text() -> None:
    def completion(system: str, user: str) -> str:
        return "  The divisor was never checked.  "

    assert narrate(SIGNAL, DIAGNOSIS, [], completion=completion) == "The divisor was never checked."


def test_narrate_without_a_model_is_empty() -> None:
    assert narrate(SIGNAL, DIAGNOSIS, [], completion=None) == ""


def test_a_provider_failure_does_not_break_the_report() -> None:
    """A PR must still open with a complete body when the narrator is down."""

    def failing(system: str, user: str) -> str:
        raise RuntimeError("503")

    narrative = narrate(SIGNAL, DIAGNOSIS, [], completion=failing)

    assert narrative == ""
    assert "### Root cause" in render_report(SIGNAL, DIAGNOSIS, narrative=narrative)


def test_narration_is_redacted() -> None:
    def leaky(system: str, user: str) -> str:
        return "the token was ghp_abcdefghijklmnopqrstuvwxyz0123456789"

    assert "ghp_abcdefghijklmnopqrstuvwxyz0123456789" not in narrate(
        SIGNAL, DIAGNOSIS, [], completion=leaky
    )


def test_the_narrator_defaults_to_a_cheap_summarisation_model() -> None:
    assert "gemini" in DEFAULT_WALKTHROUGH_MODEL


# -- abort report --------------------------------------------------------


def test_abort_report_states_the_reason_and_that_nothing_changed() -> None:
    report = render_abort_report(SIGNAL, DIAGNOSIS, "confidence below the bar")

    assert "no fix applied" in report
    assert "confidence below the bar" in report
    assert "No files were changed" in report


def test_abort_report_lists_the_gate_violations() -> None:
    blocked = Diagnosis(
        summary="s",
        root_cause="r",
        confidence=0.99,
        edits=(ProposedEdit("a", "b", "c"),),
        violations=("edit 1 (a): a is a protected path",),
    )

    assert "protected path" in render_abort_report(SIGNAL, blocked, "unsafe")


def test_abort_report_works_with_no_signal_and_no_diagnosis() -> None:
    report = render_abort_report(None, None, "no recognised failure in the job log")

    assert "no recognised failure" in report
    assert "**Failure**" not in report
