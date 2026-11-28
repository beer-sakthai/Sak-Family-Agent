"""Tests for session checkpoint stores (file-backed and Firestore-backed)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from sakthai.memory.session_store import FileSessionStore, FirestoreSessionStore
from sakthai.memory.store import MemoryStore


def _values(store: MemoryStore) -> list[str]:
    return sorted(f.value for f in store.list_facts())


def test_file_store_round_trip_reverts_memory(tmp_path: Path) -> None:
    store = MemoryStore(":memory:")
    store.add_fact("before", kind="note")
    sessions = FileSessionStore(tmp_path / "cp")

    sid = sessions.create_checkpoint(
        "snap-1", memory_store=store, session_data={"turn": 3}, metadata={"by": "test"}
    )
    assert sid == "snap-1"
    snap = sessions.get_checkpoint("snap-1")
    assert snap is not None
    assert snap.session_data == {"turn": 3}
    assert snap.metadata == {"by": "test"}

    store.add_fact("after", kind="note")
    assert sessions.revert_checkpoint("snap-1", memory_store=store) is True
    assert _values(store) == ["before"]


def test_file_store_defaults_to_sakthai_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sakthai.memory.session_store.sakthai_home", lambda: tmp_path)
    sessions = FileSessionStore()
    assert sessions.checkpoints_dir == tmp_path / "checkpoints"
    assert sessions.checkpoints_dir.is_dir()


def test_file_store_sanitizes_snapshot_id(tmp_path: Path) -> None:
    sessions = FileSessionStore(tmp_path)
    sessions.create_checkpoint("../escape/id")
    assert list(tmp_path.glob("*.json")) == [tmp_path / "___escape_id.json"]
    assert sessions.list_checkpoints() == ["___escape_id"]


def test_file_store_missing_and_corrupt_checkpoints(tmp_path: Path) -> None:
    sessions = FileSessionStore(tmp_path)
    assert sessions.get_checkpoint("nope") is None
    assert sessions.revert_checkpoint("nope") is False

    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    assert sessions.get_checkpoint("bad") is None


def test_file_store_revert_without_memory_snapshot_is_noop(tmp_path: Path) -> None:
    sessions = FileSessionStore(tmp_path)
    sessions.create_checkpoint("empty")
    store = MemoryStore(":memory:")
    store.add_fact("kept", kind="note")
    assert sessions.revert_checkpoint("empty", memory_store=store) is True
    assert _values(store) == ["kept"]


class _Doc:
    def __init__(self, doc_id: str, data: dict[str, Any] | None) -> None:
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return self._data


class _DocRef:
    def __init__(self, docs: dict[str, dict[str, Any]], doc_id: str) -> None:
        self._docs = docs
        self._id = doc_id

    def set(self, data: dict[str, Any]) -> None:
        self._docs[self._id] = data

    def get(self) -> _Doc:
        return _Doc(self._id, self._docs.get(self._id))


class _Collection:
    def __init__(self) -> None:
        self.docs: dict[str, dict[str, Any]] = {}

    def document(self, doc_id: str) -> _DocRef:
        return _DocRef(self.docs, doc_id)

    def stream(self) -> list[_Doc]:
        return [_Doc(k, v) for k, v in self.docs.items()]


class _Client:
    def __init__(self) -> None:
        self.collections: dict[str, _Collection] = {}

    def collection(self, name: str) -> _Collection:
        return self.collections.setdefault(name, _Collection())


def test_firestore_store_with_client_round_trip() -> None:
    client = _Client()
    sessions = FirestoreSessionStore(collection_name="cps", client=client)
    store = MemoryStore(":memory:")
    store.add_fact("before", kind="note")

    sessions.create_checkpoint("s1", memory_store=store, session_data={"a": 1})
    assert "s1" in client.collections["cps"].docs
    assert sessions.list_checkpoints() == ["s1"]
    assert sessions.get_checkpoint("missing") is None

    store.add_fact("after", kind="note")
    assert sessions.revert_checkpoint("s1", memory_store=store) is True
    assert _values(store) == ["before"]
    assert sessions.revert_checkpoint("missing") is False


def test_firestore_store_falls_back_to_memory_without_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "google.cloud", None)
    sessions = FirestoreSessionStore()

    sessions.create_checkpoint("local", session_data={"x": 1})
    snap = sessions.get_checkpoint("local")
    assert snap is not None
    assert snap.session_data == {"x": 1}
    assert sessions.list_checkpoints() == ["local"]
    assert sessions.get_checkpoint("absent") is None
