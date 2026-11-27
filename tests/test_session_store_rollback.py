import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

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
    store.create_checkpoint(
        snap_id, memory_store=mem, session_data={"foo": "bar"}, metadata={"meta": 123}
    )
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
