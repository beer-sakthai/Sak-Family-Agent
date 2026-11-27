import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
import sys

from sakthai.memory.session_store import FileSessionStore, FirestoreSessionStore, SessionSnapshot
from sakthai.memory.store import MemoryStore

@pytest.fixture
def temp_dir():
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path)

def test_file_session_store_checkpoint_and_revert(temp_dir):
    # Setup a memory store with some data
    mem = MemoryStore()
    mem.add_fact(json.dumps({"value": 1}), key="key1")
    # Create FileSessionStore with custom directory
    store = FileSessionStore(checkpoints_dir=temp_dir)
    snap_id = "snap1"
    # Create checkpoint
    store.create_checkpoint(snap_id, memory_store=mem, session_data={"foo": "bar"}, metadata={"meta": 123})
    # Verify file exists
    checkpoint_path = temp_dir / f"{snap_id}.json"
    assert checkpoint_path.is_file()
    # Load snapshot directly and verify contents
    data = json.loads(checkpoint_path.read_text())
    assert data["snapshot_id"] == snap_id
    assert data["memory_snapshot"] == mem.export_to_dict()
    assert data["session_data"] == {"foo": "bar"}
    assert data["metadata"] == {"meta": 123}
    # Modify memory store and revert
    mem.add_fact(json.dumps({"value": 2}), key="key2")
    assert any(f["key"] == "key2" for f in mem.export_to_dict()["facts"])
    success = store.revert_checkpoint(snap_id, memory_store=mem)
    assert success
    # After revert, key2 should be gone and original data restored
    exported = mem.export_to_dict()
    assert "key2" not in exported
    assert exported == data["memory_snapshot"]
    # List checkpoints returns our snapshot id
    assert store.list_checkpoints() == [snap_id]
    # Retrieve checkpoint returns a SessionSnapshot with matching id
    snapshot = store.get_checkpoint(snap_id)
    assert isinstance(snapshot, SessionSnapshot)
    assert snapshot.snapshot_id == snap_id

def test_firestore_session_store_fallback(monkeypatch):
    # Force FirestoreSessionStore to use in-memory fallback by not providing client and mocking import failure
    # Ensure google.cloud import fails
    monkeypatch.setitem(sys.modules, "google.cloud", None)
    store = FirestoreSessionStore()
    snap_id = "fallback1"
    mem = MemoryStore()
    mem.add_fact(json.dumps({"x": 1}), key="a")
    store.create_checkpoint(snap_id, memory_store=mem, session_data={"s": 1}, metadata={})
    # Should be stored in fallback dict
    assert snap_id in store._in_memory_fallback
    # Retrieve checkpoint
    snapshot = store.get_checkpoint(snap_id)
    assert isinstance(snapshot, SessionSnapshot)
    assert snapshot.snapshot_id == snap_id
    # List checkpoints should include our id
    assert snap_id in store.list_checkpoints()
    # Revert should restore memory store correctly
    mem.add_fact(json.dumps({"y": 2}), key="b")
    assert any(f["key"] == "b" for f in mem.export_to_dict()["facts"])
    result = store.revert_checkpoint(snap_id, memory_store=mem)
    assert result
    exported = mem.export_to_dict()
    # After revert, only original key "a" should remain
    assert "b" not in exported
    assert any(f["key"] == "a" for f in exported["facts"])
"""Unit tests for FileSessionStore and FirestoreSessionStore."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from sakthai.memory.session_store import FileSessionStore, FirestoreSessionStore
from sakthai.memory.store import MemoryStore


class TestSessionStore(unittest.TestCase):
    def test_file_session_store_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(checkpoints_dir=tmpdir)
            self.assertEqual(store.list_checkpoints(), [])
            self.assertIsNone(store.get_checkpoint("missing"))

            # Create checkpoint without MemoryStore
            sid = store.create_checkpoint("snap-1", session_data={"key": "val"})
            self.assertEqual(sid, "snap-1")
            self.assertEqual(store.list_checkpoints(), ["snap-1"])

            snap = store.get_checkpoint("snap-1")
            self.assertIsNotNone(snap)
            assert snap is not None
            self.assertEqual(snap.session_data["key"], "val")

            # Corrupted checkpoint file handling
            corrupted = Path(tmpdir) / "corrupt.json"
            corrupted.write_text("{bad json", encoding="utf-8")
            self.assertIsNone(store.get_checkpoint("corrupt"))

            # Revert with missing checkpoint
            self.assertFalse(store.revert_checkpoint("missing"))

    def test_file_session_store_default_dir_and_revert(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_db = Path(tmpdir) / "test.db"
            chk_dir = Path(tmpdir) / "checkpoints"
            store = FileSessionStore(checkpoints_dir=chk_dir)

            with MemoryStore(mem_db) as mem:
                mem.add_fact("Initial state", tags=["v1"])
                sid = store.create_checkpoint("v1-snap", memory_store=mem)

                # Mutate mem
                mem.add_fact("Mutated state", tags=["v2"])

                # Revert
                ok = store.revert_checkpoint(sid, memory_store=mem)
                self.assertTrue(ok)
                facts = mem.list_facts()
                self.assertEqual(len(facts), 1)
                self.assertIn("Initial state", facts[0].value)

    def test_firestore_session_store_fallback(self) -> None:
        store = FirestoreSessionStore()
        # Fallback in-memory operations
        sid = store.create_checkpoint("cloud-1", session_data={"step": 1})
        self.assertEqual(sid, "cloud-1")
        self.assertEqual(store.list_checkpoints(), ["cloud-1"])

        snap = store.get_checkpoint("cloud-1")
        self.assertIsNotNone(snap)
        assert snap is not None
        self.assertEqual(snap.session_data["step"], 1)

        self.assertFalse(store.revert_checkpoint("missing"))
        self.assertTrue(store.revert_checkpoint("cloud-1"))

    def test_firestore_session_store_with_mock_client(self) -> None:
        mock_client = MagicMock()
        mock_col = MagicMock()
        mock_client.collection.return_value = mock_col

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "snapshot_id": "mock-1",
            "created_at": "2026-11-26T00:00:00Z",
            "memory_snapshot": {},
            "session_data": {"user": "sakthai"},
            "metadata": {},
        }
        mock_col.document.return_value.get.return_value = mock_doc
        mock_stream_doc = MagicMock()
        mock_stream_doc.id = "mock-1"
        mock_col.stream.return_value = [mock_stream_doc]

        store = FirestoreSessionStore(client=mock_client)
        sid = store.create_checkpoint("mock-1")
        self.assertEqual(sid, "mock-1")

        snap = store.get_checkpoint("mock-1")
        self.assertIsNotNone(snap)
        self.assertEqual(store.list_checkpoints(), ["mock-1"])

        # doc.exists is False
        mock_doc.exists = False
        self.assertIsNone(store.get_checkpoint("nonexistent"))

    def test_session_store_extra_branches(self) -> None:
        from unittest.mock import patch

        # FileSessionStore with default checkpoints_dir (None)
        store = FileSessionStore(checkpoints_dir=None)
        self.assertTrue(store.checkpoints_dir.name == "checkpoints")

        # revert_checkpoint with empty memory_snapshot
        sid = store.create_checkpoint("empty-mem")
        mem_mock = MagicMock()
        self.assertTrue(store.revert_checkpoint(sid, memory_store=mem_mock))
        mem_mock.import_from_dict.assert_not_called()

        # FirestoreSessionStore revert with memory_store
        f_store = FirestoreSessionStore()
        f_store._in_memory_fallback["has-mem"] = MagicMock(memory_snapshot={"facts": []})
        f_mem_mock = MagicMock()
        self.assertTrue(f_store.revert_checkpoint("has-mem", memory_store=f_mem_mock))
        f_mem_mock.import_from_dict.assert_called_once()

        # Firestore lazy client init
        with patch.dict(
            "sys.modules", {"google.cloud": MagicMock(), "google.cloud.firestore": MagicMock()}
        ):
            lazy_store = FirestoreSessionStore()
            self.assertIsNotNone(lazy_store._get_collection())


if __name__ == "__main__":
    unittest.main()
