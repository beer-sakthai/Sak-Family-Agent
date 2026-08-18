"""Publish stage — put a verified fix on its own branch and open a pull request.

Two invariants hold regardless of what the model proposed or what the caller
passed:

* **Never a protected branch.** Every branch this module creates must carry the
  configured prefix, and :data:`PROTECTED_BRANCHES` is refused outright. The
  agent's output is a proposal for review, not a commit to ``main``.
* **Only the files the patch touched.** The commit stages an explicit path list
  captured from the patch transaction — never ``git add -A``, which would sweep
  up whatever else happened to be in the runner's working tree.

Git and ``gh`` are reached through an injected runner, so the whole stage is
testable without a repository or a network.
"""

from __future__ import annotations

import logging
import re
import subprocess  # nosec B404 — fixed argv, never a shell string
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

CommandRunner = Callable[[Sequence[str], Path], tuple[int, str]]

DEFAULT_BRANCH_PREFIX = "selfheal/"
PROTECTED_BRANCHES = frozenset({"main", "master", "develop", "release", "HEAD"})
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MAX_SLUG_LEN = 48
COMMAND_TIMEOUT = 120.0


class PublishError(RuntimeError):
    """Raised when a fix cannot be committed, pushed, or proposed."""


@dataclass(frozen=True)
class PublishResult:
    """What the publish stage produced."""

    branch: str
    pushed: bool
    pull_request_url: str = ""


def default_runner(command: Sequence[str], cwd: Path) -> tuple[int, str]:
    """Run a git/gh command with no shell, returning ``(returncode, output)``."""
    try:
        completed = subprocess.run(  # nosec B603 — argv list, no shell
            list(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, f"command not found: {exc}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {COMMAND_TIMEOUT:.0f}s"
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def slugify(text: str) -> str:
    """Reduce a summary line to a branch-safe slug."""
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:_MAX_SLUG_LEN].strip("-") or "ci-fix"


def branch_name(summary: str, run_id: str = "", prefix: str = DEFAULT_BRANCH_PREFIX) -> str:
    """Build the fix branch name. Includes the run id so re-runs do not collide."""
    suffix = f"-{slugify(run_id)}" if run_id else ""
    return f"{prefix}{slugify(summary)}{suffix}"


def validate_branch(name: str, prefix: str = DEFAULT_BRANCH_PREFIX) -> None:
    """Refuse any branch that is protected or outside the agent's namespace."""
    if not name.startswith(prefix):
        raise PublishError(f"refusing to use branch {name!r}: must start with {prefix!r}")
    bare = name[len(prefix) :]
    if not bare or bare in PROTECTED_BRANCHES or name in PROTECTED_BRANCHES:
        raise PublishError(f"refusing to use protected branch {name!r}")


def _run(runner: CommandRunner, command: Sequence[str], repo_root: Path, what: str) -> str:
    returncode, output = runner(command, repo_root)
    if returncode != 0:
        raise PublishError(f"{what} failed (exit {returncode}): {output.strip()}")
    return output


def commit_fix(
    repo_root: Path,
    branch: str,
    paths: Sequence[str],
    message: str,
    *,
    runner: CommandRunner,
    prefix: str = DEFAULT_BRANCH_PREFIX,
) -> None:
    """Create ``branch`` and commit exactly ``paths`` onto it."""
    validate_branch(branch, prefix)
    if not paths:
        raise PublishError("refusing to commit: no files were changed")

    _run(runner, ("git", "checkout", "-b", branch), repo_root, "git checkout -b")
    _run(runner, ("git", "add", "--", *paths), repo_root, "git add")
    _run(runner, ("git", "commit", "-m", message), repo_root, "git commit")


def push_branch(
    repo_root: Path,
    branch: str,
    *,
    runner: CommandRunner,
    prefix: str = DEFAULT_BRANCH_PREFIX,
) -> None:
    """Push the fix branch to ``origin``, setting upstream."""
    validate_branch(branch, prefix)
    _run(runner, ("git", "push", "-u", "origin", branch), repo_root, "git push")


def open_pull_request(
    repo_root: Path,
    branch: str,
    title: str,
    body_file: Path,
    *,
    base: str = "main",
    runner: CommandRunner,
    prefix: str = DEFAULT_BRANCH_PREFIX,
) -> str:
    """Open the PR via the ``gh`` CLI, returning its URL.

    The body is passed as a file, never as an argument: a walkthrough contains
    newlines, backticks and diff text, none of which survive an argv round-trip
    intact, and a body built from log content should not be shell-adjacent.
    """
    validate_branch(branch, prefix)
    output = _run(
        runner,
        (
            "gh",
            "pr",
            "create",
            "--base",
            base,
            "--head",
            branch,
            "--title",
            title,
            "--body-file",
            str(body_file),
        ),
        repo_root,
        "gh pr create",
    )
    for token in output.split():
        if token.startswith("https://"):
            return token
    return ""


def publish_fix(
    repo_root: Path,
    *,
    branch: str,
    paths: Sequence[str],
    commit_message: str,
    pr_title: str,
    pr_body: str,
    base: str = "main",
    open_pr: bool = True,
    runner: CommandRunner | None = None,
    prefix: str = DEFAULT_BRANCH_PREFIX,
) -> PublishResult:
    """Commit, push, and (optionally) open the PR for a verified fix."""
    execute = runner or default_runner
    commit_fix(repo_root, branch, paths, commit_message, runner=execute, prefix=prefix)
    push_branch(repo_root, branch, runner=execute, prefix=prefix)

    if not open_pr:
        return PublishResult(branch=branch, pushed=True)

    body_file = repo_root / ".selfheal-pr-body.md"
    try:
        body_file.write_text(pr_body, encoding="utf-8")
        url = open_pull_request(
            repo_root, branch, pr_title, body_file, base=base, runner=execute, prefix=prefix
        )
    finally:
        body_file.unlink(missing_ok=True)
    return PublishResult(branch=branch, pushed=True, pull_request_url=url)
