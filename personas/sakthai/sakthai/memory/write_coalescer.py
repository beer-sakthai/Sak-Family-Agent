"""SQLite Write Coalescer for high-throughput batching in SakThai agent."""

import contextlib
import logging
import queue
import sqlite3
import threading
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class WriteCoalescer:
    """Coalesces individual SQL write requests into batched transactions."""

    def __init__(
        self,
        db_path: str,
        batch_interval_ms: int = 50,
        max_batch_size: int = 100,
        on_batch_complete: Callable[[int], None] | None = None,
    ):
        self.db_path = db_path
        self.batch_interval_sec = batch_interval_ms / 1000.0
        self.max_batch_size = max_batch_size
        self.on_batch_complete = on_batch_complete

        self._queue: queue.Queue[tuple[str, tuple[Any, ...]]] = queue.Queue()
        self._running = False
        self._worker_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the background coalescer worker thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="WriteCoalescerThread"
            )
            self._worker_thread.start()

    def stop(self) -> None:
        """Stop the background worker thread and flush pending writes."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    def enqueue(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        """Queue a SQL write operation for batched execution."""
        self._queue.put((sql, params))

    def _worker_loop(self) -> None:
        """Background thread main loop."""
        conn = sqlite3.connect(self.db_path)
        while self._running or not self._queue.empty():
            batch = []
            start_time = time.time()

            while len(batch) < self.max_batch_size:
                timeout = max(0.0, self.batch_interval_sec - (time.time() - start_time))
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
        """Commit a batch of write operations in a single transaction."""
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")
            for sql, params in batch:
                cursor.execute(sql, params)
            conn.commit()
            if self.on_batch_complete:
                self.on_batch_complete(len(batch))
        except Exception as err:
            logger.error("Failed to commit coalesced batch of %d writes: %s", len(batch), err)
            with contextlib.suppress(Exception):
                conn.rollback()

    def flush(self, timeout_sec: float = 5.0) -> None:
        """Block until all currently enqueued items are processed or timeout is reached."""
        start_time = time.time()
        while not self._queue.empty() and (time.time() - start_time) < timeout_sec:
            time.sleep(0.01)
