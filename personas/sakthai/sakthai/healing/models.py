"""Data models and failure classification for the Self-Healing Protocol."""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class ErrorSeverity(enum.StrEnum):
    TRANSIENT = "transient"  # 429, timeouts, network resets
    STATE_CORRUPT = "state_corrupt"  # sqlite lock, schema inconsistency
    FATAL = "fatal"  # invalid auth, hard logic errors


class CircuitState(enum.StrEnum):
    CLOSED = "closed"  # Normal operations
    OPEN = "open"  # Failing, block calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class IncidentEnvelope:
    incident_id: str
    persona: str
    severity: ErrorSeverity
    error_message: str
    stack_trace: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class DLQItem:
    dlq_id: str
    incident_id: str
    persona: str
    payload: dict[str, Any]
    error_message: str
    retry_count: int = 0
    max_retries: int = 3
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: str = "PENDING"  # PENDING, RETRYING, RESOLVED, DEAD


def classify_exception(exc: Exception | str) -> ErrorSeverity:
    """Classify an exception into ErrorSeverity based on string/type heuristics."""
    err_str = str(exc).lower()

    if any(
        k in err_str
        for k in [
            "429",
            "rate limit",
            "timeout",
            "timed out",
            "connection reset",
            "econnrefused",
            "temporarily unavailable",
        ]
    ):
        return ErrorSeverity.TRANSIENT

    if any(
        k in err_str
        for k in [
            "database is locked",
            "sqlite_busy",
            "integrity",
            "savepoint",
            "corrupt",
            "unclosed transaction",
        ]
    ):
        return ErrorSeverity.STATE_CORRUPT

    return ErrorSeverity.FATAL
