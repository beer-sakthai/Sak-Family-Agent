#!/usr/bin/env python3
"""Fuzz :func:`sakthai.giturl.validate_git_url`.

The function guards every user-supplied URL that reaches a ``git`` subprocess
(memory sync remotes, extension clone URLs). Its contract is narrow enough to
state as an invariant: it either raises ``ValueError``, or returns a string
that cannot smuggle a git option, cannot select a remote-helper transport, and
carries an allowed scheme. Anything else — a different exception type, or an
accepted value that violates one of those three — is a bypass.

Run with Atheris (see fuzz/README.md); the invariant itself is exercised by
tests/test_fuzz_harnesses.py without it.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The package lives under personas/sakthai/, and a fuzzing environment is not
# necessarily the editable install (see CLAUDE.md: scripts must fix sys.path).
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

try:  # pragma: no cover - exercised only in a fuzzing environment
    import atheris
except ImportError:  # pragma: no cover - the normal test environment
    atheris = None  # type: ignore[assignment]

from sakthai.giturl import (  # noqa: E402
    _ALLOWED_SCHEMES,
    _HELPER_TRANSPORT_RE,
    validate_git_url,
)


def exercise(data: bytes) -> None:
    """Assert the accept/reject contract for one candidate URL."""
    url = data.decode("utf-8", errors="surrogateescape")

    try:
        accepted = validate_git_url(url)
    except ValueError:
        # Rejection is always a valid outcome.
        return

    # Accepted: the three properties the function exists to guarantee.
    assert not accepted.startswith("-"), f"option smuggling accepted: {accepted!r}"
    assert not _HELPER_TRANSPORT_RE.match(accepted), (
        f"remote-helper transport accepted: {accepted!r}"
    )
    if "://" in accepted:
        scheme = accepted.split("://", 1)[0].lower()
        assert scheme in _ALLOWED_SCHEMES, f"disallowed scheme {scheme!r} accepted: {accepted!r}"

    # An accepted value is passed to git as-is, so it must not have kept
    # leading/trailing whitespace that could change how git parses it.
    assert accepted == accepted.strip(), f"unstripped value accepted: {accepted!r}"


def _test_one_input(data: bytes) -> None:  # pragma: no cover - Atheris entry point
    exercise(data)


def main() -> None:  # pragma: no cover - Atheris entry point
    if atheris is None:
        raise SystemExit("atheris is not installed; see fuzz/README.md")
    # Without this the campaign has no coverage feedback: libFuzzer reports
    # "no interesting inputs were found" and the corpus never grows past the
    # first input, degrading the fuzzer into a random input generator.
    # `instrument_all` covers the already-imported sakthai modules, which is
    # what lets the imports above stay plain enough to run without Atheris.
    atheris.instrument_all()
    atheris.Setup(sys.argv, _test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":  # pragma: no cover
    main()
