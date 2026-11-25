"""Session store with checkpoint and snapshot rollback capabilities.

Implements AbstractSessionStore, FileSessionStore, and FirestoreSessionStore
as specified in references/anti-gaming-safeguards.md.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sakthai.config import sakthai_home
from sakthai.memory.store import MemoryStore

logger = logging.getLogger(__name__)


@dataclass
class SessionSnapshot:
    """Checkpoint snapshot holding memory facts, session state, and metadata."""

    snapshot_id: str
    created_at: str
    memory_snapshot: dict[str, Any]
    session_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionSnapshot:
        """Create snapshot from dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            memory_snapshot=data.get("memory_snapshot", {}),
            session_data=data.get("session_data", {}),
            metadata=data.get("metadata", {}),
        )


class AbstractSessionStore(ABC):
    """Abstract interface for session checkpoint persistence and rollback."""

    @abstractmethod
    def create_checkpoint(
        self,
        snapshot_id: str,
        memory_store: MemoryStore | None = None,
        session_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create and persist a snapshot checkpoint."""

    @abstractmethod
    def revert_checkpoint(
        self,
        snapshot_id: str,
        memory_store: MemoryStore | None = None,
    ) -> bool:
        """Revert memory and session state to the specified snapshot checkpoint."""

    @abstractmethod
    def get_checkpoint(self, snapshot_id: str) -> SessionSnapshot | None:
        """Retrieve snapshot details by ID."""

    @abstractmethod
    def list_checkpoints(self) -> list[str]:
        """List all available snapshot IDs ordered chronologically."""


class FileSessionStore(AbstractSessionStore):
    """Local file-backed session store persisting snapshots to disk."""

    def __init__(self, checkpoints_dir: Path | str | None = None) -> None:
        if checkpoints_dir is None:
            self.checkpoints_dir = sakthai_home() / "checkpoints"
        else:
            self.checkpoints_dir = Path(checkpoints_dir)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def _snapshot_path(self, snapshot_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in snapshot_id)
        return self.checkpoints_dir / f"{safe_id}.json"

    def create_checkpoint(
        self,
        snapshot_id: str,
        memory_store: MemoryStore | None = None,
        session_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        mem_snap = memory_store.export_to_dict() if memory_store is not None else {}
        snap = SessionSnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(UTC).isoformat(),
            memory_snapshot=mem_snap,
            session_data=session_data or {},
            metadata=metadata or {},
        )
        p = self._snapshot_path(snapshot_id)
        p.write_text(json.dumps(snap.to_dict(), indent=2), encoding="utf-8")
        logger.info("Persisted session checkpoint '%s' to %s", snapshot_id, p)
        return snapshot_id

    def revert_checkpoint(
        self,
        snapshot_id: str,
        memory_store: MemoryStore | None = None,
    ) -> bool:
        snap = self.get_checkpoint(snapshot_id)
        if snap is None:
            logger.warning("Checkpoint '%s' not found for rollback", snapshot_id)
            return False

        if memory_store is not None and snap.memory_snapshot:
            memory_store.import_from_dict(snap.memory_snapshot, mode="replace")
            logger.info("Reverted MemoryStore to snapshot '%s'", snapshot_id)
        return True

    def get_checkpoint(self, snapshot_id: str) -> SessionSnapshot | None:
        p = self._snapshot_path(snapshot_id)
        if not p.is_file():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return SessionSnapshot.from_dict(data)
        except Exception as exc:
            logger.warning("Failed loading snapshot %s: %s", p, exc)
            return None

    def list_checkpoints(self) -> list[str]:
        paths = sorted(self.checkpoints_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        return [p.stem for p in paths]


class FirestoreSessionStore(AbstractSessionStore):
    """Google Cloud Firestore-backed session store for cloud-native checkpoint persistence."""

    def __init__(
        self,
        collection_name: str = "eval_checkpoints",
        client: Any | None = None,
    ) -> None:
        self.collection_name = collection_name
        self._client = client
        self._in_memory_fallback: dict[str, SessionSnapshot] = {}

    def _get_collection(self) -> Any | None:
        if self._client is not None:
            return self._client.collection(self.collection_name)
        try:
            from google.cloud import firestore

            self._client = firestore.Client()
            return self._client.collection(self.collection_name)
        except Exception:
            return None

    def create_checkpoint(
        self,
        snapshot_id: str,
        memory_store: MemoryStore | None = None,
        session_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        mem_snap = memory_store.export_to_dict() if memory_store is not None else {}
        snap = SessionSnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(UTC).isoformat(),
            memory_snapshot=mem_snap,
            session_data=session_data or {},
            metadata=metadata or {},
        )
        col = self._get_collection()
        if col is not None:
            col.document(snapshot_id).set(snap.to_dict())
        else:
            self._in_memory_fallback[snapshot_id] = snap
        return snapshot_id

    def revert_checkpoint(
        self,
        snapshot_id: str,
        memory_store: MemoryStore | None = None,
    ) -> bool:
        snap = self.get_checkpoint(snapshot_id)
        if snap is None:
            return False
        if memory_store is not None and snap.memory_snapshot:
            memory_store.import_from_dict(snap.memory_snapshot, mode="replace")
        return True

    def get_checkpoint(self, snapshot_id: str) -> SessionSnapshot | None:
        col = self._get_collection()
        if col is not None:
            doc = col.document(snapshot_id).get()
            if doc.exists:
                return SessionSnapshot.from_dict(doc.to_dict())
            return None
        return self._in_memory_fallback.get(snapshot_id)

    def list_checkpoints(self) -> list[str]:
        col = self._get_collection()
        if col is not None:
            return [doc.id for doc in col.stream()]
        return list(self._in_memory_fallback.keys())
