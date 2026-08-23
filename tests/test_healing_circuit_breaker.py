# tests/test_healing_circuit_breaker.py
import time

from sakthai.healing.circuit_breaker import DynamicCircuitBreaker
from sakthai.healing.models import CircuitState


def test_circuit_breaker_initial_closed():
    cb = DynamicCircuitBreaker(failure_threshold=3, recovery_time_sec=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_execution() is True


def test_circuit_breaker_trips_to_open():
    cb = DynamicCircuitBreaker(failure_threshold=2, recovery_time_sec=1.0)
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_execution() is False


def test_circuit_breaker_half_open_recovery():
    cb = DynamicCircuitBreaker(failure_threshold=2, recovery_time_sec=0.2)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    time.sleep(0.25)
    # After recovery timeout, it transitions to HALF_OPEN
    assert cb.allow_execution() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success closes the circuit
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_reset():
    cb = DynamicCircuitBreaker(failure_threshold=1, recovery_time_sec=10.0)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_execution() is True
