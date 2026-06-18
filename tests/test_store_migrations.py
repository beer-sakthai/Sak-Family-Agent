"""Correctness tests for MemoryStore schema migrations (_migrate_schema).

These build legacy databases by hand (raw sqlite3) and assert that opening them
through MemoryStore upgrades the schema additively while preserving existing
rows. No network, no GCP.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pytest

from sakthai.memory.store import MemoryStore

# A pre-schema_version "facts" table: the v1 shape, before the tags column.
_LEGACY_FACTS = (
    "CREATE TABLE facts (id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "kind TEXT NOT NULL DEFAULT 'note', key TEXT, value TEXT NOT NULL, "
    "source_session TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)"
)


def _schema_version(path: Path) -> int:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return int(row[0])
    finally:
        conn.close()


def _columns(path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def test_fresh_db_migrates_to_latest(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    with MemoryStore(db):
        pass
    assert _schema_version(db) == 3
    assert "tags" in _columns(db, "facts")
    assert "confidence" in _columns(db, "observations")


def test_reopen_is_idempotent_and_preserves_data(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    with MemoryStore(db) as s:
        s.add_fact("keep me")
    # Second open must not re-run migrations or drop data.
    with MemoryStore(db) as s:
        values = [f.value for f in s.list_facts()]
    assert _schema_version(db) == 3
    assert "keep me" in values


def test_legacy_facts_only_db_is_upgraded(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    conn = sqlite3.connect(db)
    conn.execute(_LEGACY_FACTS)
    conn.execute(
        "INSERT INTO facts (kind, value, created_at, updated_at) "
        "VALUES ('note', 'legacy fact', 1, 1)"
    )
    conn.commit()
    conn.close()

    with MemoryStore(db) as s:
        facts = s.list_facts()
        # The added tags column decodes to [] for the pre-existing row.
        assert any(f.value == "legacy fact" and f.tags == [] for f in facts)
        # The observations table now exists and is usable.
        s.add_observation("derived")
        assert any(o.summary == "derived" for o in s.top_observations())

    assert _schema_version(db) == 3
    assert "tags" in _columns(db, "facts")
    assert "confidence" in _columns(db, "observations")


def test_legacy_observations_without_confidence_gets_backfilled(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    conn = sqlite3.connect(db)
    conn.execute(_LEGACY_FACTS)
    # An observations table missing the confidence column.
    conn.execute(
        "CREATE TABLE observations (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "summary TEXT NOT NULL, evidence_session_id TEXT, "
        "weight REAL NOT NULL DEFAULT 1.0, created_at INTEGER NOT NULL)"
    )
    conn.execute(
        "INSERT INTO observations (summary, weight, created_at) VALUES ('old obs', 1.0, 1)"
    )
    conn.commit()
    conn.close()

    with MemoryStore(db) as s:
        match = [o for o in s.top_observations() if o.summary == "old obs"]
        # Row preserved; confidence backfilled to the column default.
        assert match and match[0].confidence == 0.5

    assert "confidence" in _columns(db, "observations")


def test_wal_failure_tolerated_store_remains_functional(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """MemoryStore opens and is fully functional when WAL mode is rejected.

    On read-only filesystems or network mounts ``PRAGMA journal_mode=WAL``
    raises OperationalError. The store absorbs it, logs a debug message, and
    falls back to the default journal — this test pins that contract.
    """
    import sakthai.memory.store as _store_mod

    real_sqlite3_module = _store_mod.sqlite3

    class _WalBlockedConnection:
        """Proxy that forwards everything except the WAL pragma."""

        def __init__(self, conn: sqlite3.Connection) -> None:
            self._real = conn

        def __getattr__(self, name: str):
            return getattr(self._real, name)

        @property
        def row_factory(self):
            return self._real.row_factory

        @row_factory.setter
        def row_factory(self, value) -> None:
            self._real.row_factory = value

        def execute(self, sql: str, *args):
            if "journal_mode" in sql.lower():
                raise sqlite3.OperationalError("test: read-only filesystem")
            return self._real.execute(sql, *args)

    class _FakeSqlite3Module:
        OperationalError = sqlite3.OperationalError
        Row = sqlite3.Row

        @staticmethod
        def connect(database, **kw):
            return _WalBlockedConnection(real_sqlite3_module.connect(database, **kw))

        def __getattr__(self, name: str):
            return getattr(real_sqlite3_module, name)

    monkeypatch.setattr(_store_mod, "sqlite3", _FakeSqlite3Module())

    db = tmp_path / "wal_fallback.db"
    with caplog.at_level(logging.DEBUG, logger="sakthai.memory.store"):
        with MemoryStore(db) as s:
            fid = s.add_fact("WAL fallback works")
            assert s.list_facts()[0].value == "WAL fallback works"
            assert s.forget_fact(fid) is True
            assert s.list_facts() == []

    assert any("WAL unavailable" in r.message for r in caplog.records), (
        "expected a debug log saying WAL is unavailable"
    )
