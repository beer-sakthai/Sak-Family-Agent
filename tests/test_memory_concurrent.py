"""Tests for concurrent MemoryStore access (busy_timeout / locking).

Multiple subprocesses write to the same SQLite file simultaneously.
The configured busy_timeout lets writers queue rather than fail immediately
with "database is locked", so every write must commit successfully.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from sakthai.memory.store import MemoryStore


def test_concurrent_writers_all_succeed(tmp_path: Path) -> None:
    """Four concurrent subprocesses each write 20 facts; all 80 must survive.

    Pre-creates the schema in the parent process so the writers don't race
    on the migration path — their contention is purely on INSERT + COMMIT.
    """
    db = tmp_path / "concurrent.db"
    n_writers = 4
    facts_per_writer = 20

    # Initialise schema once so writers don't race on migration.
    with MemoryStore(db):
        pass

    writer_code = textwrap.dedent(f"""
        from pathlib import Path
        from sakthai.memory.store import MemoryStore
        with MemoryStore(Path({str(db)!r})) as s:
            for i in range({facts_per_writer}):
                s.add_fact(f"fact-{{i}}")
    """)

    procs = [subprocess.Popen([sys.executable, "-c", writer_code]) for _ in range(n_writers)]

    failed = []
    for p in procs:
        ret = p.wait(timeout=60)
        if ret != 0:
            failed.append(ret)

    assert not failed, f"{len(failed)}/{n_writers} writer(s) exited non-zero: {failed}"

    with MemoryStore(db) as s:
        total = len(s.list_facts(limit=n_writers * facts_per_writer + 1))

    assert total == n_writers * facts_per_writer
