"""End-to-end tests for the self-healing pipeline.

One test per leaf of the flow, each asserting on the terminal status *and* on
what happened to the working tree — a status of ``rolled_back`` is only
meaningful if the files really were restored.

Nothing here starts a model, git, or pytest: the completion, the test runner and
the command runner are all injected.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from sakthai.selfheal.models import HealStatus
from sakthai.selfheal.pipeline import HealConfig, heal

CALC_ORIGINAL = "def divide(a, b):\n    return a / b\n"
CALC_FIXED = "def divide(a, b):\n    return a / b if b else 0\n"

FAILING_LOG = """\
=================================== FAILURES ===================================
_________________________________ test_divide __________________________________
tests/test_math.py:12: in test_divide
    result = divide(1, 0)
sakthai/calc.py:2: in divide
    return a / b
E   ZeroDivisionError: division by zero
=========================== short test summary info ============================
FAILED tests/test_math.py::test_divide - ZeroDivisionError: division by zero
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "sakthai").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "sakthai" / "calc.py").write_text(CALC_ORIGINAL, encoding="utf-8")
    (root / "tests" / "test_math.py").write_text(
        "from sakthai.calc import divide\n\n\ndef test_divide():\n    assert divide(1, 0) == 0\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    return root


def _config(repo: Path, **overrides: object) -> HealConfig:
    defaults: dict[str, object] = {"repo_root": repo, "publish_fix": False}
    defaults.update(overrides)
    return HealConfig(**defaults)  # type: ignore[arg-type]


def _completion(**overrides: object):
    payload: dict[str, object] = {
        "summary": "Guard divide against a zero denominator",
        "root_cause": "divide() does not handle b == 0",
        "confidence": 0.92,
        "edits": [
            {"path": "sakthai/calc.py", "old": "return a / b", "new": "return a / b if b else 0"}
        ],
    }
    payload.update(overrides)

    def complete(system: str, user: str) -> str:
        return json.dumps(payload)

    return complete


def _tests(*returncodes: int):
    codes = list(returncodes) or [0]

    def runner(command: Sequence[str], cwd: Path, timeout: float) -> tuple[int, str]:
        return (codes.pop(0) if codes else 0), "pytest output"

    return runner


class _Git:
    """A fake git/gh that tracks the checked-out branch, so cleanup is real."""

    def __init__(self, fail_on: str = "") -> None:
        self.calls: list[tuple[str, ...]] = []
        self.fail_on = fail_on
        self.branch = "main"
        self.deleted: list[str] = []

    def __call__(self, command: Sequence[str], cwd: Path) -> tuple[int, str]:
        self.calls.append(tuple(command))
        joined = " ".join(command)
        if self.fail_on and self.fail_on in joined:
            return 1, "fatal: refused"
        if joined.startswith("git rev-parse"):
            return 0, f"{self.branch}\n"
        if command[:2] == ("git", "checkout"):
            self.branch = command[-1]
        elif command[:3] == ("git", "branch", "-D"):
            self.deleted.append(command[-1])
        elif command[0] == "gh":
            return 0, "https://github.com/o/r/pull/4"
        return 0, ""

    def ran(self, fragment: str) -> bool:
        return any(fragment in " ".join(call) for call in self.calls)


# -- the happy path ------------------------------------------------------


def test_a_verified_fix_is_applied_and_left_in_the_tree(repo: Path) -> None:
    outcome = heal(FAILING_LOG, _config(repo), completion=_completion(), test_runner=_tests(0, 0))

    assert outcome.status is HealStatus.FIXED
    assert outcome.healed is True
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_FIXED
    assert outcome.changed_files == ("sakthai/calc.py",)


def test_a_verified_fix_is_published_with_a_report(repo: Path) -> None:
    git = _Git()

    outcome = heal(
        FAILING_LOG,
        _config(repo, publish_fix=True, run_id="9911", run_url="https://x/runs/9911"),
        completion=_completion(),
        test_runner=_tests(0, 0),
        command_runner=git,
    )

    assert outcome.status is HealStatus.PUBLISHED
    assert outcome.branch == "selfheal/guard-divide-against-a-zero-denominator-9911"
    assert outcome.pull_request_url == "https://github.com/o/r/pull/4"
    assert git.ran("git push -u origin selfheal/")
    assert git.ran("gh pr create")
    assert "https://x/runs/9911" in outcome.report


def test_only_the_changed_file_is_staged(repo: Path) -> None:
    git = _Git()

    heal(
        FAILING_LOG,
        _config(repo, publish_fix=True),
        completion=_completion(),
        test_runner=_tests(0, 0),
        command_runner=git,
    )

    add = next(call for call in git.calls if call[:2] == ("git", "add"))
    assert add == ("git", "add", "--", "sakthai/calc.py")


def test_the_narrative_is_included_when_a_narrator_is_given(repo: Path) -> None:
    def narrator(system: str, user: str) -> str:
        return "The divisor was never checked before the division."

    outcome = heal(
        FAILING_LOG,
        _config(repo),
        completion=_completion(),
        narrator=narrator,
        test_runner=_tests(0, 0),
    )

    assert "The divisor was never checked" in outcome.report
    assert "model-generated" in outcome.report


def test_publishing_can_stop_before_opening_a_pr(repo: Path) -> None:
    git = _Git()

    outcome = heal(
        FAILING_LOG,
        _config(repo, publish_fix=True, open_pr=False),
        completion=_completion(),
        test_runner=_tests(0, 0),
        command_runner=git,
    )

    assert outcome.status is HealStatus.PUBLISHED
    assert outcome.pull_request_url == ""
    assert not git.ran("gh")


# -- the abort paths -----------------------------------------------------


def test_a_log_with_no_failure_changes_nothing(repo: Path) -> None:
    outcome = heal("42 passed in 1.2s\n", _config(repo), completion=_completion())

    assert outcome.status is HealStatus.NO_FAILURE
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL
    assert "no recognised failure" in outcome.report


def test_a_diagnosis_with_no_edits_reports_instead_of_fixing(repo: Path) -> None:
    outcome = heal(
        FAILING_LOG,
        _config(repo),
        completion=_completion(edits=[], root_cause="a transient runner network failure"),
    )

    assert outcome.status is HealStatus.NO_DIAGNOSIS
    assert "transient runner network failure" in outcome.report
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL


def test_an_unsafe_patch_aborts_before_touching_the_tree(repo: Path) -> None:
    outcome = heal(
        FAILING_LOG,
        _config(repo),
        completion=_completion(
            confidence=0.99,
            edits=[{"path": "pyproject.toml", "old": "[project]", "new": "[project] # x"}],
        ),
    )

    assert outcome.status is HealStatus.ABORTED_UNSAFE
    assert (repo / "pyproject.toml").read_text(encoding="utf-8") == "[project]\n"
    assert "protected path" in outcome.report


def test_low_confidence_aborts_even_when_the_patch_is_safe(repo: Path) -> None:
    outcome = heal(FAILING_LOG, _config(repo), completion=_completion(confidence=0.3))

    assert outcome.status is HealStatus.ABORTED_LOW_CONFIDENCE
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL
    assert "0.30" in outcome.report


def test_the_confidence_bar_is_configurable(repo: Path) -> None:
    outcome = heal(
        FAILING_LOG,
        _config(repo, min_confidence=0.95),
        completion=_completion(confidence=0.92),
        test_runner=_tests(0, 0),
    )

    assert outcome.status is HealStatus.ABORTED_LOW_CONFIDENCE


def test_a_dry_run_diagnoses_without_writing(repo: Path) -> None:
    outcome = heal(FAILING_LOG, _config(repo, dry_run=True), completion=_completion())

    assert outcome.status is HealStatus.DRY_RUN
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL
    assert outcome.diagnosis is not None
    assert outcome.diagnosis.confidence == 0.92


def test_an_edit_that_becomes_ambiguous_before_it_lands_is_refused(repo: Path) -> None:
    """A tree that moved between diagnosis and apply must fail closed, not fuzzy-match."""
    original = (repo / "sakthai" / "calc.py").read_text(encoding="utf-8")

    def completion(system: str, user: str) -> str:
        reply = _completion()(system, user)
        # The anchor now appears twice — exactly the race apply_edits guards.
        (repo / "sakthai" / "calc.py").write_text(original + original, encoding="utf-8")
        return reply

    outcome = heal(FAILING_LOG, _config(repo), completion=completion)

    assert outcome.status is HealStatus.ABORTED_UNSAFE
    assert "ambiguous" in outcome.report


def test_a_patch_error_at_apply_time_aborts_without_publishing(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.selfheal import patch as patch_module

    def failing_apply(edits: object, repo_root: object) -> object:
        raise patch_module.PatchError("disk went away")

    monkeypatch.setattr(patch_module, "apply_edits", failing_apply)
    git = _Git()

    outcome = heal(
        FAILING_LOG,
        _config(repo, publish_fix=True),
        completion=_completion(),
        command_runner=git,
    )

    assert outcome.status is HealStatus.ABORTED_UNSAFE
    assert "patch could not be applied" in outcome.detail
    assert git.calls == []


# -- the rollback path ---------------------------------------------------


def test_a_failing_verification_rolls_the_patch_back(repo: Path) -> None:
    outcome = heal(FAILING_LOG, _config(repo), completion=_completion(), test_runner=_tests(1))

    assert outcome.status is HealStatus.ROLLED_BACK
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL
    assert outcome.test_outcome is not None
    assert outcome.test_outcome.passed is False


def test_breaking_another_test_also_rolls_back(repo: Path) -> None:
    """The targeted test passing is not enough — the suite must stay green too."""
    outcome = heal(FAILING_LOG, _config(repo), completion=_completion(), test_runner=_tests(0, 1))

    assert outcome.status is HealStatus.ROLLED_BACK
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL


def test_a_rolled_back_run_never_pushes(repo: Path) -> None:
    git = _Git()

    heal(
        FAILING_LOG,
        _config(repo, publish_fix=True),
        completion=_completion(),
        test_runner=_tests(1),
        command_runner=git,
    )

    assert git.calls == []


def test_a_failed_push_rolls_back_and_cleans_the_branch(repo: Path) -> None:
    git = _Git(fail_on="git push")

    outcome = heal(
        FAILING_LOG,
        _config(repo, publish_fix=True),
        completion=_completion(),
        test_runner=_tests(0, 0),
        command_runner=git,
    )

    assert outcome.status is HealStatus.ROLLED_BACK
    assert "publishing failed" in outcome.detail
    assert (repo / "sakthai" / "calc.py").read_text(encoding="utf-8") == CALC_ORIGINAL
    assert git.ran("git checkout main")
    assert git.ran("git branch -D selfheal/")


def test_branch_cleanup_is_skipped_when_the_branch_was_never_created(repo: Path) -> None:
    git = _Git(fail_on="git checkout -b")

    outcome = heal(
        FAILING_LOG,
        _config(repo, publish_fix=True),
        completion=_completion(),
        test_runner=_tests(0, 0),
        command_runner=git,
    )

    assert outcome.status is HealStatus.ROLLED_BACK
    assert not git.ran("git branch -D")


# -- reporting -----------------------------------------------------------


def test_the_outcome_carries_the_signal_and_the_gathered_context(repo: Path) -> None:
    outcome = heal(FAILING_LOG, _config(repo), completion=_completion(), test_runner=_tests(0, 0))

    assert outcome.signal is not None
    assert outcome.signal.error_type == "ZeroDivisionError"
    assert [c.path for c in outcome.contexts] == ["sakthai/calc.py", "tests/test_math.py"]


def test_the_diagnosis_sees_the_innermost_frames_source(repo: Path) -> None:
    """The prompt must contain the code that raised, not just the test that called it."""
    seen: dict[str, str] = {}

    def completion(system: str, user: str) -> str:
        seen["user"] = user
        return _completion()(system, user)

    heal(FAILING_LOG, _config(repo), completion=completion, test_runner=_tests(0, 0))

    assert "def divide(a, b):" in seen["user"]


def test_the_first_and_most_specific_failure_is_the_one_acted_on(repo: Path) -> None:
    log = FAILING_LOG + "sakthai/calc.py:1:1: F401 [*] unused import\n"

    outcome = heal(log, _config(repo), completion=_completion(), test_runner=_tests(0, 0))

    assert outcome.signal is not None
    assert outcome.signal.tool == "pytest"
