"""Self-Healing Multi-Agent Recovery Protocol.

Provides automated exception interception, dead-letter queue (DLQ) persistent
buffering, memory snapshot rollback, dynamic circuit breakers, and self-healing
remediation across all 6 personas.
"""

from __future__ import annotations

from .circuit_breaker import DynamicCircuitBreaker
from .dlq import DeadLetterItem, DeadLetterQueue
from .models import CircuitState, DLQItem, ErrorSeverity, IncidentEnvelope, classify_exception
from .snapshot import MemorySnapshotManager
from .supervisor import RecoveryResult, SelfHealingSupervisor

__all__ = [
    "CircuitState",
    "DLQItem",
    "DeadLetterItem",
    "DeadLetterQueue",
    "DynamicCircuitBreaker",
    "ErrorSeverity",
    "IncidentEnvelope",
    "MemorySnapshotManager",
    "RecoveryResult",
    "SelfHealingSupervisor",
    "classify_exception",
]
