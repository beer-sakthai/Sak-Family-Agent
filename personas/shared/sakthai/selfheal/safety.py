"""Safety gate — the check that stands between a model's patch and the repository.

Everything upstream of this module is advisory: the diagnosis agent proposes, and
a model can be wrong, confused, or steered by text it read in a CI log. This
module decides, and it decides deterministically — no model call, no network, no
judgement calls that vary between runs.

Three classes of rule, each closing a distinct failure mode:

* **Scope** — an edit must land on an existing file inside the repository, and
  must not touch anything on the protected list (CI definitions, dependency
  pins, the security subsystem, or this pipeline itself).
* **Shape** — an edit must be a small, unambiguous, exactly-once replacement.
  A patch that rewrites half a file is not a CI fix.
* **Content** — the replacement must not add code-execution primitives, silence
  a checker instead of satisfying it, neuter a test, or introduce a secret.

A violation is a hard stop. There is no confidence score high enough to override
one, because the whole point is that the model's confidence is not evidence.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from fnmatch import fnmatch
from pathlib import Path

from ..agent.guardrails import _is_sensitive_path
from ..config import _SECRET_RE
from .models import ProposedEdit

# Paths the agent may never rewrite. Anything that defines how the repository is
# built, gated, or defended is off-limits: a self-healing agent that can edit its
# own CI, its own guardrails, or its own safety gate is not gated at all.
PROTECTED_GLOBS: tuple[str, ...] = (
    ".github/*",
    ".github/**",
    ".githooks/*",
    ".githooks/**",
    ".gitleaks.toml",
    ".gitignore",
    ".gitattributes",
    "pyproject.toml",
    "uv.lock",
    "Makefile",
    "Dockerfile*",
    "*/Dockerfile*",
    "infra/**",
    "security/**",
    "bin/**",
    "scripts/**",
    "**/.env*",
    # The security subsystem and its regression tests.
    "**/guardrails.py",
    "**/guardrails_hardened.py",
    "**/security_hardening.py",
    "**/auth.py",
    "**/giturl.py",
    "**/sandbox.py",
    "tests/test_guardrails*.py",
    "tests/test_sentinel*.py",
    "tests/test_security*.py",
    "tests/test_web_auth.py",
    "tests/test_giturl.py",
    "tests/test_persona_guardrails_parity.py",
    # The pipeline may not heal itself.
    "**/selfheal/*",
    "tests/test_selfheal*.py",
)

# Shape limits. A genuine CI fix is small; anything larger is a refactor a human
# should be reviewing from scratch, not approving as an auto-patch.
MAX_EDITS = 5
MAX_NEW_LINES = 60
MAX_REMOVED_LINES = 40

# Content the replacement may not introduce, and why it is refused.
_FORBIDDEN_CONTENT: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\beval\s*\("), "adds eval()"),
    (re.compile(r"\bexec\s*\("), "adds exec()"),
    (re.compile(r"\b__import__\s*\("), "adds __import__()"),
    (re.compile(r"\bos\.system\s*\("), "adds os.system()"),
    (re.compile(r"\bos\.pope\w*\s*\("), "adds os.popen()"),
    (re.compile(r"\bshell\s*=\s*True\b"), "adds a shell=True subprocess call"),
    (re.compile(r"\bpickle\.loads?\s*\("), "adds pickle deserialisation"),
    (re.compile(r"\byaml\.load\s*\("), "adds unsafe yaml.load()"),
    (re.compile(r"\bverify\s*=\s*False\b"), "disables TLS verification"),
    # Suppressing a checker is not fixing what it found.
    (re.compile(r"#\s*nosec\b"), "suppresses bandit with # nosec"),
    (re.compile(r"#\s*type:\s*ignore\b"), "suppresses mypy with # type: ignore"),
    (re.compile(r"#\s*noqa\b"), "suppresses ruff with # noqa"),
    (re.compile(r"#\s*pragma:\s*no cover\b"), "excludes code from coverage"),
    # Neutering a test is not fixing it.
    (re.compile(r"@pytest\.mark\.(?:skip|xfail)"), "skips or xfails a test"),
    (re.compile(r"\bpytest\.skip\s*\("), "skips a test at runtime"),
)


def _relative_path(edit_path: str, repo_root: Path) -> str | None:
    """The repo-relative posix path for an edit, or ``None`` if it escapes the root."""
    root = repo_root.resolve()
    candidate = Path(edit_path)
    absolute = candidate if candidate.is_absolute() else root / candidate
    try:
        resolved = absolute.resolve()
        return resolved.relative_to(root).as_posix()
    except (OSError, ValueError):
        return None


def is_protected(relative_path: str) -> bool:
    """True when a repo-relative path is on the never-auto-edit list."""
    return any(fnmatch(relative_path, pattern) for pattern in PROTECTED_GLOBS)


def _check_scope(edit: ProposedEdit, repo_root: Path, label: str) -> list[str]:
    relative = _relative_path(edit.path, repo_root)
    if relative is None:
        return [f"{label}: path {edit.path!r} resolves outside the repository"]

    violations: list[str] = []
    if is_protected(relative):
        violations.append(f"{label}: {relative} is a protected path and may not be auto-edited")
    if _is_sensitive_path(relative):
        violations.append(f"{label}: {relative} is a sensitive path")
    if not (repo_root.resolve() / relative).is_file():
        violations.append(
            f"{label}: {relative} does not exist (the agent may only edit, not create)"
        )
    return violations


def _check_shape(edit: ProposedEdit, repo_root: Path, label: str) -> list[str]:
    violations: list[str] = []
    if not edit.old:
        violations.append(f"{label}: empty search text — an edit must anchor to existing code")
    if edit.old == edit.new:
        violations.append(f"{label}: replacement is identical to the original")

    added = edit.new.count("\n") + 1 if edit.new else 0
    removed = edit.old.count("\n") + 1 if edit.old else 0
    if added > MAX_NEW_LINES:
        violations.append(f"{label}: replacement is {added} lines (limit {MAX_NEW_LINES})")
    if removed > MAX_REMOVED_LINES:
        violations.append(f"{label}: replaces {removed} lines (limit {MAX_REMOVED_LINES})")

    target = _relative_path(edit.path, repo_root)
    if target is None or not edit.old:
        return violations
    file_path = repo_root.resolve() / target
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations
    occurrences = content.count(edit.old)
    if occurrences == 0:
        violations.append(f"{label}: search text was not found in {target}")
    elif occurrences > 1:
        violations.append(
            f"{label}: search text appears {occurrences} times in {target} — ambiguous"
        )
    return violations


def _check_content(edit: ProposedEdit, label: str) -> list[str]:
    violations: list[str] = []
    # Only flag a construct the edit *introduces*: code that was already there
    # and is merely carried through the replacement is not this agent's doing.
    for pattern, reason in _FORBIDDEN_CONTENT:
        if pattern.search(edit.new) and not pattern.search(edit.old):
            violations.append(f"{label}: {reason}")
    if _SECRET_RE.search(edit.new):
        violations.append(f"{label}: replacement contains what looks like a credential")
    return violations


def evaluate_edits(edits: Sequence[ProposedEdit], repo_root: Path) -> tuple[str, ...]:
    """Return every reason these edits must not be applied. Empty means safe.

    The whole set is evaluated rather than short-circuiting on the first problem,
    so an aborted run reports all of what was wrong in one pass.
    """
    if not edits:
        return ("no edits were proposed",)

    violations: list[str] = []
    if len(edits) > MAX_EDITS:
        violations.append(f"{len(edits)} edits proposed (limit {MAX_EDITS})")

    for index, edit in enumerate(edits[:MAX_EDITS], start=1):
        label = f"edit {index} ({edit.path})"
        violations.extend(_check_scope(edit, repo_root, label))
        violations.extend(_check_shape(edit, repo_root, label))
        violations.extend(_check_content(edit, label))
    return tuple(violations)


def describe_violations(violations: Iterable[str]) -> str:
    """Render violations as a markdown bullet list for reports and CLI output."""
    listed = list(violations)
    if not listed:
        return "_none_"
    return "\n".join(f"- {violation}" for violation in listed)
