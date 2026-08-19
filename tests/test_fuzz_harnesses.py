"""The fuzz harnesses' invariants, run over a seed corpus without Atheris.

Atheris is not installed in CI (it needs a matching clang toolchain), so
without this the harnesses in `fuzz/` would be dead code that rots between
campaigns — the exact failure mode where a fuzz target still compiles but
stopped reaching the code it was named after.

Each harness keeps its invariant in a plain `exercise(data: bytes)` function
that touches nothing from Atheris, so it can be called directly here. These
tests assert that the invariants *hold* over inputs known to be interesting;
finding new inputs is the fuzzer's job, not pytest's.

The seeds are read from `fuzz/corpus/<harness>/`, the same directory passed to
libFuzzer as the seed corpus, so there is one set of interesting inputs rather
than two that drift apart. Seeding matters for more than tidiness: without it
the MCP harness has to rediscover literal method strings like `tools/call` by
mutation, and a 90-second campaign reached 85 edges instead of several hundred.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

FUZZ_DIR = Path(__file__).resolve().parent.parent / "fuzz"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"fuzz_{name}", FUZZ_DIR / f"fuzz_{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The harnesses insert the package path into sys.path at import time; loading
# them once per session keeps that to a single mutation.
@pytest.fixture(scope="module")
def giturl_harness() -> ModuleType:
    return _load("giturl")


@pytest.fixture(scope="module")
def guardrails_harness() -> Iterator[ModuleType]:
    """Load the harness with the shell rule disarmed, and undo it afterwards.

    With `SAKTHAI_SHELL_ALLOW` unset, rule 1 denies every `run_command` before
    the path and destructive-token logic runs, so the seeds would all take the
    same shallow path. It is scoped to this module rather than set in the
    harness: a dozen test files assert `run_command` is refused by default, and
    a process-wide setenv would disarm the very rule they check.
    """
    mp = pytest.MonkeyPatch()
    mp.setenv("SAKTHAI_SHELL_ALLOW", "1")
    try:
        yield _load("guardrails")
    finally:
        mp.undo()


@pytest.fixture(scope="module")
def mcp_harness() -> ModuleType:
    return _load("mcp_server")


# --------------------------------------------------------------------------
# seed corpora
# --------------------------------------------------------------------------

CORPUS_DIR = FUZZ_DIR / "corpus"


def _seeds(harness: str) -> list[bytes]:
    files = sorted((CORPUS_DIR / harness).iterdir())
    assert files, f"no seed corpus for {harness}"
    return [f.read_bytes() for f in files]


def _ids(harness: str) -> list[str]:
    return [f.name for f in sorted((CORPUS_DIR / harness).iterdir())]


# --------------------------------------------------------------------------
# the invariants
# --------------------------------------------------------------------------


@pytest.mark.parametrize("seed", _seeds("giturl"), ids=_ids("giturl"))
def test_giturl_invariant_holds(giturl_harness: ModuleType, seed: bytes) -> None:
    giturl_harness.exercise(seed)


@pytest.mark.parametrize("seed", _seeds("guardrails"), ids=_ids("guardrails"))
def test_guardrails_invariant_holds(guardrails_harness: ModuleType, seed: bytes) -> None:
    guardrails_harness.exercise(seed)


@pytest.mark.parametrize("seed", _seeds("mcp_server"), ids=_ids("mcp_server"))
def test_mcp_invariant_holds(mcp_harness: ModuleType, seed: bytes) -> None:
    mcp_harness.exercise(seed)


# --------------------------------------------------------------------------
# the harnesses themselves
# --------------------------------------------------------------------------


def test_giturl_harness_catches_a_broken_validator(
    giturl_harness: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The invariant must actually fail when the property it guards is broken.

    A harness that passes unconditionally is worse than none: it reports a
    clean campaign over code it never checked.
    """
    monkeypatch.setattr(giturl_harness, "validate_git_url", lambda url: url)
    with pytest.raises(AssertionError, match="remote-helper transport accepted"):
        giturl_harness.exercise(b"ext::sh -c id")


def test_mcp_harness_catches_a_malformed_response(
    mcp_harness: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mcp_harness, "handle_request", lambda *a, **k: {"jsonrpc": "2.0"})
    with pytest.raises(AssertionError, match="exactly one of result/error"):
        mcp_harness.exercise(b"{}")


def test_mcp_harness_exposes_no_side_effecting_tools(mcp_harness: ModuleType) -> None:
    """`tools/call` executes the handler, so the exposed set must stay store-only.

    Adding `read_file`, `run_command` or a Graph/Telegram tool here would let a
    fuzzing campaign touch the filesystem, spawn processes, or send network
    traffic from fuzzer-controlled arguments.
    """
    exposed = {t.name for t in mcp_harness._SAFE_TOOLS}
    assert exposed == {"learn", "recall", "search", "forget"}


def test_importing_a_harness_does_not_touch_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No harness may set an env var at import time.

    An earlier revision of `fuzz_guardrails.py` did `os.environ.setdefault(
    "SAKTHAI_SHELL_ALLOW", "1")` at module scope. Importing it under pytest set
    that for the rest of the session, silently disarming the deny-by-default
    shell rule that `test_guardrails_*.py`, `test_tools.py` and `test_agent_loop.py`
    exist to verify — the tests would still pass, against a policy that was no
    longer the one shipped.
    """
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    for name in ("giturl", "guardrails", "mcp_server"):
        _load(name)
        assert "SAKTHAI_SHELL_ALLOW" not in os.environ, (
            f"fuzz_{name}.py set SAKTHAI_SHELL_ALLOW at import time"
        )


def test_harnesses_declare_the_atheris_import() -> None:
    """Scorecard's Fuzzing check greps `*.py` for the literal `import atheris`.

    It is what closes alert #15463 (`checks/raw/fuzzing.go` matches the string
    against file contents), so a refactor that drops or renames the import
    silently reopens the alert.
    """
    harnesses = sorted(FUZZ_DIR.glob("fuzz_*.py"))
    assert harnesses, "no fuzz harnesses found"
    for path in harnesses:
        assert "import atheris" in path.read_text(), f"{path.name} lost its atheris import"


def test_harnesses_import_without_atheris_installed() -> None:
    """CI has no Atheris; the guarded import is what keeps these testable."""
    assert "atheris" not in sys.modules or sys.modules["atheris"] is not None
    for name in ("giturl", "guardrails", "mcp_server"):
        module = _load(name)
        assert hasattr(module, "exercise")
