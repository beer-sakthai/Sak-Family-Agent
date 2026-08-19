"""Asynchronous Write Coalescer for high-throughput SQLite mutations.

Decouples multi-agent writes from immediate disk transactions by buffering
mutations in a thread-safe queue and committing them in high-speed batches
using atomic ``BEGIN IMMEDIATE`` blocks.
"""

from __future__ import annotations

import contextlib
import logging
import queue
import sqlite3
import threading
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class AsyncWriteCoalescer:
    """Buffers SQLite mutation queries and writes them in atomic batches."""

    def __init__(
        self,
        db_path: str,
        batch_interval_ms: int = 50,
        max_batch_size: int = 100,
        on_batch_complete: Callable[[int], None] | None = None,
    ):
        self.db_path = db_path
        self.batch_interval_sec = max(0.005, batch_interval_ms / 1000.0)
        self.max_batch_size = max(1, max_batch_size)
        self.on_batch_complete = on_batch_complete

        self._queue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._total_writes = 0
        self._total_batches = 0

        self._worker = threading.Thread(
            target=self._worker_loop,
            name=f"WriteCoalescer-{db_path}",
            daemon=True,
        )
        self._worker.start()

    def enqueue(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        """Enqueue a mutation SQL statement and parameters for background commit."""
        self._queue.put((sql, params))

    def _worker_loop(self) -> None:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")

        while not self._stop_event.is_set() or not self._queue.empty():
            batch: list[tuple[str, tuple[Any, ...]]] = []
            deadline = time.time() + self.batch_interval_sec

            while time.time() < deadline and len(batch) < self.max_batch_size:
                timeout = max(0.001, deadline - time.time())
                try:
                    item = self._queue.get(timeout=timeout)
                    batch.append(item)
                except queue.Empty:
                    break

            if batch:
                self._commit_batch(conn, batch)

        with contextlib.suppress(Exception):
            conn.close()

    def _commit_batch(
        self, conn: sqlite3.Connection, batch: list[tuple[str, tuple[Any, ...]]]
    ) -> None:
        try:
            conn.execute("BEGIN IMMEDIATE")
            for sql, params in batch:
                conn.execute(sql, params)
            conn.commit()
            with self._lock:
                self._total_writes += len(batch)
                self._total_batches += 1
            logger.info("Committed batch of %d writes", len(batch))
            if self.on_batch_complete:
                self.on_batch_complete(len(batch))
        except Exception as err:
            logger.warning(
                "Coalesced batch write failed (%s); attempting individual write commits...", err
            )
            with contextlib.suppress(Exception):
                conn.rollback()
            committed_count = 0
            for sql, params in batch:
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute(sql, params)
                    conn.commit()
                    committed_count += 1
                except Exception as item_err:
                    logger.error("Individual write failed for query %s: %s", sql, item_err)
                    with contextlib.suppress(Exception):
                        conn.rollback()
            with self._lock:
                self._total_writes += committed_count
                if committed_count > 0:
                    self._total_batches += 1
            if self.on_batch_complete and committed_count > 0:
                self.on_batch_complete(committed_count)

    def flush(self, timeout_sec: float = 5.0) -> None:
        """Block until all queued writes have been processed."""
        deadline = time.time() + timeout_sec
        while not self._queue.empty() and time.time() < deadline:
            time.sleep(0.01)

    def close(self) -> None:
        """Flush remaining mutations and terminate the background worker thread."""
        self._stop_event.set()
        self.flush()
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "pending": self._queue.qsize(),
                "total_writes": self._total_writes,
                "total_batches": self._total_batches,
            }
