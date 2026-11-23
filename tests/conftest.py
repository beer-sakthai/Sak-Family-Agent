"""Shared fixtures: an isolated memory store and a sandboxed SAKTHAI_HOME."""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from sakthai.memory.store import MemoryStore

# Append personas/sakthai to sys.path so subpackages like evolution resolve
# without shadowing installed third-party site-packages (e.g. python-telegram-bot).
_sakthai_pkg_dir = str(Path(__file__).resolve().parent.parent / "personas" / "sakthai")
if _sakthai_pkg_dir not in sys.path:
    sys.path.append(_sakthai_pkg_dir)

# Ensure loopback addresses bypass any ambient HTTP/HTTPS proxy during test runs.
for _k in ("NO_PROXY", "no_proxy"):
    _cur = os.environ.get(_k, "")
    _hosts = [h.strip() for h in _cur.split(",") if h.strip() and h.strip() != "[::1]"]
    for _lh in ("127.0.0.1", "localhost"):
        if _lh not in _hosts:
            _hosts.append(_lh)
    os.environ[_k] = ",".join(_hosts)

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

        from sakthai.agent.quota import reset_quota_sentinel

        reset_quota_sentinel()
        try:
            yield home
        finally:
            reset_quota_sentinel()


@pytest.fixture(autouse=True)
def _isolate_mcp_config(_isolate_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `SAKTHAI_MCP_CONFIG` at an empty manifest for every test.

    `_isolate_home` sandboxes the first three tiers of
    `mcp/servers.load_server_specs()` — the two extension directories and
    `~/.sakthai/mcp.json` — because all three hang off `SAKTHAI_HOME`. The
    fourth and highest tier does not: `SAKTHAI_MCP_CONFIG` is an absolute path,
    and `cli/agent.py:_tool_context` sets it to
    `config.persona_mcp_config_path(persona)` whenever `--persona` is passed and
    the variable is not already set. That resolves to the repository's own
    `personas/<persona>/config/mcp.json`, so a test invoking `run --persona X`
    without `--no-mcp` really starts that persona's servers.

    That happened. Finding 1 of docs/test-coverage-audit-2026-09-01.md caught
    five `node` processes fetching from `registry.npmjs.org` inside the
    `test (3.11)` job, then reaching `huggingface.co` and a FLUX.1-schnell
    Space — four MCP servers coming up, in CI, on every push, for a test whose
    assertions never touched MCP. `connect_servers` fails soft, so the test
    passed identically with the registry unreachable: the egress bought no
    signal at all. The audit asked for exactly this fixture so that "real MCP
    server" is an explicit choice rather than the default.

    An empty `{"mcpServers": {}}` is deliberately not the same as unsetting the
    variable. `load_server_specs` merges tiers into one dict by server name, so
    an empty highest tier contributes nothing and *shadows nothing* — the many
    tests that configure servers through the sandboxed `~/.sakthai/mcp.json`
    keep working unchanged. All it removes is the persona-manifest escape hatch.

    Opt out explicitly when a test needs that hatch, the same way
    `test_memory_merged.py` opts out of `SAKTHAI_HOME`:

        monkeypatch.delenv("SAKTHAI_MCP_CONFIG", raising=False)

    `monkeypatch` is function-scoped and later calls win, so a test that sets
    the variable to a manifest of its own needs no opt-out.
    """
    empty = _isolate_home / "empty-mcp.json"
    empty.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(empty))
    return empty


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
