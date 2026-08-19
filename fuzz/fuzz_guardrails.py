#!/usr/bin/env python3
"""Fuzz the guardrail policy's pre-execution decision.

``GuardrailPolicy.check_pre_execution`` is the choke point every tool call
passes through, and it reaches a lot of hand-rolled string and path parsing:
shell tokenisation, ``make`` recipe and ``-C``/``-f`` resolution, separator
normalisation, and case-insensitive matching over sensitive basenames. That is
the kind of code fuzzing is for.

Two failure modes matter, and both are asserted here:

* **Raising.** A guardrail that raises on a malformed argument is not a safe
  default — the exception propagates into the agent loop rather than denying
  the call, so a crafted path becomes a denial-of-service on the loop at best,
  and depends on the caller's error handling at worst.
* **Returning something the caller cannot act on.** ``run_agent`` branches on
  ``result.action`` and substitutes ``result.modified_args``; a result outside
  that contract is a bypass in waiting.

A campaign needs ``SAKTHAI_SHELL_ALLOW`` set: with it unset, rule 1 denies
every ``run_command`` immediately and the path/destructive-token logic below it
is never reached. Nothing is executed either way — ``check_pre_execution`` only
inspects arguments — but the variable is read per call, not at import, so
``main`` sets it rather than module scope. Setting it on import would leak into
any process that merely imports this module, which under pytest is the whole
session: a dozen test files assert `run_command` is refused by default, and
this harness would quietly disarm the rule they are checking.

Run with Atheris (see fuzz/README.md); the invariant itself is exercised by
tests/test_fuzz_harnesses.py without it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

try:  # pragma: no cover - exercised only in a fuzzing environment
    import atheris
except ImportError:  # pragma: no cover - the normal test environment
    atheris = None  # type: ignore[assignment]

from sakthai.agent.guardrails import (  # noqa: E402
    DEFAULT_POLICY,
    GuardrailAction,
    GuardrailResult,
)
from sakthai.agent.tools import BUILTIN_TOOLS  # noqa: E402
from sakthai.memory.store import MemoryStore  # noqa: E402

# One store for the whole campaign: fuzzing is throughput-bound and the
# pre-execution rules only read from it.
_STORE = MemoryStore(":memory:")

# The tools whose arguments are attacker-shaped in practice.
_TOOLS = {t.name: t for t in BUILTIN_TOOLS if t.name in {"run_command", "read_file"}}


def exercise(data: bytes) -> None:
    """Assert the pre-execution contract for one fuzzed argument set."""
    text = data.decode("utf-8", errors="surrogateescape")

    # Split the input so one buffer drives both tools and both argument names.
    head, _, tail = text.partition("\x00")

    candidates = [
        (_TOOLS["run_command"], {"command": head}),
        (_TOOLS["run_command"], {"command": head, "cwd": tail}),
        (_TOOLS["read_file"], {"path": head}),
    ]

    for tool, args in candidates:
        result = DEFAULT_POLICY.check_pre_execution(tool, args, _STORE)

        assert isinstance(result, GuardrailResult), f"not a GuardrailResult: {result!r}"
        assert isinstance(result.action, GuardrailAction), (
            f"action outside the enum: {result.action!r}"
        )
        if result.modified_args is not None:
            assert isinstance(result.modified_args, dict), (
                f"modified_args must be a dict, got {type(result.modified_args)!r}"
            )
        if result.action == GuardrailAction.DENY:
            # The loop surfaces this string to the model; an empty reason
            # leaves the denial unexplained.
            assert result.reason, "DENY carries no reason"


def _test_one_input(data: bytes) -> None:  # pragma: no cover - Atheris entry point
    exercise(data)


def main() -> None:  # pragma: no cover - Atheris entry point
    if atheris is None:
        raise SystemExit("atheris is not installed; see fuzz/README.md")
    # Read per call, so setting it here is enough — and unlike module scope it
    # cannot leak into an unrelated process. See the module docstring.
    os.environ.setdefault("SAKTHAI_SHELL_ALLOW", "1")
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
