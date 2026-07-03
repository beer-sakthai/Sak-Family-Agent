"""Durable, queryable memory store for the agent, backed by SQLite.

This provides a simple key-value interface for agent facts, where facts are
grouped by a `kind` for namespacing.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator


@dataclass(frozen=True)
class Fact:
    """A single piece of information in the agent's memory."""

    value: Any
    kind: str
    key: str


class MemoryStore:
    """Manages agent state persistence in an SQLite database."""

    def __init__(self, db_path: str | Path = "memory.db"):
        """Initializes the memory store and ensures the table exists.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        """Creates the 'facts' table if it doesn't already exist."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    kind TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    PRIMARY KEY (kind, key)
                )
                """
            )

    def add_fact(self, value: str, *, kind: str, key: str) -> None:
        """Adds or updates a fact in the database.

        Args:
            value: The value of the fact to store.
            kind: The category or namespace for the fact.
            key: The unique key for the fact within its kind.
        """
        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO facts (kind, key, value)
                VALUES (?, ?, ?)
                """,
                (kind, key, value),
            )

    def get_fact(self, kind: str, key: str) -> Fact | None:
        """Retrieves a single fact from the database.

        Args:
            kind: The kind of the fact to retrieve.
            key: The key of the fact to retrieve.

        Returns:
            A Fact object if found, otherwise None.
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM facts WHERE kind = ? AND key = ?", (kind, key))
        row = cursor.fetchone()
        if row:
            return Fact(value=row["value"], kind=kind, key=key)
        return None

    def list_facts(self) -> Generator[Fact, None, None]:
        """Yields all facts currently in the database."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT kind, key, value FROM facts")
        for row in cursor.fetchall():
            yield Fact(value=row["value"], kind=row["kind"], key=row["key"])

    def close(self) -> None:
        """Closes the database connection."""
        if self._conn:
            self._conn.close()

    def __del__(self) -> None:
        """Ensure connection is closed when the object is destroyed."""
        self.close()