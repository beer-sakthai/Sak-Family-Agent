"""Tests for the self-healing log ingestor.

The fixtures below are shaped like real GitHub Actions output — timestamp
prefixes, ``##[group]`` markers, ANSI colour — because that is what the ingestor
actually receives. A parser tested only against hand-cleaned text passes while
being useless on a live log.
"""

from __future__ import annotations

from sakthai.selfheal import ingest
from sakthai.selfheal.ingest import parse_job_log

PYTEST_LONG_LOG = """\
============================= test session starts ==============================
collected 4 items

tests/test_math.py ..F.                                                  [100%]

=================================== FAILURES ===================================
_________________________________ test_divide __________________________________

    def test_divide():
>       result = divide(1, 0)

tests/test_math.py:12:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

a = 1, b = 0

    def divide(a, b):
>       return a / b
E       ZeroDivisionError: division by zero

sakthai/calc.py:5: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_math.py::test_divide - ZeroDivisionError: division by zero
1 failed, 3 passed in 0.11s
"""

PYTEST_SHORT_LOG = """\
=================================== FAILURES ===================================
______________________ TestAdder.test_addition_is_correct ______________________
tests/test_adder.py:20: in test_addition_is_correct
    assert add(1, 2) == 4
E   assert 3 == 4
=========================== short test summary info ============================
FAILED tests/test_adder.py::TestAdder::test_addition_is_correct - assert 3 == 4
"""


def test_parses_a_long_style_pytest_traceback() -> None:
    signals = parse_job_log(PYTEST_LONG_LOG)

    assert len(signals) == 1
    signal = signals[0]
    assert signal.tool == "pytest"
    assert signal.error_type == "ZeroDivisionError"
    assert signal.message == "division by zero"
    assert signal.test_id == "tests/test_math.py::test_divide"


def test_innermost_frame_is_where_the_error_was_raised() -> None:
    """The last frame — not the test — is what the diagnosis should look at first."""
    signal = parse_job_log(PYTEST_LONG_LOG)[0]

    assert signal.primary_frame is not None
    assert signal.primary_frame.path == "sakthai/calc.py"
    assert signal.primary_frame.line == 5
    # The test's own frame is still present, outermost-first.
    assert signal.frames[0].path == "tests/test_math.py"
    assert signal.frames[0].line == 12


def test_parses_short_style_traceback_and_rewritten_assertion() -> None:
    signal = parse_job_log(PYTEST_SHORT_LOG)[0]

    assert signal.error_type == "AssertionError"
    assert signal.message == "assert 3 == 4"
    assert signal.test_id == "tests/test_adder.py::TestAdder::test_addition_is_correct"
    assert signal.frames[-1].function == "test_addition_is_correct"


def test_strips_actions_timestamps_group_markers_and_ansi() -> None:
    decorated = "\n".join(
        f"2026-08-16T09:15:23.1234567Z {line}" for line in PYTEST_SHORT_LOG.splitlines()
    )
    decorated = "2026-08-16T09:15:22.0000000Z ##[group]Run pytest\n" + decorated
    decorated = decorated.replace("E   assert 3 == 4", "\x1b[31mE   assert 3 == 4\x1b[0m")

    signal = parse_job_log(decorated)[0]

    assert signal.error_type == "AssertionError"
    assert signal.test_id == "tests/test_adder.py::TestAdder::test_addition_is_correct"


def test_parses_native_traceback_frames() -> None:
    log = """\
=================================== ERRORS =====================================
_________________________ ERROR collecting test_x.py ___________________________
  File "tests/test_x.py", line 3, in <module>
    import sakthai.missing
E   ModuleNotFoundError: No module named 'sakthai.missing'
"""
    signal = parse_job_log(log)[0]

    assert signal.error_type == "ModuleNotFoundError"
    assert signal.frames[-1].path == "tests/test_x.py"
    assert signal.frames[-1].function == "<module>"


def test_falls_back_to_the_summary_when_the_failures_section_is_missing() -> None:
    """A truncated log still names its failing tests; that is enough to act on."""
    log = (
        "=========================== short test summary info ===========\n"
        "FAILED tests/test_thing.py::test_case - AssertionError: nope\n"
    )

    signals = parse_job_log(log)

    assert len(signals) == 1
    assert signals[0].test_id == "tests/test_thing.py::test_case"
    assert signals[0].error_type == "TestFailure"
    assert signals[0].frames[0].path == "tests/test_thing.py"


def test_summary_fallback_without_a_python_path_yields_no_frames() -> None:
    signals = parse_job_log("FAILED some-non-python-target - boom\n")

    assert signals[0].frames == ()


def test_block_without_an_error_line_uses_the_trailing_location_type() -> None:
    log = """\
=================================== FAILURES ===================================
________________________________ test_silent ___________________________________
    some context with no E-prefixed line
tests/test_silent.py:7: RuntimeError
"""
    signal = parse_job_log(log)[0]

    assert signal.error_type == "RuntimeError"
    assert signal.message == ""


def test_block_with_no_error_at_all_is_skipped() -> None:
    log = """\
=================================== FAILURES ===================================
________________________________ test_quiet ____________________________________
    nothing useful here
=========================== short test summary info ============================
"""
    assert parse_job_log(log) == []


def test_bare_non_assertion_error_line_is_typed_as_failure() -> None:
    log = """\
=================================== FAILURES ===================================
________________________________ test_odd ______________________________________
E   Fixture 'thing' not found
"""
    signal = parse_job_log(log)[0]

    assert signal.error_type == "Failure"
    assert signal.message == "Fixture 'thing' not found"


def test_multiple_failing_tests_become_separate_signals() -> None:
    log = """\
=================================== FAILURES ===================================
_________________________________ test_one _____________________________________
tests/test_a.py:5: in test_one
E   AssertionError: first
_________________________________ test_two _____________________________________
tests/test_b.py:9: in test_two
E   ValueError: second
=========================== short test summary info ============================
FAILED tests/test_a.py::test_one - AssertionError: first
FAILED tests/test_b.py::test_two - ValueError: second
"""
    signals = parse_job_log(log)

    assert [s.error_type for s in signals] == ["AssertionError", "ValueError"]
    assert [s.test_id for s in signals] == [
        "tests/test_a.py::test_one",
        "tests/test_b.py::test_two",
    ]


def test_parses_ruff_diagnostics() -> None:
    log = "personas/sakthai/sakthai/thing.py:12:5: F401 [*] `os` imported but unused\n"

    signal = parse_job_log(log)[0]

    assert signal.tool == "ruff"
    assert signal.error_type == "F401"
    assert signal.message == "`os` imported but unused"
    assert signal.frames[0].line == 12


def test_parses_mypy_diagnostics_with_and_without_a_code() -> None:
    log = (
        "sakthai/a.py:12: error: Incompatible return value type  [return-value]\n"
        "sakthai/b.py:3:7: error: Name 'x' is not defined\n"
    )
    signals = parse_job_log(log)

    assert [s.tool for s in signals] == ["mypy", "mypy"]
    assert signals[0].error_type == "return-value"
    assert signals[1].error_type == "error"
    assert signals[1].frames[0].path == "sakthai/b.py"


def test_parses_bandit_issue_and_location_pairs() -> None:
    log = """\
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True
   Severity: High   Confidence: High
   Location: ./sakthai/runner.py:42:8
"""
    signal = parse_job_log(log)[0]

    assert signal.tool == "bandit"
    assert signal.error_type == "B602"
    assert signal.frames[0].path == "./sakthai/runner.py"
    assert signal.frames[0].line == 42


def test_bandit_issue_without_a_location_is_dropped() -> None:
    assert parse_job_log(">> Issue: [B101:assert_used] assert detected\n") == []


def test_line_checkers_do_not_re_parse_the_pytest_section() -> None:
    """A traceback that quotes a ruff-shaped line must not become a second signal."""
    log = """\
=================================== FAILURES ===================================
_________________________________ test_lint ____________________________________
tests/test_lint.py:8: in test_lint
    assert "thing.py:12:5: F401 unused" not in output
E   AssertionError: lint output changed
"""
    signals = parse_job_log(log)

    assert [s.tool for s in signals] == ["pytest"]


def test_identical_failures_are_deduplicated() -> None:
    line = "sakthai/a.py:12:5: F401 [*] `os` imported but unused\n"

    assert len(parse_job_log(line * 3)) == 1


def test_signal_count_is_capped() -> None:
    log = "".join(f"sakthai/mod{i}.py:{i + 1}:1: F401 [*] unused\n" for i in range(40))

    assert len(parse_job_log(log)) == ingest.MAX_SIGNALS


def test_a_clean_log_yields_nothing() -> None:
    assert parse_job_log("42 passed in 3.10s\n") == []
    assert parse_job_log("") == []


def test_excerpt_is_bounded() -> None:
    body = "\n".join(f"    line {i}" for i in range(200))
    log = (
        "=================================== FAILURES ===================================\n"
        "_________________________________ test_big _____________________________________\n"
        f"{body}\n"
        "E   ValueError: too much\n"
    )
    signal = parse_job_log(log)[0]

    assert len(signal.excerpt.splitlines()) <= ingest.MAX_EXCERPT_LINES


def test_frames_are_bounded() -> None:
    frames = "\n".join(f"sakthai/deep{i}.py:{i + 1}: in recurse" for i in range(40))
    log = (
        "=================================== FAILURES ===================================\n"
        "________________________________ test_deep _____________________________________\n"
        f"{frames}\n"
        "E   RecursionError: too deep\n"
    )
    signal = parse_job_log(log)[0]

    assert len(signal.frames) == ingest.MAX_FRAMES
    # Keeping the *innermost* frames is what matters; the outer ones are dropped.
    assert signal.frames[-1].path == "sakthai/deep39.py"


def test_describe_is_readable_for_a_non_test_failure() -> None:
    signal = parse_job_log("sakthai/a.py:12:5: F401 [*] `os` imported but unused\n")[0]

    assert signal.describe() == "[ruff] F401: `os` imported but unused (sakthai/a.py)"


def test_describe_falls_back_when_there_is_no_frame() -> None:
    signals = parse_job_log("FAILED some-non-python-target - boom\n")

    assert signals[0].describe().endswith("(some-non-python-target)")


def test_normalise_handles_crlf_and_lone_cr() -> None:
    assert ingest.normalise("a\r\nb\rc") == ["a", "b", "c"]


def test_two_failures_sections_are_both_parsed() -> None:
    log = """\
=================================== FAILURES ===================================
_________________________________ test_one _____________________________________
E   AssertionError: first
=================================== FAILURES ===================================
_________________________________ test_two _____________________________________
E   ValueError: second
"""
    assert [s.error_type for s in parse_job_log(log)] == ["AssertionError", "ValueError"]
