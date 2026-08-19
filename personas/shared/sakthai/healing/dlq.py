"""Persistent Dead-Letter Queue (DLQ) for failed agent execution tasks."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, overload

from ..config import memory_db_path, redact_secrets
from .models import DLQItem

logger = logging.getLogger(__name__)


@dataclass
class DeadLetterItem:
    item_id: str
    persona: str
    action: str
    payload: dict[str, Any]
    error_type: str
    error_message: str
    stack_trace: str
    retry_count: int
    max_retries: int
    status: str  # "pending", "replayed", "quarantined", "purged", "DEAD", "RESOLVED"
    created_at: int
    updated_at: int
    next_retry_at: int


def _recovery_db_path() -> Path:
    base = memory_db_path().parent
    base.mkdir(parents=True, exist_ok=True)
    return base / "recovery.db"


class DeadLetterQueue:
    """Thread-safe SQLite persistent Dead-Letter Queue with jittered exponential backoff."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else _recovery_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dead_letter_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    persona TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    next_retry_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_dlq_status ON dead_letter_items(status, next_retry_at)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dlq_persona ON dead_letter_items(persona)")

    @overload
    def enqueue(self, persona: DLQItem) -> str: ...

    @overload
    def enqueue(
        self,
        persona: str,
        action: str = "execution",
        payload: dict[str, Any] | None = None,
        error: Exception | str = "",
        stack_trace: str = "",
        max_retries: int = 3,
    ) -> str: ...

    def enqueue(
        self,
        persona: DLQItem | str,
        action: str = "execution",
        payload: dict[str, Any] | None = None,
        error: Exception | str = "",
        stack_trace: str = "",
        max_retries: int = 3,
    ) -> str:
        """Store a failed task envelope with redacted secrets."""
        now = int(time.time())

        if isinstance(persona, DLQItem):
            item = persona
            item_id = item.dlq_id or f"dlq_{uuid.uuid4().hex[:12]}"
            p_name = item.persona
            act = "execution"
            payload_dict = item.payload
            err_msg = redact_secrets(item.error_message)
            err_type = "DLQTaskError"
            clean_stack = ""
            max_ret = item.max_retries
            stat = item.status
            next_retry_at = now + 2
        else:
            p_name = persona
            item_id = f"dlq_{uuid.uuid4().hex[:12]}"
            act = action
            payload_dict = payload or {}
            err_type = type(error).__name__ if isinstance(error, Exception) else "TaskError"
            err_msg = redact_secrets(str(error))
            clean_stack = redact_secrets(stack_trace)
            max_ret = max_retries
            stat = "pending"
            next_retry_at = now + 2

        try:
            raw_payload = json.dumps(payload_dict, ensure_ascii=False)
            clean_payload = redact_secrets(raw_payload)
        except Exception:
            clean_payload = "{}"

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO dead_letter_items (
                    item_id, persona, action, payload, error_type,
                    error_message, stack_trace, retry_count, max_retries,
                    status, created_at, updated_at, next_retry_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    payload=excluded.payload,
                    error_message=excluded.error_message,
                    updated_at=excluded.updated_at
                """,
                (
                    item_id,
                    p_name,
                    act,
                    clean_payload,
                    err_type,
                    err_msg,
                    clean_stack,
                    max_ret,
                    stat,
                    now,
                    now,
                    next_retry_at,
                ),
            )
        logger.warning(
            "Task enqueued to DLQ: item_id=%s, persona=%s, error=%s",
            item_id,
            persona,
            err_msg,
        )
        return item_id

    def peek(self, limit: int = 50) -> list[DLQItem]:
        """Fetch pending DLQ items as DLQItem instances."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dead_letter_items
                WHERE status IN ('pending', 'PENDING', 'retrying', 'RETRYING')
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_dlq_item(r) for r in rows]

    def list_pending(self, limit: int = 50) -> list[DeadLetterItem]:
        """Fetch pending DLQ tasks eligible for retry or inspection."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dead_letter_items
                WHERE status IN ('pending', 'PENDING')
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_item(r) for r in rows]

    def list_dead(self, limit: int = 50) -> list[DLQItem]:
        """List dead/quarantined items."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dead_letter_items
                WHERE status IN ('dead', 'DEAD', 'quarantined')
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_dlq_item(r) for r in rows]

    def record_retry_attempt(self, dlq_id: str) -> bool:
        """Increment retry count. If max reached, transition to DEAD."""
        now = int(time.time())
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT retry_count, max_retries FROM dead_letter_items WHERE item_id = ?",
                (dlq_id,),
            ).fetchone()
            if not row:
                return False
            new_count = row["retry_count"] + 1
            if new_count >= row["max_retries"]:
                conn.execute(
                    "UPDATE dead_letter_items SET retry_count = ?, status = 'DEAD', updated_at = ? WHERE item_id = ?",
                    (new_count, now, dlq_id),
                )
                return False

            next_delay = 2**new_count
            conn.execute(
                "UPDATE dead_letter_items SET retry_count = ?, status = 'RETRYING', updated_at = ?, next_retry_at = ? WHERE item_id = ?",
                (new_count, now, now + next_delay, dlq_id),
            )
            return True

    def resolve(self, dlq_id: str) -> bool:
        now = int(time.time())
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE dead_letter_items SET status = 'RESOLVED', updated_at = ? WHERE item_id = ?",
                (now, dlq_id),
            )
            return cur.rowcount > 0

    def mark_replayed(self, item_id: str) -> bool:
        now = int(time.time())
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE dead_letter_items SET status = 'replayed', updated_at = ? WHERE item_id = ?",
                (now, item_id),
            )
            return cur.rowcount > 0

    def record_retry_failure(self, item_id: str, error_message: str = "") -> bool:
        now = int(time.time())
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT retry_count, max_retries FROM dead_letter_items WHERE item_id = ?",
                (item_id,),
            ).fetchone()
            if not row:
                return False
            new_count = row["retry_count"] + 1
            if new_count >= row["max_retries"]:
                status = "quarantined"
            else:
                status = "pending"

            clean_err = redact_secrets(error_message) if error_message else None
            if clean_err:
                conn.execute(
                    "UPDATE dead_letter_items SET retry_count = ?, status = ?, error_message = ?, updated_at = ? WHERE item_id = ?",
                    (new_count, status, clean_err, now, item_id),
                )
            else:
                conn.execute(
                    "UPDATE dead_letter_items SET retry_count = ?, status = ?, updated_at = ? WHERE item_id = ?",
                    (new_count, status, now, item_id),
                )
            return True

    def quarantine(self, item_id: str) -> bool:
        now = int(time.time())
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE dead_letter_items SET status = 'quarantined', updated_at = ? WHERE item_id = ?",
                (now, item_id),
            )
            return cur.rowcount > 0

    def get_item(self, item_id: str) -> DeadLetterItem | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM dead_letter_items WHERE item_id = ?", (item_id,)
            ).fetchone()
            return self._row_to_item(row) if row else None

    def _row_to_dlq_item(self, row: sqlite3.Row) -> DLQItem:
        try:
            payload = json.loads(row["payload"])
        except Exception:
            payload = {}
        return DLQItem(
            dlq_id=row["item_id"],
            incident_id=row["item_id"],
            persona=row["persona"],
            payload=payload,
            error_message=row["error_message"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            enqueued_at=datetime.fromtimestamp(row["created_at"], tz=UTC),
            status=row["status"],
        )

    def _row_to_item(self, row: sqlite3.Row) -> DeadLetterItem:
        try:
            payload = json.loads(row["payload"])
        except Exception:
            payload = {}
        return DeadLetterItem(
            item_id=row["item_id"],
            persona=row["persona"],
            action=row["action"],
            payload=payload,
            error_type=row["error_type"],
            error_message=row["error_message"],
            stack_trace=row["stack_trace"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            next_retry_at=row["next_retry_at"],
        )
