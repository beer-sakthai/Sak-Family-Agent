"""In-memory and distributed caching layer for SakThai memory store.

Provides:
- ``MemoryLRUCache``: Thread-safe, bounded, in-process LRU cache with TTL eviction.
- ``DistributedMemoryCache``: Resilience-wrapped Redis/Valkey client with circuit breaker
  and pub/sub invalidation topic (degrades safely to no-op when Redis is offline).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

# Default Redis / Valkey invalidation topic
INVALIDATION_CHANNEL = "agent:memory:invalidations"


class MemoryLRUCache:
    """Thread-safe bounded in-process LRU cache with TTL expiration."""

    def __init__(self, capacity: int = 1000, ttl_seconds: float = 30.0):
        self._capacity = max(1, capacity)
        self._default_ttl = max(0.1, ttl_seconds)
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            value, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        duration = ttl if ttl is not None and ttl > 0 else self._default_ttl
        expires_at = time.time() + duration
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expires_at)
            if len(self._cache) > self._capacity:
                self._cache.popitem(last=False)
                self._evictions += 1

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "capacity": self._capacity,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self._evictions,
            }


class CircuitBreaker:
    """Lightweight circuit breaker for external distributed services."""

    def __init__(self, failure_threshold: int = 3, recovery_time_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_time_sec:
                    self.state = "HALF-OPEN"
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.state = "CLOSED"

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(
                    "Distributed cache circuit breaker tripped to OPEN (failures=%d)",
                    self.failure_count,
                )


class DistributedMemoryCache:
    """Redis/Valkey distributed cache abstraction with fail-safe local fallback."""

    def __init__(
        self,
        redis_url: str | None = None,
        local_l1: MemoryLRUCache | None = None,
    ):
        self.redis_url = redis_url or os.getenv("VALKEY_URL") or os.getenv("REDIS_URL")
        self.l1 = local_l1 or MemoryLRUCache(capacity=2000, ttl_seconds=60.0)
        self.circuit_breaker = CircuitBreaker()
        self._client: Any = None
        self._initialized = False
        self._subscriber_thread: threading.Thread | None = None

    def _get_client(self) -> Any | None:
        if not self.redis_url:
            return None
        if not self.circuit_breaker.allow_request():
            return None
        if self._client is not None:
            return self._client

        try:
            import redis

            self._client = redis.from_url(
                self.redis_url,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
                decode_responses=True,
            )
            self._client.ping()
            self.circuit_breaker.record_success()
            return self._client
        except Exception as err:
            self.circuit_breaker.record_failure()
            logger.debug("Distributed cache unavailable, using local mode: %s", err)
            self._client = None
            return None

    def get(self, key: str) -> Any | None:
        # 1. Check L1 in-process cache
        val = self.l1.get(key)
        if val is not None:
            return val

        # 2. Check L2 distributed cache
        client = self._get_client()
        if client is not None:
            try:
                raw = client.get(key)
                if raw is not None:
                    parsed = json.loads(raw)
                    self.l1.set(key, parsed)
                    self.circuit_breaker.record_success()
                    return parsed
            except Exception as err:
                self.circuit_breaker.record_failure()
                logger.debug("L2 cache read failed: %s", err)

        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        # Populate L1
        self.l1.set(key, value, ttl=float(ttl_seconds))

        # Populate L2
        client = self._get_client()
        if client is not None:
            try:
                raw = json.dumps(value, ensure_ascii=False)
                client.setex(key, ttl_seconds, raw)
                self.circuit_breaker.record_success()
            except Exception as err:
                self.circuit_breaker.record_failure()
                logger.debug("L2 cache write failed: %s", err)

    def invalidate(self, key: str, broadcast: bool = True) -> None:
        self.l1.delete(key)
        client = self._get_client()
        if client is not None:
            try:
                client.delete(key)
                if broadcast:
                    client.publish(
                        INVALIDATION_CHANNEL,
                        json.dumps({"action": "invalidate", "key": key}),
                    )
                self.circuit_breaker.record_success()
            except Exception as err:
                self.circuit_breaker.record_failure()
                logger.debug("L2 cache invalidation failed: %s", err)
