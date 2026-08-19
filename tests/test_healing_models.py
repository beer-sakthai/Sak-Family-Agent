# tests/test_healing_models.py
from datetime import UTC, datetime

from sakthai.healing.models import (
    CircuitState,
    ErrorSeverity,
    IncidentEnvelope,
    classify_exception,
)


def test_error_severity_values():
    assert ErrorSeverity.TRANSIENT == "transient"
    assert ErrorSeverity.STATE_CORRUPT == "state_corrupt"
    assert ErrorSeverity.FATAL == "fatal"


def test_circuit_state_values():
    assert CircuitState.CLOSED == "closed"
    assert CircuitState.OPEN == "open"
    assert CircuitState.HALF_OPEN == "half_open"


def test_classify_exception_transient():
    exc = Exception("HTTP 429: Too Many Requests - Rate limit exceeded")
    assert classify_exception(exc) == ErrorSeverity.TRANSIENT

    timeout_exc = TimeoutError("Connection timed out after 30s")
    assert classify_exception(timeout_exc) == ErrorSeverity.TRANSIENT


def test_classify_exception_state_corrupt():
    exc = Exception("sqlite3.OperationalError: database is locked")
    assert classify_exception(exc) == ErrorSeverity.STATE_CORRUPT


def test_classify_exception_fatal():
    exc = ValueError("Invalid API credentials supplied")
    assert classify_exception(exc) == ErrorSeverity.FATAL


def test_incident_envelope_serialization():
    now = datetime.now(UTC)
    envelope = IncidentEnvelope(
        incident_id="inc-12345",
        persona="saksee",
        severity=ErrorSeverity.TRANSIENT,
        error_message="429 Rate Limit",
        stack_trace="Traceback...",
        timestamp=now,
        context={"task": "scraping_job"},
    )
    data = envelope.to_dict()
    assert data["incident_id"] == "inc-12345"
    assert data["severity"] == "transient"
    assert data["persona"] == "saksee"
