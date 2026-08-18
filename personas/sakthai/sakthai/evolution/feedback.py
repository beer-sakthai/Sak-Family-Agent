"""Feedback and Trajectory Collector for Multi-Agent Evolution."""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from pathlib import Path

from sakthai.evolution.models import TrajectoryFeedback


class FeedbackCollector:
    """Collects and aggregates agent trajectory feedback and failure patterns."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_env = os.getenv("SAKTHAI_EVOLUTION_DB")
            self.db_path = (
                Path(db_env) if db_env else Path.home() / ".sakthai" / "evolution.sqlite3"
            )
        elif str(db_path) == ":memory:":
            self.db_path = Path(":memory:")
        else:
            self.db_path = Path(db_path)

        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._shared_conn: sqlite3.Connection | None = None
        if str(self.db_path) == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False, timeout=30.0)
            self._shared_conn.row_factory = sqlite3.Row

        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evolution_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    tool_errors INTEGER NOT NULL,
                    duration_sec REAL NOT NULL,
                    user_rating REAL,
                    error_summary TEXT,
                    timestamp TEXT NOT NULL
                );
                """
            )

    def record_feedback(
        self,
        persona: str,
        task_type: str,
        success: bool,
        tool_errors: int = 0,
        duration_sec: float = 0.0,
        user_rating: float | None = None,
        error_summary: str | None = None,
    ) -> TrajectoryFeedback:
        """Record trajectory outcome."""
        fb = TrajectoryFeedback(
            feedback_id=f"fb_{uuid.uuid4().hex[:10]}",
            persona=persona.lower(),
            task_type=task_type,
            success=success,
            tool_errors=tool_errors,
            duration_sec=duration_sec,
            user_rating=user_rating,
            error_summary=error_summary,
        )

        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO evolution_feedback (
                    feedback_id, persona, task_type, success, tool_errors, duration_sec, user_rating, error_summary, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    fb.feedback_id,
                    fb.persona,
                    fb.task_type,
                    1 if fb.success else 0,
                    fb.tool_errors,
                    fb.duration_sec,
                    fb.user_rating,
                    fb.error_summary,
                    fb.timestamp,
                ),
            )

        return fb

    def get_persona_metrics(self, persona: str) -> dict[str, object]:
        """Aggregate performance and error statistics for a persona."""
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) as total_trajectories,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                       SUM(tool_errors) as total_tool_errors,
                       AVG(duration_sec) as avg_duration,
                       AVG(user_rating) as avg_rating
                FROM evolution_feedback
                WHERE persona = ?;
                """,
                (persona.lower(),),
            ).fetchone()

            total = int(row["total_trajectories"]) if row and row["total_trajectories"] else 0
            successful = int(row["successful"]) if row and row["successful"] else 0
            tool_errors = int(row["total_tool_errors"]) if row and row["total_tool_errors"] else 0
            avg_duration = float(row["avg_duration"]) if row and row["avg_duration"] else 0.0
            avg_rating = float(row["avg_rating"]) if row and row["avg_rating"] else 5.0

            success_rate = (successful / total) if total > 0 else 1.0

            return {
                "persona": persona.lower(),
                "total_trajectories": total,
                "success_rate": round(success_rate, 4),
                "total_tool_errors": tool_errors,
                "avg_duration_sec": round(avg_duration, 2),
                "avg_user_rating": round(avg_rating, 2),
            }
