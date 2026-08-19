# tests/test_healing_snapshot.py
import sqlite3

import pytest

from sakthai.healing.snapshot import MemorySnapshotManager


@pytest.fixture
def memory_db(tmp_path):
    db_file = tmp_path / "memory.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE facts (id TEXT PRIMARY KEY, text TEXT);")
    conn.execute("INSERT INTO facts VALUES ('f1', 'Original Fact');")
    conn.commit()
    conn.close()
    return db_file


def test_snapshot_and_rollback(memory_db):
    mgr = MemorySnapshotManager(backup_dir=memory_db.parent / "snapshots")
    cp_id = mgr.create_checkpoint(memory_db, label="pre_cycle")
    assert cp_id != ""

    # Corrupt or mutate facts
    conn = sqlite3.connect(memory_db)
    conn.execute("INSERT INTO facts VALUES ('f2', 'Corrupted Fact');")
    conn.commit()
    conn.close()

    # Verify mutation exists
    conn = sqlite3.connect(memory_db)
    assert len(conn.execute("SELECT * FROM facts").fetchall()) == 2
    conn.close()

    # Rollback
    success = mgr.rollback(memory_db, cp_id)
    assert success is True

    # Verify restored state
    conn = sqlite3.connect(memory_db)
    rows = conn.execute("SELECT * FROM facts").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "f1"
    conn.close()
