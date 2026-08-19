"""Self-Healing Supervisor coordinating DLQ, rollbacks, and recovery remediation."""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .circuit_breaker import DynamicCircuitBreaker
from .dlq import DeadLetterItem, DeadLetterQueue
from .models import DLQItem, ErrorSeverity, classify_exception
from .snapshot import MemorySnapshotManager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    action_taken: str
    remediated: bool
    severity: ErrorSeverity
    dlq_id: str | None = None
    rolled_back: bool = False
    error_message: str = ""


class SelfHealingSupervisor:
    """Central resilience controller across all 6 agent personas."""

    def __init__(
        self,
        dlq: DeadLetterQueue | None = None,
        snapshot_mgr: MemorySnapshotManager | None = None,
    ):
        self.dlq = dlq or DeadLetterQueue()
        self.snapshot_mgr = snapshot_mgr or MemorySnapshotManager()
        self._circuit_breakers: dict[str, DynamicCircuitBreaker] = {}

    def get_circuit_breaker(self, persona: str) -> DynamicCircuitBreaker:
        if persona not in self._circuit_breakers:
            self._circuit_breakers[persona] = DynamicCircuitBreaker(
                failure_threshold=3, recovery_time_sec=30.0
            )
        return self._circuit_breakers[persona]

    def classify_error(self, error: Exception | str) -> ErrorSeverity:
        return classify_exception(error)

    def handle_exception(
        self,
        persona: str,
        exception: Exception | str,
        payload: dict[str, Any],
        db_path: Path | str | None = None,
        checkpoint_id: str | None = None,
    ) -> RecoveryResult:
        """Alias for handle_execution_failure accepting direct db_path or payload."""
        store_or_path = db_path
        return self.handle_execution_failure(
            persona=persona,
            action="execution",
            payload=payload,
            error=exception if isinstance(exception, Exception) else Exception(str(exception)),
            store=store_or_path,
            checkpoint_id=checkpoint_id,
        )

    def handle_execution_failure(
        self,
        persona: str,
        action: str,
        payload: dict[str, Any],
        error: Exception,
        store: Any | None = None,
        checkpoint_id: str | None = None,
    ) -> RecoveryResult:
        """Handle execution exception with automated remediation strategy."""
        severity = self.classify_error(error)
        stack = traceback.format_exc()
        cb = self.get_circuit_breaker(persona)
        cb.record_failure()

        rolled_back = False
        action_taken = "none"

        # 1. State Rollback if checkpoint provided
        if checkpoint_id and store:
            rolled_back = self.snapshot_mgr.rollback(store, checkpoint_id)
            if rolled_back:
                action_taken = "memory_rollback"

        # 2. Enqueue to DLQ for durable persistence and replay
        dlq_id = self.dlq.enqueue(
            persona=persona,
            action=action,
            payload=payload,
            error=error,
            stack_trace=stack,
        )
        if action_taken == "none":
            action_taken = "enqueued_dlq"
        else:
            action_taken += "+enqueued_dlq"

        logger.warning(
            "Self-healing remediation executed: persona=%s, severity=%s, action=%s, dlq_id=%s",
            persona,
            severity.value,
            action_taken,
            dlq_id,
        )

        return RecoveryResult(
            action_taken=action_taken,
            remediated=rolled_back or (severity == ErrorSeverity.TRANSIENT) or (dlq_id is not None),
            severity=severity,
            dlq_id=dlq_id,
            rolled_back=rolled_back,
            error_message=str(error),
        )

    def replay_dlq_item(
        self, item_id: str, executor_fn: Callable[[DeadLetterItem | DLQItem], Any]
    ) -> bool:
        """Execute replay callback for a DLQ task."""
        with self.dlq._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM dead_letter_items WHERE item_id = ?", (item_id,)
            ).fetchone()
            if not row or row["status"] not in ("pending", "PENDING", "retrying", "RETRYING"):
                return False

            item = self.dlq._row_to_item(row)
            try:
                executor_fn(item)
                self.dlq.resolve(item_id)
                cb = self.get_circuit_breaker(item.persona)
                cb.record_success()
                logger.info("Successfully replayed DLQ task: %s", item_id)
                return True
            except Exception as err:
                self.dlq.record_retry_attempt(item_id)
                logger.error("Failed to replay DLQ task %s: %s", item_id, err)
                return False

    def get_health_status(self, persona: str) -> dict[str, Any]:
        cb = self.get_circuit_breaker(persona)
        return {
            "persona": persona,
            "circuit_state": cb.state.value,
            "failure_count": cb.failure_count,
            "healthy": cb.state == "closed",
        }
