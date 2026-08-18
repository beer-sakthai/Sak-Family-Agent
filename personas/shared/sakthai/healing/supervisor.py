"""Self-Healing Supervisor coordinating DLQ, rollbacks, and recovery remediation."""

from __future__ import annotations

import enum
import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..memory.cache import CircuitBreaker
from .dlq import DeadLetterItem, DeadLetterQueue
from .snapshot import MemorySnapshotManager

if TYPE_CHECKING:
    from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)


class ErrorSeverity(enum.StrEnum):
    TRANSIENT = "transient"  # 429, timeouts, connection resets
    STATE_CORRUPT = "state_corrupt"  # partial transaction fail, db lock
    FATAL = "fatal"  # auth fail, invalid schema, unrecoverable


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
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, persona: str) -> CircuitBreaker:
        if persona not in self._circuit_breakers:
            self._circuit_breakers[persona] = CircuitBreaker(
                failure_threshold=3, recovery_time_sec=30.0
            )
        return self._circuit_breakers[persona]

    def classify_error(self, error: Exception | str) -> ErrorSeverity:
        err_str = str(error).lower()

        # Transient / Rate Limit patterns
        if any(
            w in err_str
            for w in ["429", "rate limit", "timeout", "connection reset", "econnrefused"]
        ):
            return ErrorSeverity.TRANSIENT

        # State corruption patterns
        if any(
            w in err_str
            for w in ["database is locked", "sqlite_busy", "integrity", "savepoint", "rollback"]
        ):
            return ErrorSeverity.STATE_CORRUPT

        return ErrorSeverity.FATAL

    def handle_execution_failure(
        self,
        persona: str,
        action: str,
        payload: dict[str, Any],
        error: Exception,
        store: MemoryStore | None = None,
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
        if (
            checkpoint_id
            and store
            and severity in (ErrorSeverity.STATE_CORRUPT, ErrorSeverity.FATAL)
        ):
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
            action_taken = "enqueued_to_dlq"
        else:
            action_taken += "+enqueued_to_dlq"

        logger.warning(
            "Self-healing remediation executed: persona=%s, severity=%s, action=%s, dlq_id=%s",
            persona,
            severity.value,
            action_taken,
            dlq_id,
        )

        return RecoveryResult(
            action_taken=action_taken,
            remediated=rolled_back or (severity == ErrorSeverity.TRANSIENT),
            severity=severity,
            dlq_id=dlq_id,
            rolled_back=rolled_back,
            error_message=str(error),
        )

    def replay_dlq_item(self, item_id: str, executor_fn: Callable[[DeadLetterItem], Any]) -> bool:
        """Execute replay callback for a DLQ task."""
        item = self.dlq.get_item(item_id)
        if not item or item.status != "pending":
            return False

        try:
            executor_fn(item)
            self.dlq.mark_replayed(item_id)
            cb = self.get_circuit_breaker(item.persona)
            cb.record_success()
            logger.info("Successfully replayed DLQ task: %s", item_id)
            return True
        except Exception as err:
            self.dlq.record_retry_failure(item_id, str(err))
            logger.error("Failed to replay DLQ task %s: %s", item_id, err)
            return False

    def get_health_status(self, persona: str) -> dict[str, Any]:
        cb = self.get_circuit_breaker(persona)
        return {
            "persona": persona,
            "circuit_state": cb.state,
            "failure_count": cb.failure_count,
            "healthy": cb.state == "CLOSED",
        }
