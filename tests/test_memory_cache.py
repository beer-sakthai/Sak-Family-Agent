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

    def test_delete_and_clear_and_set_overwrite(self):
        cache = MemoryLRUCache(capacity=5, ttl_seconds=10.0)
        cache.set("k", "v1")
        # Overwrite hits the move_to_end branch in set().
        cache.set("k", "v2")
        self.assertEqual(cache.get("k"), "v2")
        # delete() returns True on hit, False on miss.
        self.assertTrue(cache.delete("k"))
        self.assertFalse(cache.delete("k"))
        # clear() empties the whole cache.
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        self.assertEqual(cache.size, 0)


class TestCircuitBreakerAndDistributedCache(unittest.TestCase):
    """Test distributed cache fallback and resilience."""

    def test_circuit_breaker_tripping_and_recovery(self):
        # Use a long recovery window and rewind the clock deterministically
        # rather than time.sleep()ing past a short one — a >100ms pause between
        # the .record_failure() and .allow_request() lines (routine on a busy
        # runner) would flip the breaker back to HALF-OPEN and make the
        # assertion racy.
        cb = CircuitBreaker(failure_threshold=2, recovery_time_sec=30.0)
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertEqual(cb.state, "OPEN")
        self.assertFalse(cb.allow_request())

        # Simulate the recovery window elapsing.
        cb.last_failure_time = time.time() - (cb.recovery_time_sec + 1)
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

    def test_distributed_cache_no_url_short_circuits(self):
        # No redis_url and no env var → _get_client returns None, get returns None,
        # invalidate clears L1 without ever calling redis.
        for var in ("VALKEY_URL", "REDIS_URL"):
            os.environ.pop(var, None)
        dist_cache = DistributedMemoryCache(redis_url=None)
        self.assertIsNone(dist_cache.redis_url)
        dist_cache.set("fact:no-redis", {"x": 1})
        # L1 still serves the value.
        self.assertEqual(dist_cache.get("fact:no-redis"), {"x": 1})
        # invalidate only affects L1 (no client to broadcast to).
        dist_cache.invalidate("fact:no-redis", broadcast=True)
        self.assertIsNone(dist_cache.get("fact:no-redis"))

    def test_distributed_cache_open_circuit_blocks_client(self):
        # A tripped breaker returns None from _get_client even with a URL set.
        dist_cache = DistributedMemoryCache(redis_url="redis://localhost:9999/0")
        dist_cache.circuit_breaker.state = "OPEN"
        dist_cache.circuit_breaker.last_failure_time = time.time()
        self.assertIsNone(dist_cache._get_client())


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

    def test_batch_failure_falls_back_to_per_row_commits(self):
        """Some queries in a batch reference a non-existent table.

        Exercises `_commit_batch`'s exception branch: the batch BEGIN IMMEDIATE
        rolls back, each row is retried individually, the good rows still land,
        the bad rows are logged and dropped, and total_writes reflects only the
        committed ones.
        """
        completed: list[int] = []
        coalescer = AsyncWriteCoalescer(
            self.db_path,
            batch_interval_ms=20,
            max_batch_size=50,
            on_batch_complete=completed.append,
        )
        coalescer.enqueue("INSERT INTO items (worker, val) VALUES (?, ?)", ("mixed", 1))
        coalescer.enqueue("INSERT INTO no_such_table (x) VALUES (?)", (42,))
        coalescer.enqueue("INSERT INTO items (worker, val) VALUES (?, ?)", ("mixed", 2))
        coalescer.flush(timeout_sec=5.0)
        coalescer.close()

        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT val FROM items WHERE worker='mixed' ORDER BY val").fetchall()
        conn.close()
        self.assertEqual(rows, [(1,), (2,)])
        self.assertEqual(coalescer.stats["total_writes"], 2)
        # The completion callback fires with the committed count when >0.
        self.assertEqual(completed, [2])
        # pending_count property returns 0 once drained.
        self.assertEqual(coalescer.pending_count, 0)


if __name__ == "__main__":
    unittest.main()
