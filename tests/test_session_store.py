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
