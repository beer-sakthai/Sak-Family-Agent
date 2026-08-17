"""Test runner — prove the patch actually fixed the thing, locally, before pushing.

Two runs, in order, and both must pass:

1. **Targeted** — just the failing test (or the module the diagnostic pointed
   at). Fast, and it answers the only question that matters first: did this fix
   the reported failure?
2. **Full** — the suite minus integration tests, the same selection ``ci.yml``
   uses. Slower, and it answers the second question: did the fix break anything
   else? Skipping it would let the agent push a patch that trades one red job
   for another.

The subprocess call is behind an injected :data:`CommandRunner` so the pipeline
can be tested without ever starting pytest.
"""

from __future__ import annotations

import logging
import subprocess  # nosec B404 — fixed argv, never a shell string
from collections.abc import Callable, Sequence
from pathlib import Path

from ..config import redact_secrets
from .models import FailureSignal, VerificationResult

logger = logging.getLogger(__name__)

CommandRunner = Callable[[Sequence[str], Path, float], tuple[int, str]]

DEFAULT_TIMEOUT = 900.0
# Enough of the tail to show the failure summary without carrying a whole log
# into a PR body.
MAX_OUTPUT_CHARS = 8_000

BASE_COMMAND: tuple[str, ...] = ("uv", "run", "pytest", "-m", "not integration", "-q")
FULL_TARGET = "tests/"


def default_runner(command: Sequence[str], cwd: Path, timeout: float) -> tuple[int, str]:
    """Run ``command`` with no shell, returning ``(returncode, combined output)``."""
    try:
        completed = subprocess.run(  # nosec B603 — argv list, no shell, fixed executable
            list(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, f"command not found: {exc}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout:.0f}s"
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def _tail(output: str) -> str:
    redacted = redact_secrets(output)
    if len(redacted) <= MAX_OUTPUT_CHARS:
        return redacted
    return "…(truncated)…\n" + redacted[-MAX_OUTPUT_CHARS:]


def targeted_selection(signal: FailureSignal) -> str | None:
    """The narrowest pytest selector for a signal, or ``None`` if there isn't one.

    A pytest failure gives a node id. A ruff/mypy/bandit finding does not point
    at a test at all, so there is nothing to target and only the full run applies.
    """
    if signal.tool == "pytest" and signal.test_id and "/" in signal.test_id:
        return signal.test_id
    return None


def build_commands(signal: FailureSignal | None) -> tuple[tuple[str, ...], ...]:
    """The ordered pytest invocations that verify a fix for ``signal``."""
    commands: list[tuple[str, ...]] = []
    if signal is not None and (selection := targeted_selection(signal)) is not None:
        commands.append((*BASE_COMMAND, selection))
    commands.append((*BASE_COMMAND, FULL_TARGET))
    return tuple(commands)


def run_tests(
    signal: FailureSignal | None,
    repo_root: Path,
    *,
    runner: CommandRunner | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> VerificationResult:
    """Run the verification suite, stopping at the first command that fails."""
    execute = runner or default_runner
    outcome = VerificationResult(passed=True, returncode=0, command=(), output="")

    for command in build_commands(signal):
        logger.info("selfheal: verifying with %s", " ".join(command))
        returncode, output = execute(command, repo_root, timeout)
        outcome = VerificationResult(
            passed=returncode == 0,
            returncode=returncode,
            command=command,
            output=_tail(output),
        )
        if returncode != 0:
            return outcome
    return outcome
