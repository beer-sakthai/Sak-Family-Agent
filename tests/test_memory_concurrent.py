"""Tests for concurrent MemoryStore access (busy_timeout / locking).

Multiple subprocesses write to the same SQLite file simultaneously.
The configured busy_timeout lets writers queue rather than fail immediately
with "database is locked", so every write must commit successfully.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import threading
from pathlib import Path

from sakthai.memory.store import MemoryStore


def _run_threads(targets: list) -> list[BaseException]:
    """Run each callable in its own thread; return any exceptions they raised.

    Each worker opens its *own* ``MemoryStore`` on the shared file — a single
    sqlite3 connection is not shareable across threads, but separate WAL
    connections to the same DB are exactly the contention we want to test.
    """
    errors: list[BaseException] = []
    lock = threading.Lock()

    def _wrap(fn: object) -> object:
        def runner() -> None:
            try:
                fn()  # type: ignore[operator]
            except BaseException as exc:  # noqa: BLE001 — surfaced to the test
                with lock:
                    errors.append(exc)

        return runner

    threads = [threading.Thread(target=_wrap(t)) for t in targets]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=60)
    return errors


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

    procs = [
        subprocess.Popen([sys.executable, "-c", writer_code]) for _ in range(n_writers)
    ]

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
    assert (
        len(written_values) == 10
    ), f"expected 10 written facts, got {len(written_values)}"


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
    procs = [
        subprocess.Popen([sys.executable, "-c", opener_code]) for _ in range(n_openers)
    ]

    failed = []
    for p in procs:
        ret = p.wait(timeout=60)
        if ret != 0:
            failed.append(ret)

    assert (
        not failed
    ), f"{len(failed)}/{n_openers} opener(s) failed during migration race"

    with MemoryStore(db) as s:
        total = len(s.list_facts(limit=n_openers + 1))
    assert total == n_openers


# -- in-process (thread) contention --------------------------------------


def test_threaded_writers_no_lost_writes(tmp_path: Path) -> None:
    """N threads, each on its own connection, write M facts; all N*M must survive."""
    db = tmp_path / "threads.db"
    with MemoryStore(db):  # create schema once so writers don't race on migration
        pass

    n_writers, per_writer = 5, 20

    def make_writer(tag: int) -> object:
        def write() -> None:
            with MemoryStore(db) as s:
                for i in range(per_writer):
                    s.add_fact(f"w{tag}-fact-{i}", kind="note")

        return write

    errors = _run_threads([make_writer(t) for t in range(n_writers)])
    assert not errors, f"writer threads raised: {errors}"

    with MemoryStore(db) as s:
        total = len(s.list_facts(limit=n_writers * per_writer + 1))
    assert total == n_writers * per_writer


def test_deduplicate_races_with_writers(tmp_path: Path) -> None:
    """Dedup running concurrently with writers must not raise (busy_timeout queues).

    After everyone is done, a final deduplicate must leave no duplicate group
    behind — i.e. concurrent access never corrupted the invariant.
    """
    db = tmp_path / "dedup-race.db"
    with MemoryStore(db) as s:
        for i in range(20):
            # Two facts per key so there is always something to deduplicate.
            s.add_fact("v1", kind="note", key=f"k{i}")
            s.add_fact("v2", kind="note", key=f"k{i}")

    def writer() -> None:
        with MemoryStore(db) as s:
            for i in range(30):
                s.add_fact(f"extra-{i}", kind="extra")

    def deduper() -> None:
        with MemoryStore(db) as s:
            for _ in range(10):
                s.deduplicate_facts()

    errors = _run_threads([writer, deduper, deduper])
    assert not errors, f"dedup/writer threads raised: {errors}"

    with MemoryStore(db) as s:
        s.deduplicate_facts()  # quiesce
        groups: dict[tuple[str, str], int] = {}
        for f in s.list_facts(limit=10_000):
            if f.key is not None:
                groups[(f.kind, f.key)] = groups.get((f.kind, f.key), 0) + 1
    assert all(count == 1 for count in groups.values())


def test_consolidate_is_atomic_under_readers(tmp_path: Path) -> None:
    """Readers concurrent with a consolidation never observe a half-applied write.

    ``consolidate_facts`` deletes the folded facts and inserts the summary in one
    transaction. Each count is therefore all-or-nothing: a reader sees the fact
    table at the full total or empty (never a partial deletion), and the
    observation table at 0 or 1 (never mid-insert). We assert each table
    independently — the two COUNT(*) reads aren't a single snapshot, so the
    *pair* may legitimately straddle the commit.
    """
    db = tmp_path / "consolidate-race.db"
    n_facts = 40
    with MemoryStore(db) as s:
        for i in range(n_facts):
            s.add_fact(f"old-{i}", kind="note")

    observed: list[tuple[int, int]] = []
    obs_lock = threading.Lock()

    def consolidator() -> None:
        with MemoryStore(db) as s:
            s.consolidate_facts(age_seconds=-1)  # folds every fact

    def reader() -> None:
        with MemoryStore(db) as s:
            for _ in range(50):
                st = s.stats()
                snap = (st["facts"]["total"], st["observations"]["total"])
                with obs_lock:
                    observed.append(snap)

    errors = _run_threads([consolidator, reader, reader])
    assert not errors, f"consolidate/reader threads raised: {errors}"

    # No partial deletion and no mid-insert ever surfaced.
    assert all(f in (0, n_facts) for f, _ in observed), observed
    assert all(o in (0, 1) for _, o in observed), observed

    with MemoryStore(db) as s:
        final = s.stats()
    assert final["facts"]["total"] == 0
    assert final["observations"]["total"] == 1
