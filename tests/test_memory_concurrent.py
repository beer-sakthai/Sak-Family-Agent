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


def test_concurrent_readers_do_not_block_writers(tmp_path: Path) -> None:
    """WAL mode: readers should not prevent writers from committing.

    A writer writes 10 facts while 2 readers continuously list facts.
    All writes must complete and every reader must exit zero.
    """
    db = tmp_path / "wal.db"

    # Pre-seed schema and a few initial facts so readers have something to read.
    with MemoryStore(db) as s:
        for i in range(5):
            s.add_fact(f"seed-{i}")

    writer_code = textwrap.dedent(f"""
        from pathlib import Path
        from sakthai.memory.store import MemoryStore
        with MemoryStore(Path({str(db)!r})) as s:
            for i in range(10):
                s.add_fact(f"write-{{i}}")
    """)

    reader_code = textwrap.dedent(f"""
        import time
        from pathlib import Path
        from sakthai.memory.store import MemoryStore
        for _ in range(20):
            with MemoryStore(Path({str(db)!r})) as s:
                _ = s.list_facts(limit=100)
            time.sleep(0.01)
    """)

    writer = subprocess.Popen([sys.executable, "-c", writer_code])
    readers = [subprocess.Popen([sys.executable, "-c", reader_code]) for _ in range(2)]

    assert writer.wait(timeout=30) == 0, "writer exited non-zero"
    for r in readers:
        assert r.wait(timeout=30) == 0, "reader exited non-zero"

    with MemoryStore(db) as s:
        facts = s.list_facts(limit=200)
    written_values = {f.value for f in facts if f.value.startswith("write-")}
    assert len(written_values) == 10, f"expected 10 written facts, got {len(written_values)}"


def test_migration_race_multiple_openers(tmp_path: Path) -> None:
    """Multiple processes opening a brand-new DB simultaneously must not corrupt it.

    BEGIN IMMEDIATE in _migrate_schema() serialises the migration; all
    processes must finish without error and exactly one schema must result.
    """
    db = tmp_path / "race.db"
    # DB does NOT exist yet — all openers will race on migration.

    opener_code = textwrap.dedent(f"""
        from pathlib import Path
        from sakthai.memory.store import MemoryStore
        with MemoryStore(Path({str(db)!r})) as s:
            s.add_fact("opener-fact")
    """)

    n_openers = 6
    procs = [subprocess.Popen([sys.executable, "-c", opener_code]) for _ in range(n_openers)]

    failed = []
    for p in procs:
        ret = p.wait(timeout=60)
        if ret != 0:
            failed.append(ret)

    assert not failed, f"{len(failed)}/{n_openers} opener(s) failed during migration race"

    with MemoryStore(db) as s:
        total = len(s.list_facts(limit=n_openers + 1))
    assert total == n_openers
