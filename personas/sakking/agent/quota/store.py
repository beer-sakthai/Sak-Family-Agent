"""Persistent SQLite store and in-process sliding window for Quota Sentinel."""

from __future__ import annotations

import collections
import os
import sqlite3
import threading
import time
from pathlib import Path

from .models import get_pacific_date_str


def _get_default_db_path() -> Path:
    base_dir = Path(os.environ.get("SAKTHAI_HOME", "~/.sakthai")).expanduser()
    return base_dir / "quota_sentinel.db"


class QuotaSentinelStore:
    """Atomic SQLite store for daily RPD and in-memory sliding window for sub-minute RPM/TPM."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is not None:
            self.db_path = Path(db_path) if str(db_path) != ":memory:" else db_path
        elif "SAKTHAI_QUOTA_DB" in os.environ:
            self.db_path = Path(os.environ["SAKTHAI_QUOTA_DB"])
        else:
            self.db_path = _get_default_db_path()

        self._lock = threading.Lock()
        self._rpm_windows: dict[str, collections.deque[float]] = {}
        self._tpm_windows: dict[str, collections.deque[tuple[float, int]]] = {}
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if isinstance(self.db_path, str) and self.db_path == ":memory:":
            conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            assert isinstance(self.db_path, Path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path), timeout=15.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_usage (
                    date TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    request_count INTEGER NOT NULL DEFAULT 0,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (date, model_name)
                );
                """
            )
            conn.commit()

    def _prune_windows(self, model: str, now: float) -> None:
        cutoff = now - 60.0
        if model in self._rpm_windows:
            dq = self._rpm_windows[model]
            while dq and dq[0] < cutoff:
                dq.popleft()
        if model in self._tpm_windows:
            dq_tpm = self._tpm_windows[model]
            while dq_tpm and dq_tpm[0][0] < cutoff:
                dq_tpm.popleft()

    def record_request(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        timestamp: float | None = None,
        date_str: str | None = None,
    ) -> None:
        """Record an API request into in-memory sliding window and persistent SQLite store."""
        base_name = model.rsplit("/", 1)[-1]
        now = time.time() if timestamp is None else timestamp
        target_date = get_pacific_date_str() if date_str is None else date_str
        total_tokens = int(input_tokens or 0) + int(output_tokens or 0)

        with self._lock:
            # Update sliding window
            if base_name not in self._rpm_windows:
                self._rpm_windows[base_name] = collections.deque()
            if base_name not in self._tpm_windows:
                self._tpm_windows[base_name] = collections.deque()

            self._rpm_windows[base_name].append(now)
            self._tpm_windows[base_name].append((now, total_tokens))
            self._prune_windows(base_name, now)

            # Update daily persistent store
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO daily_usage (date, model_name, request_count, input_tokens, output_tokens)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(date, model_name) DO UPDATE SET
                        request_count = request_count + 1,
                        input_tokens = input_tokens + excluded.input_tokens,
                        output_tokens = output_tokens + excluded.output_tokens;
                    """,
                    (target_date, base_name, int(input_tokens or 0), int(output_tokens or 0)),
                )
                conn.commit()

    def get_daily_usage(
        self, model: str | None = None, date_str: str | None = None
    ) -> dict[str, dict[str, int]]:
        """Fetch daily usage stats for a given date (defaults to current US/Pacific date)."""
        target_date = get_pacific_date_str() if date_str is None else date_str
        base_name = model.rsplit("/", 1)[-1] if model else None

        with self._lock, self._get_connection() as conn:
            if base_name:
                cursor = conn.execute(
                    """
                    SELECT model_name, request_count, input_tokens, output_tokens
                    FROM daily_usage
                    WHERE date = ? AND model_name = ?;
                    """,
                    (target_date, base_name),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT model_name, request_count, input_tokens, output_tokens
                    FROM daily_usage
                    WHERE date = ?;
                    """,
                    (target_date,),
                )
            rows = cursor.fetchall()

        result: dict[str, dict[str, int]] = {}
        for row in rows:
            result[row[0]] = {
                "request_count": int(row[1]),
                "input_tokens": int(row[2]),
                "output_tokens": int(row[3]),
            }
        return result

    def get_sliding_window_usage(self, model: str, now: float | None = None) -> tuple[int, int]:
        """Return (rpm_used, tpm_used) in the last 60 seconds."""
        base_name = model.rsplit("/", 1)[-1]
        current_time = time.time() if now is None else now

        with self._lock:
            self._prune_windows(base_name, current_time)
            rpm = len(self._rpm_windows.get(base_name, ()))
            tpm = sum(tokens for _, tokens in self._tpm_windows.get(base_name, ()))
            return rpm, tpm

    def get_oldest_timestamp_in_window(self, model: str, now: float | None = None) -> float | None:
        """Return the oldest timestamp within the sliding window, or None if empty."""
        base_name = model.rsplit("/", 1)[-1]
        current_time = time.time() if now is None else now

        with self._lock:
            self._prune_windows(base_name, current_time)
            dq = self._rpm_windows.get(base_name)
            if dq:
                return dq[0]
            return None
