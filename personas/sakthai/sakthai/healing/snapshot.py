"""Point-in-time transactional state snapshot and rollback manager for SQLite memory."""

from __future__ import annotations

import contextlib
import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MemorySnapshotManager:
    """Manages memory checkpoints and atomic rollbacks upon workflow task failure."""

    def __init__(self, backup_dir: Path | str | None = None) -> None:
        self.backup_dir = Path(backup_dir) if backup_dir else Path.home() / ".sakthai" / "snapshots"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots: dict[str, dict[str, Any]] = {}

    def create_checkpoint(self, store_or_path: Any, label: str = "task_checkpoint") -> str:
        """Capture the current state of facts and observations or full database file."""
        checkpoint_id = f"ckpt_{label}_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        # If direct path or Path-like
        if isinstance(store_or_path, (str, Path)):
            db_path = Path(store_or_path)
            if db_path.exists():
                snapshot_file = self.backup_dir / f"{checkpoint_id}.db"
                src = sqlite3.connect(db_path)
                dst = sqlite3.connect(snapshot_file)
                try:
                    src.backup(dst)
                finally:
                    dst.close()
                    src.close()
                self._snapshots[checkpoint_id] = {
                    "label": label,
                    "created_at": time.time(),
                    "db_path": str(db_path),
                    "file_backup": str(snapshot_file),
                }
                return checkpoint_id

        # MemoryStore instance
        try:
            facts = [dict(f.__dict__) for f in store_or_path.list_facts(limit=100000)]
            observations = [dict(o.__dict__) for o in store_or_path.top_observations(limit=100000)]
            self._snapshots[checkpoint_id] = {
                "label": label,
                "created_at": time.time(),
                "facts": facts,
                "observations": observations,
                "db_path": str(getattr(store_or_path, "db_path", "")),
            }
            logger.debug("Created memory checkpoint: %s (label=%s)", checkpoint_id, label)
            return checkpoint_id
        except Exception as err:
            logger.error("Failed to create memory checkpoint: %s", err)
            return ""

    def rollback(self, store_or_path: Any, checkpoint_id: str) -> bool:
        """Rollback facts and observations or database file to snapshot state."""
        snapshot = self._snapshots.get(checkpoint_id)
        if not snapshot:
            snapshot_file = self.backup_dir / f"{checkpoint_id}.db"
            if snapshot_file.exists() and isinstance(store_or_path, (str, Path)):
                db_path = Path(store_or_path)
                src = sqlite3.connect(snapshot_file)
                dst = sqlite3.connect(db_path)
                try:
                    src.backup(dst)
                    return True
                except Exception as err:
                    logger.error("Failed file rollback: %s", err)
                    return False
                finally:
                    dst.close()
                    src.close()
            logger.warning("Checkpoint %s not found for rollback", checkpoint_id)
            return False

        # If file backup was used
        if "file_backup" in snapshot and isinstance(store_or_path, (str, Path)):
            db_path = Path(store_or_path)
            src = sqlite3.connect(snapshot["file_backup"])
            dst = sqlite3.connect(db_path)
            try:
                src.backup(dst)
                return True
            except Exception as err:
                logger.error("Failed file backup restore: %s", err)
                return False
            finally:
                dst.close()
                src.close()

        # If MemoryStore in-memory snapshot
        try:
            store = store_or_path
            with store._conn as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM facts")
                conn.execute("DELETE FROM observations")

                for f in snapshot.get("facts", []):
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

                for o in snapshot.get("observations", []):
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
        """Drop checkpoint from memory cache and disk."""
        snapshot = self._snapshots.pop(checkpoint_id, None)
        if snapshot and "file_backup" in snapshot:
            with contextlib.suppress(Exception):
                Path(snapshot["file_backup"]).unlink(missing_ok=True)

    def list_checkpoints(self) -> list[str]:
        return list(self._snapshots.keys()) + [f.stem for f in self.backup_dir.glob("*.db")]

    @property
    def active_checkpoints_count(self) -> int:
        return len(self._snapshots)
