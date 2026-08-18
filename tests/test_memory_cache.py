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


if __name__ == "__main__":
    unittest.main()
