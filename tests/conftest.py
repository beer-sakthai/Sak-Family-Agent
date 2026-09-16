"""Shared fixtures: an isolated memory store and a sandboxed SAKTHAI_HOME."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from sakthai.memory.store import MemoryStore

#: The invoking user's real `~/.sakthai`, captured once at import time — before
#: any fixture has had a chance to move `HOME`. `test_home_isolation.py` asserts
#: the suite never creates it.
REAL_SAKTHAI_HOME = Path(os.path.expanduser("~")) / ".sakthai"


@pytest.fixture
def real_sakthai_home() -> Path:
    """The invoking user's `~/.sakthai`, as it was before `HOME` was redirected.

    A fixture rather than an import because `tests/` is not a package, so test
    modules cannot import from `conftest` directly.
    """
    return REAL_SAKTHAI_HOME


@pytest.fixture(autouse=True)
def _isolate_home(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point `HOME` at `tmp_path` for every test in the suite.

    Isolation used to be opt-in, and `SAKTHAI_HOME` was the only knob on offer.
    That knob cannot contain `config.persona_memory_db_path()`, which resolves
    from `Path.home()` *deliberately independent* of `SAKTHAI_HOME` — that
    independence is the function's whole purpose. So a test calling
    `run_persona_task("sakking", ...)` wrote a real shard to
    `~/.sakthai/sakking/memory.db`: the exact path SakKing's deployed process
    uses on the VM, opened with `_migrate_schema()`'s `ALTER TABLE` under
    `BEGIN IMMEDIATE`. Migrations are additive, so nothing was destroyed, but
    the suite was taking a write lock on a production database and nothing
    stopped a future test inserting rows.

    It also caused the ±1-statement coverage drift all four audits recorded and
    none explained: `memory/store.py` forks on whether the DB file already
    exists (create at `0600` vs `chmod`), so a pristine home measured one branch
    and the next run measured the other.

    `HOME` is what makes this airtight; `SAKTHAI_HOME` is set alongside it so a
    test that reads either lands in the same sandbox. A test that genuinely
    needs something else just overrides it — `monkeypatch` is function-scoped
    and later `setenv` calls win, which is why the 22 files that already set
    `SAKTHAI_HOME` themselves keep working unchanged.

    The sandbox is its own temp directory, deliberately **not** a child of
    `tmp_path`: several tests hand `tmp_path` to skill discovery and assert on
    everything found under it, so a home directory nested there would show up as
    a bogus skill folder.

    See finding 1 of docs/test-coverage-audit-2026-08-31.md.
    """
    with tempfile.TemporaryDirectory(prefix="sakthai-test-home-") as raw:
        home = Path(raw)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))  # Path.home() reads this on Windows
        monkeypatch.setenv("SAKTHAI_HOME", str(home / ".sakthai"))
        yield home


@pytest.fixture
def store(tmp_path: Path) -> Iterator[MemoryStore]:
    s = MemoryStore(tmp_path / "memory.db")
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def sakthai_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    return home
