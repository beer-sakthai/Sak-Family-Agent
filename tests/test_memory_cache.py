"""Unit and concurrency tests for memory caching layer and write coalescer."""

import os
import sqlite3
import tempfile
import threading
import time
import unittest

from sakthai.memory.cache import (
    CircuitBreaker,
    DistributedMemoryCache,
    MemoryLRUCache,
)
from sakthai.memory.write_coalescer import AsyncWriteCoalescer


class TestMemoryLRUCache(unittest.TestCase):
    """Test in-process bounded LRU cache."""

    def test_lru_eviction_and_capacity(self):
        cache = MemoryLRUCache(capacity=3, ttl_seconds=10.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.get("b"), 2)

        # Inserting 4th item evicts "c" (least recently used among remaining)
        cache.set("d", 4)
        self.assertEqual(cache.size, 3)
        self.assertEqual(cache.get("d"), 4)
        self.assertEqual(cache.get("a"), 1)
        self.assertIsNone(cache.get("c"))

    def test_ttl_expiration(self):
        cache = MemoryLRUCache(capacity=5, ttl_seconds=0.1)
        cache.set("temp", "hello")
        self.assertEqual(cache.get("temp"), "hello")
        time.sleep(0.15)
        self.assertIsNone(cache.get("temp"))

    def test_stats_tracking(self):
        cache = MemoryLRUCache(capacity=5, ttl_seconds=10.0)
        cache.set("k1", "v1")
        cache.get("k1")  # hit
        cache.get("k2")  # miss
        stats = cache.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 0.5)


class TestCircuitBreakerAndDistributedCache(unittest.TestCase):
    """Test distributed cache fallback and resilience."""

    def test_circuit_breaker_tripping_and_recovery(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_time_sec=0.1)
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertEqual(cb.state, "OPEN")
        self.assertFalse(cb.allow_request())

        # Wait for recovery
        time.sleep(0.15)
        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, "HALF-OPEN")
        cb.record_success()
        self.assertEqual(cb.state, "CLOSED")

    def test_distributed_cache_offline_fallback(self):
        # Point to invalid Redis URL
        dist_cache = DistributedMemoryCache(redis_url="redis://localhost:9999/0")
        dist_cache.set("fact:101", {"entity": "test", "val": 123})
        # Should gracefully read from L1 local fallback
        res = dist_cache.get("fact:101")
        self.assertIsNotNone(res)
        self.assertEqual(res["entity"], "test")


class TestAsyncWriteCoalescer(unittest.TestCase):
    """Test high-concurrency batching without SQLITE_BUSY errors."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_coalesce.db")
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, worker TEXT, val INTEGER)")
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_concurrent_multi_agent_writes(self):
        """Simulate 6 personas writing 100 items simultaneously."""
        coalescer = AsyncWriteCoalescer(self.db_path, batch_interval_ms=20, max_batch_size=50)

        personas = ["sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan"]
        threads = []

        def worker_task(persona_name: str):
            for i in range(50):
                coalescer.enqueue(
                    "INSERT INTO items (worker, val) VALUES (?, ?)",
                    (persona_name, i),
                )
                time.sleep(0.001)

        for p in personas:
            t = threading.Thread(target=worker_task, args=(p,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        coalescer.flush(timeout_sec=5.0)
        coalescer.close()

        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        conn.close()

        # 6 personas * 50 writes = 300 total items committed cleanly
        self.assertEqual(count, 300)
        self.assertGreater(coalescer.stats["total_batches"], 0)


if __name__ == "__main__":
    unittest.main()
