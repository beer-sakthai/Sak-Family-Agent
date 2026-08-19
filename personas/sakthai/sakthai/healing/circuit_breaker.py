"""Dynamic Circuit Breaker protecting agent personas against cascading downstream errors."""

from __future__ import annotations

import time

from .models import CircuitState


class DynamicCircuitBreaker:
    """Tracks consecutive failures and isolates degraded endpoints/personas."""

    def __init__(self, failure_threshold: int = 3, recovery_time_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self._state: CircuitState = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and time.time() - self.last_failure_time >= self.recovery_time_sec
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_execution(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        self.failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._state = CircuitState.CLOSED
