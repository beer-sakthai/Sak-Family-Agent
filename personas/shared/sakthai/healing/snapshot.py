"""Point-in-time transactional state snapshot and rollback manager for SQLite memory."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)


class MemorySnapshotManager:
    """Manages memory checkpoints and atomic rollbacks upon workflow task failure."""

    def __init__(self) -> None:
        self._snapshots: dict[str, dict[str, Any]] = {}

    def create_checkpoint(self, store: MemoryStore, label: str = "task_checkpoint") -> str:
        """Capture the current state of facts and observations in MemoryStore."""
        checkpoint_id = f"ckpt_{uuid.uuid4().hex[:10]}"
        try:
            facts = [dict(f.__dict__) for f in store.list_facts(limit=100000)]
            observations = [dict(o.__dict__) for o in store.top_observations(limit=100000)]
            self._snapshots[checkpoint_id] = {
                "label": label,
                "created_at": time.time(),
                "facts": facts,
                "observations": observations,
                "db_path": str(store.db_path),
            }
            logger.debug("Created memory checkpoint: %s (label=%s)", checkpoint_id, label)
            return checkpoint_id
        except Exception as err:
            logger.error("Failed to create memory checkpoint: %s", err)
            return ""

    def rollback(self, store: MemoryStore, checkpoint_id: str) -> bool:
        """Rollback facts and observations to snapshot state inside an atomic transaction."""
        snapshot = self._snapshots.get(checkpoint_id)
        if not snapshot:
            logger.warning("Checkpoint %s not found for rollback", checkpoint_id)
            return False

        try:
            # Atomic transaction reset
            with store._conn as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM facts")
                conn.execute("DELETE FROM observations")

                for f in snapshot["facts"]:
                    tags_val = (
                        json.dumps(f.get("tags"), ensure_ascii=False)
                        if isinstance(f.get("tags"), list)
                        else f.get("tags")
                    )
                    conn.execute(
                        """
                        INSERT INTO facts (id, kind, key, value, source_session, created_at, updated_at, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f.get("id"),
                            f.get("kind", "note"),
                            f.get("key"),
                            f.get("value", ""),
                            f.get("source_session"),
                            f.get("created_at"),
                            f.get("updated_at"),
                            tags_val,
                        ),
                    )

                for o in snapshot["observations"]:
                    conn.execute(
                        """
                        INSERT INTO observations (id, summary, evidence_session_id, weight, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            o.get("id"),
                            o.get("summary", ""),
                            o.get("evidence_session_id"),
                            o.get("weight", 1.0),
                            o.get("confidence", 0.5),
                            o.get("created_at"),
                        ),
                    )
            logger.info("Successfully rolled back memory store to checkpoint %s", checkpoint_id)
            return True
        except Exception as err:
            logger.error("Failed to rollback memory checkpoint %s: %s", checkpoint_id, err)
            return False

    def release_checkpoint(self, checkpoint_id: str) -> None:
        """Drop checkpoint from memory cache."""
        self._snapshots.pop(checkpoint_id, None)

    @property
    def active_checkpoints_count(self) -> int:
        return len(self._snapshots)
