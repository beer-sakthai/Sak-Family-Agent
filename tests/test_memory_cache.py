"""Unit tests for the thread-safe LRU MemoryCache component."""

import threading
import time
import unittest

from sakthai.memory.cache import (
    MemoryCache,
    MemoryCacheEntry,
    get_memory_cache,
    reset_memory_cache,
)


class TestMemoryCacheEntry(unittest.TestCase):
    """Tests for individual MemoryCacheEntry behavior."""

    def test_entry_expiration(self):
        """Verify is_expired correctly identifies expired entries."""
        entry = MemoryCacheEntry(key="k1", value="v1", ttl_seconds=0.1)
        self.assertFalse(entry.is_expired())

        time.sleep(0.15)
        self.assertTrue(entry.is_expired())

    def test_entry_touch_updates_access_time(self):
        """Verify touch updates the last_accessed timestamp."""
        entry = MemoryCacheEntry(key="k1", value="v1", ttl_seconds=10.0)
        t0 = entry.last_accessed
        time.sleep(0.01)
        entry.touch()
        t1 = entry.last_accessed
        self.assertGreater(t1, t0)

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
class TestMemoryCache(unittest.TestCase):
    """Tests for the thread-safe MemoryCache core functionality."""

    def setUp(self):
        """Reset singleton cache before each test."""
        reset_memory_cache()
        self.cache = MemoryCache(max_size=5, default_ttl=10.0)

    def tearDown(self):
        """Clean up cache after each test."""
        reset_memory_cache()

    def test_get_set_basic(self):
        """Verify basic set and get operations."""
        self.cache.set("a", 100)
        self.assertEqual(self.cache.get("a"), 100)
        self.assertIsNone(self.cache.get("b"))
        self.assertEqual(self.cache.get("b", default="default_val"), "default_val")

    def test_ttl_expiration(self):
        """Verify entries expire after their TTL."""
        self.cache.set("short_lived", "data", ttl=0.1)
        self.assertEqual(self.cache.get("short_lived"), "data")

        time.sleep(0.15)
        self.assertIsNone(self.cache.get("short_lived"))

    def test_lru_eviction(self):
        """Verify least recently used entry is evicted when capacity is reached."""
        cache = MemoryCache(max_size=3, default_ttl=10.0)
        cache.set("k1", 1)
        cache.set("k2", 2)
        cache.set("k3", 3)

        # Access k1 to make k2 the LRU
        cache.get("k1")

        # Insert k4, which should trigger eviction of k2
        cache.set("k4", 4)

        self.assertEqual(cache.get("k1"), 1)
        self.assertIsNone(cache.get("k2"))
        self.assertEqual(cache.get("k3"), 3)
        self.assertEqual(cache.get("k4"), 4)

    def test_delete_and_clear(self):
        """Verify delete and clear operations."""
        self.cache.set("k1", 1)
        self.cache.set("k2", 2)

        self.assertTrue(self.cache.delete("k1"))
        self.assertFalse(self.cache.delete("k1"))
        self.assertIsNone(self.cache.get("k1"))

        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("k2"))

    def test_stats_tracking(self):
        """Verify hits, misses, and evictions are accurately tracked."""
        cache = MemoryCache(max_size=2, default_ttl=10.0)
        cache.set("k1", 1)

        cache.get("k1")  # Hit
        cache.get("k1")  # Hit
        cache.get("k2")  # Miss

        cache.set("k2", 2)
        cache.set("k3", 3)  # Eviction of k1

        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["evictions"], 1)
        self.assertEqual(stats["size"], 2)
        self.assertGreater(stats["hit_ratio"], 0.6)

    def test_thread_safety(self):
        """Verify concurrent access from multiple threads works safely."""
        cache = MemoryCache(max_size=100, default_ttl=5.0)

        def worker(thread_id: int):
            for i in range(50):
                key = f"key_{thread_id}_{i}"
                cache.set(key, i)
                val = cache.get(key)
                self.assertEqual(val, i)

        threads = [
            threading.Thread(target=worker, args=(t,)) for t in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertGreater(cache.size(), 0)

    def test_get_or_compute(self):
        """Verify get_or_compute calculates value on miss and uses cached on hit."""
        computation_count = 0

        def compute_fn():
            nonlocal computation_count
            computation_count += 1
            return f"computed_{computation_count}"

        res1 = self.cache.get_or_compute("calc_key", compute_fn)
        self.assertEqual(res1, "computed_1")
        self.assertEqual(computation_count, 1)

        res2 = self.cache.get_or_compute("calc_key", compute_fn)
        self.assertEqual(res2, "computed_1")
        self.assertEqual(computation_count, 1)

    def test_singleton_get_memory_cache(self):
        """Verify global singleton get_memory_cache returns the same instance."""
        c1 = get_memory_cache()
        c2 = get_memory_cache()
        self.assertIs(c1, c2)

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
