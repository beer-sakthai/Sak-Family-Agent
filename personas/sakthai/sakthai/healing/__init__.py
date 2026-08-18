"""Self-Healing Multi-Agent Recovery Protocol.

Provides automated exception interception, dead-letter queue (DLQ) persistent
buffering, memory snapshot rollback, dynamic circuit breakers, and self-healing
remediation across all 6 personas.
"""

from __future__ import annotations

from .dlq import DeadLetterItem, DeadLetterQueue
from .snapshot import MemorySnapshotManager
from .supervisor import ErrorSeverity, RecoveryResult, SelfHealingSupervisor

__all__ = [
    "DeadLetterItem",
    "DeadLetterQueue",
    "ErrorSeverity",
    "MemorySnapshotManager",
    "RecoveryResult",
    "SelfHealingSupervisor",
]
