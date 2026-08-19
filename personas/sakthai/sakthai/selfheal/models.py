"""Shared value types for the self-healing CI pipeline.

Every stage of the pipeline hands the next one a frozen dataclass, so a stage can
be tested in isolation by constructing its input directly. Nothing here touches
the filesystem, the network, or a model provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


@dataclass(frozen=True)
class LogFrame:
    """One implicated source location pulled out of a CI log."""

    path: str
    line: int
    function: str = ""


@dataclass(frozen=True)
class FailureSignal:
    """A single parsed CI failure: what broke, where, and how it was reported.

    ``tool`` names the checker that emitted the failure (``pytest``, ``ruff``,
    ``mypy``, ``bandit``). ``frames`` are ordered outermost-first, matching the
    order a traceback prints them, so :attr:`primary_frame` is the innermost —
    the line that actually raised.
    """

    tool: str
    error_type: str
    message: str
    test_id: str = ""
    frames: tuple[LogFrame, ...] = ()
    excerpt: str = ""

    @property
    def primary_frame(self) -> LogFrame | None:
        """The innermost frame — where the error was raised — or ``None``."""
        return self.frames[-1] if self.frames else None

    def describe(self) -> str:
        """One-line human summary, used in reports and log lines."""
        where = self.test_id or (self.primary_frame.path if self.primary_frame else "?")
        return f"[{self.tool}] {self.error_type}: {self.message} ({where})"


@dataclass(frozen=True)
class FileContext:
    """A verbatim slice of a repository file surrounding an implicated line.

    ``text`` is exactly what the file contains between ``start_line`` and
    ``end_line`` (both 1-based, inclusive) with no line numbers added, so a model
    can quote from it to build an exact-match edit.
    """

    path: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True)
class ProposedEdit:
    """One exact-string replacement inside a repository file.

    Deliberately not a unified diff: an exact ``old`` → ``new`` replacement that
    must match once and only once is far cheaper to validate, and a model that
    hallucinates context fails closed instead of applying a fuzzy hunk.
    """

    path: str
    old: str
    new: str


@dataclass(frozen=True)
class Diagnosis:
    """The diagnosis agent's verdict on a failure.

    ``violations`` is filled in by the safety gate, not the model — a non-empty
    tuple means the proposed edits were rejected regardless of ``confidence``.
    """

    summary: str
    root_cause: str
    confidence: float
    edits: tuple[ProposedEdit, ...] = ()
    violations: tuple[str, ...] = ()

    def is_actionable(self, min_confidence: float) -> bool:
        """True when there is something to apply, it is safe, and confidence clears the bar."""
        return bool(self.edits) and not self.violations and self.confidence >= min_confidence


@dataclass(frozen=True)
class VerificationResult:
    """The result of the local verification run."""

    passed: bool
    returncode: int
    command: tuple[str, ...]
    output: str


class HealStatus(StrEnum):
    """Terminal state of a healing attempt — one per leaf of the pipeline."""

    NO_FAILURE = "no_failure"
    NO_DIAGNOSIS = "no_diagnosis"
    DRY_RUN = "dry_run"
    ABORTED_UNSAFE = "aborted_unsafe"
    ABORTED_LOW_CONFIDENCE = "aborted_low_confidence"
    ROLLED_BACK = "rolled_back"
    FIXED = "fixed"
    PUBLISHED = "published"


@dataclass(frozen=True)
class HealingOutcome:
    """Everything a healing attempt produced, whatever branch of the flow it took."""

    status: HealStatus
    detail: str = ""
    signal: FailureSignal | None = None
    diagnosis: Diagnosis | None = None
    test_outcome: VerificationResult | None = None
    contexts: tuple[FileContext, ...] = ()
    branch: str = ""
    pull_request_url: str = ""
    report: str = ""
    changed_files: tuple[str, ...] = field(default_factory=tuple)

    @property
    def healed(self) -> bool:
        """True when a verified fix exists on disk (whether or not it was published)."""
        return self.status in (HealStatus.FIXED, HealStatus.PUBLISHED)
