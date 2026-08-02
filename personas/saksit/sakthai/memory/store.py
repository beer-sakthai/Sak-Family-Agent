"""SQLite-backed memory store.

Two tables hold everything:

* ``facts`` — explicit notes captured with ``sakthai learn``.
* ``observations`` — agent-curated summaries with a weight and confidence.

:class:`MemoryStore` is the only place that talks to SQLite. The module-level
``snapshot_to_*`` helpers render an :meth:`MemoryStore.export_to_dict` snapshot
to JSONL or CSV for portability.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import logging
import os
import sqlite3
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from ..config import memory_db_path, redact_secrets

logger = logging.getLogger(__name__)

# Connection tuning. busy_timeout lets writers wait out contention rather than
# failing immediately with "database is locked".
DB_CONNECT_TIMEOUT = 5.0  # seconds, passed to sqlite3.connect
DB_BUSY_TIMEOUT_MS = 5000  # milliseconds, PRAGMA busy_timeout

# Defaults for render_prompt_block().
DEFAULT_FACT_LIMIT = 25
DEFAULT_OBS_LIMIT = 10

# Security: cap on the length of any single fact or observation to prevent DoS.
MAX_MEMORY_CONTENT_CHARS = 32768

# Snapshot format version. Bump whenever the exported columns change so old
# snapshots are rejected loudly instead of importing into the wrong shape.
SNAPSHOT_VERSION = 1
SNAPSHOT_FACT_FIELDS = {
    "id",
    "kind",
    "key",
    "value",
    "source_session",
    "created_at",
    "updated_at",
}
SNAPSHOT_OBS_FIELDS = {
    "id",
    "summary",
    "evidence_session_id",
    "weight",
    "confidence",
    "created_at",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kind            TEXT    NOT NULL DEFAULT 'note',
    key             TEXT,
    value           TEXT    NOT NULL,
    source_session  TEXT,
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    summary             TEXT    NOT NULL,
    evidence_session_id TEXT,
    weight              REAL    NOT NULL DEFAULT 1.0,
    confidence          REAL    NOT NULL DEFAULT 0.5,
    created_at          INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_facts_kind ON facts(kind);
CREATE INDEX IF NOT EXISTS idx_facts_updated ON facts(updated_at);
CREATE INDEX IF NOT EXISTS idx_obs_weight ON observations(weight);
"""

# Flat column set for snapshot_to_csv(): facts and observations in one file,
# distinguished by the leading "type" column.
CSV_COLUMNS = [
    "type",
    "id",
    "kind",
    "key",
    "value",
    "source_session",
    "tags",
    "summary",
    "evidence_session_id",
    "weight",
    "confidence",
    "created_at",
    "updated_at",
]


@dataclass
class Fact:
    id: int
    kind: str
    key: str | None
    value: str
    source_session: str | None
    created_at: int
    updated_at: int
    # Stored as a JSON array (schema v2); exposed as a plain list. Defaulted so
    # positional construction and tag-less snapshots keep working.
    tags: list[str] = field(default_factory=list)


@dataclass
class Observation:
    id: int
    summary: str
    evidence_session_id: str | None
    weight: float
    confidence: float
    created_at: int


def _now() -> int:
    return int(time.time())


def _encode_tags(tags: Any) -> str | None:
    """Normalise a tag list to JSON text (None when there is nothing to store).

    Blank entries are dropped and duplicates collapsed, preserving first-seen
    order. Raises ValueError if given something that is not a list/tuple.
    """
    if not tags:
        return None
    if not isinstance(tags, (list, tuple)):
        raise ValueError(f"tags must be a list of strings, got {type(tags).__name__}")
    ordered: dict[str, None] = {}
    for raw in tags:
        cleaned = str(raw).strip()
        if cleaned:
            ordered.setdefault(cleaned, None)
    if not ordered:
        return None
    return json.dumps(list(ordered), ensure_ascii=False)


def _decode_tags(raw: Any) -> list[str]:
    """Decode the stored JSON tags column, tolerating junk by returning []."""
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return [str(t) for t in value] if isinstance(value, list) else []


def _fact_from_row(row: sqlite3.Row) -> Fact:
    data = dict(row)
    data["tags"] = _decode_tags(data.get("tags"))
    return Fact(**data)


def _render_facts(facts: Iterable[Fact]) -> list[str]:
    lines: list[str] = []
    for f in facts or []:
        prefix = f"[{f.kind}]"
        if f.key:
            lines.append(f"- {prefix} {f.key}: {f.value}")
        else:
            lines.append(f"- {prefix} {f.value}")
    return lines


def _validate_row(row: Any, required: set[str], label: str) -> None:
    if not isinstance(row, dict):
        raise ValueError(f"{label} row must be a dict, got {type(row).__name__}")
    missing = required - row.keys()
    if missing:
        raise ValueError(f"{label} row missing fields: {sorted(missing)}")


class MemoryStore:
    """A connection to the SQLite memory DB, opened for the object's lifetime."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else memory_db_path()
        # Restrict permissions on the data directory: rwx------ (0700)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(str(self.db_path.parent), 0o700)

        # Ensure the DB file itself is restricted: rw------- (0600)
        # If it doesn't exist, we create it with correct permissions.
        # ":memory:" is a special SQLite string, not a real path.
        is_mem = str(self.db_path) == ":memory:"
        if not is_mem and not self.db_path.exists():
            with contextlib.suppress(OSError):
                fd = os.open(str(self.db_path), os.O_WRONLY | os.O_CREAT, 0o600)
                os.close(fd)
        elif not is_mem:
            with contextlib.suppress(OSError):
                os.chmod(str(self.db_path), 0o600)

        self._conn = sqlite3.connect(self.db_path, timeout=DB_CONNECT_TIMEOUT)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(f"PRAGMA busy_timeout={DB_BUSY_TIMEOUT_MS}")
        # WAL is recorded in the file header and inherited by later opens. The
        # one-time flip briefly needs an exclusive lock that busy_timeout may not
        # cover, so a racing failure is tolerated — the default journal is safe.
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            logger.debug("WAL unavailable on %s; using default journal", self.db_path)
        self._migrate_schema()
        logger.debug("MemoryStore opened: %s", self.db_path)

    # -- lifecycle --------------------------------------------------------

    def close(self) -> None:
        self._conn.close()
        logger.debug("MemoryStore closed: %s", self.db_path)

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def healthcheck(self) -> str:
        """Return 'ok' on a clean DB, otherwise the integrity_check messages."""
        rows = self._conn.execute("PRAGMA integrity_check").fetchall()
        if not rows:
            return "unknown"
        messages = [str(r[0]) for r in rows]
        if messages == ["ok"]:
            return "ok"
        return "; ".join(messages)

    # -- migrations -------------------------------------------------------

    def _migrate_schema(self) -> None:
        with contextlib.suppress(sqlite3.OperationalError):
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "version INTEGER PRIMARY KEY, migrated_at INTEGER NOT NULL)"
            )
            self._conn.commit()

        migrations = {1: self._migration_v1, 2: self._migration_v2, 3: self._migration_v3}
        try:
            # BEGIN IMMEDIATE serialises migration across parallel openers.
            self._conn.execute("BEGIN IMMEDIATE")
            row = self._conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
            current = int(row["v"]) if row and row["v"] is not None else 0

            # A DB created before schema_version existed already has the v1
            # tables; record it as v1 so we don't re-run the create.
            if current == 0:
                existing = self._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='facts'"
                ).fetchone()
                if existing is not None:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO schema_version (version, migrated_at) VALUES (?, ?)",
                        (1, _now()),
                    )
                    current = 1

            for version in sorted(migrations):
                if version > current:
                    logger.info("Migrating memory schema to v%d", version)
                    migrations[version]()
                    self._conn.execute(
                        "INSERT OR IGNORE INTO schema_version (version, migrated_at) VALUES (?, ?)",
                        (version, _now()),
                    )
            self._conn.commit()
        except Exception:
            with contextlib.suppress(sqlite3.OperationalError):
                self._conn.rollback()
            logger.exception("Schema migration failed")
            raise

    def _migration_v1(self) -> None:
        # Run statements one at a time; executescript() would force a commit.
        for statement in SCHEMA.split(";"):
            stripped = statement.strip()
            if stripped:
                self._conn.execute(stripped)

    def _migration_v2(self) -> None:
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(facts)")}
        if "tags" not in cols:
            self._conn.execute("ALTER TABLE facts ADD COLUMN tags TEXT")

    def _migration_v3(self) -> None:
        # Ensure observations exists (a very old DB may have had only facts).
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS observations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, summary TEXT NOT NULL, "
            "evidence_session_id TEXT, weight REAL NOT NULL DEFAULT 1.0, "
            "confidence REAL NOT NULL DEFAULT 0.5, created_at INTEGER NOT NULL)"
        )
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(observations)")}
        if "confidence" not in cols:
            self._conn.execute(
                "ALTER TABLE observations ADD COLUMN confidence REAL NOT NULL DEFAULT 0.5"
            )

    # -- facts ------------------------------------------------------------

    def add_fact(
        self,
        value: str,
        *,
        kind: str = "note",
        key: str | None = None,
        source_session: str | None = None,
        tags: list[str] | None = None,
    ) -> int:
        # Security: redact secrets and truncate before storing.
        clean_value = redact_secrets(value)[:MAX_MEMORY_CONTENT_CHARS]
        clean_kind = redact_secrets(kind)
        clean_key = redact_secrets(key) if key else None
        clean_tags = [redact_secrets(t) for t in tags] if tags is not None else None
        clean_source_session = redact_secrets(source_session) if source_session else None

        now = _now()
        cur = self._conn.execute(
            "INSERT INTO facts (kind, key, value, source_session, created_at, "
            "updated_at, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                clean_kind,
                clean_key,
                clean_value,
                clean_source_session,
                now,
                now,
                _encode_tags(clean_tags),
            ),
        )
        self._conn.commit()
        return cast(int, cur.lastrowid)

    def list_facts(
        self,
        limit: int = 100,
        *,
        after_ts: int | None = None,
        before_ts: int | None = None,
    ) -> list[Fact]:
        """Return facts ordered newest-first.

        Optional ``after_ts`` / ``before_ts`` are inclusive Unix timestamps
        that filter on ``created_at``.
        """
        clauses: list[str] = []
        params: list[int] = []
        if after_ts is not None:
            clauses.append("created_at >= ?")
            params.append(after_ts)
        if before_ts is not None:
            clauses.append("created_at <= ?")
            params.append(before_ts)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        rows = self._conn.execute(
            f"SELECT * FROM facts {where} ORDER BY updated_at DESC LIMIT ?",  # nosec B608
            params,
        ).fetchall()
        return [_fact_from_row(r) for r in rows]

    def get_fact_by_key(self, kind: str, key: str) -> Fact | None:
        row = self._conn.execute(
            "SELECT * FROM facts WHERE kind = ? AND key = ? ORDER BY updated_at DESC LIMIT 1",
            (kind, key),
        ).fetchone()
        return _fact_from_row(row) if row else None

    def delete_facts_by_key(self, kind: str, key: str) -> int:
        cur = self._conn.execute("DELETE FROM facts WHERE kind = ? AND key = ?", (kind, key))
        self._conn.commit()
        return cur.rowcount

    def search_by_tag(self, tag: str, limit: int = 50) -> list[Fact]:
        """Return facts carrying the exact tag, newest first.

        Matching goes through ``json_each`` so it compares decoded tag values
        rather than doing a substring LIKE over the raw JSON text (which would
        give false positives).
        """
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE tags IS NOT NULL AND EXISTS ("
            "SELECT 1 FROM json_each(tags) WHERE value = ?) "
            "ORDER BY updated_at DESC LIMIT ?",
            (tag.strip(), limit),
        ).fetchall()
        return [_fact_from_row(r) for r in rows]

    def forget_fact(self, fact_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def update_fact(
        self,
        fact_id: int,
        value: str,
        *,
        tags: list[str] | None = None,
    ) -> bool:
        """Update a fact's value (and tags if given). Returns False if absent.

        ``updated_at`` is always refreshed; tags are only rewritten when
        explicitly supplied. Raises ValueError on an empty value.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError("value must be a non-empty string")

        # Security: redact secrets and truncate before storing.
        clean_value = redact_secrets(value)[:MAX_MEMORY_CONTENT_CHARS]
        clean_tags = [redact_secrets(t) for t in tags] if tags is not None else None
        now = _now()
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            if tags is not None:
                cur = self._conn.execute(
                    "UPDATE facts SET value = ?, tags = ?, updated_at = ? WHERE id = ?",
                    (clean_value, _encode_tags(clean_tags), now, fact_id),
                )
            else:
                cur = self._conn.execute(
                    "UPDATE facts SET value = ?, updated_at = ? WHERE id = ?",
                    (clean_value, now, fact_id),
                )
            updated = cur.rowcount > 0
            self._conn.commit()
        except Exception:
            with contextlib.suppress(sqlite3.OperationalError):
                self._conn.rollback()
            raise
        return updated

    # -- observations -----------------------------------------------------

    def add_observation(
        self,
        summary: str,
        *,
        evidence_session_id: str | None = None,
        weight: float = 1.0,
        confidence: float = 0.5,
    ) -> int:
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Observation summary must be a non-empty string.")

        # Security: redact secrets and truncate before storing.
        clean_summary = redact_secrets(summary)[:MAX_MEMORY_CONTENT_CHARS]
        clean_sid = redact_secrets(evidence_session_id) if evidence_session_id else None
        cur = self._conn.execute(
            "INSERT INTO observations (summary, evidence_session_id, weight, "
            "confidence, created_at) VALUES (?, ?, ?, ?, ?)",
            (clean_summary, clean_sid, weight, confidence, _now()),
        )
        self._conn.commit()
        return cast(int, cur.lastrowid)

    def forget_observation(self, obs_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM observations WHERE id = ?", (obs_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def top_observations(self, limit: int = 20) -> list[Observation]:
        rows = self._conn.execute(
            "SELECT * FROM observations ORDER BY weight DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [Observation(**dict(r)) for r in rows]

    # -- search & rendering ----------------------------------------------

    def search_memory(self, query: str, limit: int = 50) -> tuple[list[Fact], list[Observation]]:
        """Substring-search both tables; returns (matching facts, observations)."""
        # Escape LIKE wildcards with '=' so a literal % or _ in the query does
        # not act as a wildcard.
        escaped = query.replace("=", "==").replace("%", "=%").replace("_", "=_")
        pattern = f"%{escaped}%"
        fact_rows = self._conn.execute(
            "SELECT * FROM facts WHERE value LIKE ? ESCAPE '=' OR key LIKE ? ESCAPE '=' "
            "OR kind LIKE ? ESCAPE '=' ORDER BY updated_at DESC LIMIT ?",
            (pattern, pattern, pattern, limit),
        ).fetchall()
        obs_rows = self._conn.execute(
            "SELECT * FROM observations WHERE summary LIKE ? ESCAPE '=' "
            "ORDER BY weight DESC, created_at DESC LIMIT ?",
            (pattern, limit),
        ).fetchall()
        return (
            [_fact_from_row(r) for r in fact_rows],
            [Observation(**dict(r)) for r in obs_rows],
        )

    def render_prompt_block(
        self,
        *,
        fact_limit: int = DEFAULT_FACT_LIMIT,
        obs_limit: int = DEFAULT_OBS_LIMIT,
    ) -> str:
        """Render recent memory as a markdown block for a system prompt."""
        facts = self.list_facts(limit=fact_limit)
        obs = self.top_observations(limit=obs_limit)
        if not facts and not obs:
            return ""
        lines = ["## SakThai personal memory"]
        if facts:
            lines.append("### Facts about the user")
            lines.extend(_render_facts(facts))
        if obs:
            lines.append("### Observations")
            lines.extend(f"- {o.summary}" for o in obs)
        return "\n".join(lines)

    # -- maintenance ------------------------------------------------------

    def consolidate_facts(self, age_seconds: int = 86400) -> int:
        """Fold facts older than ``age_seconds`` into one observation.

        The insert and delete run in a single transaction so the store can never
        end up with the summary but not the deletions (or vice versa). Returns
        the number of facts folded.
        """
        threshold = _now() - age_seconds
        rows = self._conn.execute(
            "SELECT value FROM facts WHERE updated_at < ?", (threshold,)
        ).fetchall()
        if not rows:
            return 0
        # Security: redact and truncate individual values if they somehow escaped earlier.
        values = [redact_secrets(r["value"])[:MAX_MEMORY_CONTENT_CHARS] for r in rows]
        summary = f"Consolidated {len(values)} facts: " + "; ".join(values)

        # Final safety check on the combined summary.
        summary = redact_secrets(summary)[:MAX_MEMORY_CONTENT_CHARS]
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "INSERT INTO observations (summary, evidence_session_id, weight, "
                "confidence, created_at) VALUES (?, ?, ?, ?, ?)",
                (summary, None, 0.5, 0.5, _now()),
            )
            self._conn.execute("DELETE FROM facts WHERE updated_at < ?", (threshold,))
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return len(values)

    def deduplicate_facts(
        self, *, detailed: bool = False, dry_run: bool = False
    ) -> int | list[Fact]:
        """Drop duplicate facts, keeping the most recently updated of each group.

        Keyed facts group by (kind, key); key-less facts group by (kind, value).
        Returns the deleted Facts when ``detailed`` else the count. With
        ``dry_run`` nothing is deleted but the would-be deletions are reported.
        """
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            keyed = self._conn.execute(
                "SELECT * FROM facts WHERE key IS NOT NULL AND id NOT IN ("
                "SELECT id FROM facts f2 WHERE f2.kind = facts.kind AND f2.key = facts.key "
                "ORDER BY f2.updated_at DESC, f2.id DESC LIMIT 1)"
            ).fetchall()
            keyless = self._conn.execute(
                "SELECT * FROM facts WHERE key IS NULL AND id NOT IN ("
                "SELECT id FROM facts f2 WHERE f2.kind = facts.kind AND f2.key IS NULL "
                "AND f2.value = facts.value ORDER BY f2.updated_at DESC, f2.id DESC LIMIT 1)"
            ).fetchall()
            deleted = [_fact_from_row(r) for r in keyed + keyless]
            if deleted and not dry_run:
                ids = [f.id for f in deleted]
                placeholders = ",".join("?" for _ in ids)
                self._conn.execute(
                    f"DELETE FROM facts WHERE id IN ({placeholders})",  # nosec B608 — placeholders are '?'
                    ids,
                )
            self._conn.commit()
            return deleted if detailed else len(deleted)
        except Exception:
            self._conn.rollback()
            raise

    def deduplicate_observations(
        self, *, detailed: bool = False, dry_run: bool = False
    ) -> int | list[Observation]:
        """Drop duplicate observations sharing a summary.

        Keeps the highest weight, breaking ties by confidence, then created_at,
        then id. Returns deleted Observations when ``detailed`` else the count.
        """
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            rows = self._conn.execute(
                "SELECT * FROM observations WHERE id NOT IN ("
                "SELECT id FROM observations o2 WHERE o2.summary = observations.summary "
                "ORDER BY o2.weight DESC, o2.confidence DESC, o2.created_at DESC, "
                "o2.id DESC LIMIT 1)"
            ).fetchall()
            deleted = [Observation(**dict(r)) for r in rows]
            if deleted and not dry_run:
                ids = [o.id for o in deleted]
                placeholders = ",".join("?" for _ in ids)
                self._conn.execute(
                    f"DELETE FROM observations WHERE id IN ({placeholders})",  # nosec B608
                    ids,
                )
            self._conn.commit()
            return deleted if detailed else len(deleted)
        except Exception:
            self._conn.rollback()
            raise

    # -- reporting --------------------------------------------------------

    def get_dashboard_aggregates(
        self,
        table: str,
        limit: int,
        start_ts: int,
        week_ago_ts: int,
    ) -> dict[str, Any]:
        """Return KPI counts and binned growth data for the dashboard in one pass.

        Aggregation happens in SQL to avoid fetching and parsing thousands of
        rows in Python. Capped by ``limit`` to match legacy behavior.
        """
        if table not in ("facts", "observations"):
            raise ValueError(f"Invalid table: {table}")

        # We use a CTE to apply the limit once, then aggregate over that subset.
        # ``table`` is allowlist-validated above, so the interpolation is safe.
        query = f"""
            WITH subset AS (
                SELECT created_at FROM {table} LIMIT ?
            )
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as this_week,
                SUM(CASE WHEN created_at <= ? THEN 1 ELSE 0 END) as before_start
            FROM subset
        """  # nosec B608
        row = self._conn.execute(query, (limit, week_ago_ts, start_ts)).fetchone()
        res: dict[str, Any] = {
            "total": row["total"] or 0,
            "this_week": row["this_week"] or 0,
            "before_start": row["before_start"] or 0,
            "bins": [],
        }

        # Growth bins: one per day for 30 days.
        days = 30
        bins = [0] * days
        bin_query = f"""
            WITH subset AS (
                SELECT created_at FROM {table} LIMIT ?
            )
            SELECT
                CAST((created_at - ? - 1) / 86400 AS INTEGER) as bin,
                COUNT(*) as n
            FROM subset
            WHERE created_at > ? AND created_at <= ?
            GROUP BY bin
        """  # nosec B608
        rows = self._conn.execute(
            bin_query, (limit, start_ts, start_ts, start_ts + days * 86400)
        ).fetchall()
        for r in rows:
            idx = r["bin"]
            if 0 <= idx < days:
                bins[idx] = r["n"]
        res["bins"] = bins
        return res

    def get_fact_kind_counts(self, limit: int) -> dict[str, int]:
        """Return counts of facts grouped by kind, capped by ``limit``."""
        query = """
            WITH subset AS (
                SELECT kind FROM facts LIMIT ?
            )
            SELECT kind, COUNT(*) as n FROM subset GROUP BY kind ORDER BY n DESC, kind
        """
        rows = self._conn.execute(query, (limit,)).fetchall()
        return {r["kind"]: r["n"] for r in rows}

    def stats(self) -> dict[str, Any]:
        """Aggregate counts and distributions. Safe on an empty DB."""
        c = self._conn
        n_facts = c.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        n_obs = c.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        by_kind = {
            r["kind"]: r["n"]
            for r in c.execute(
                "SELECT kind, COUNT(*) AS n FROM facts GROUP BY kind ORDER BY n DESC, kind"
            ).fetchall()
        }
        # SQL-based tag counting is ~2.6x faster than Python loop (Bolt optimization)
        tag_counts = {
            r["tag"]: r["n"]
            for r in c.execute(
                "SELECT j.value AS tag, COUNT(*) AS n "
                "FROM facts, json_each(facts.tags) AS j "
                "WHERE facts.tags IS NOT NULL AND json_valid(facts.tags) "
                "GROUP BY tag"
            ).fetchall()
        }
        f_min, f_max = c.execute("SELECT MIN(created_at), MAX(created_at) FROM facts").fetchone()
        o_min, o_max, avg_w, avg_c = c.execute(
            "SELECT MIN(created_at), MAX(created_at), AVG(weight), AVG(confidence) "
            "FROM observations"
        ).fetchone()
        return {
            "db_path": str(self.db_path),
            "facts": {
                "total": n_facts,
                "by_kind": by_kind,
                "oldest": f_min,
                "newest": f_max,
            },
            "observations": {
                "total": n_obs,
                "oldest": o_min,
                "newest": o_max,
                "avg_weight": round(avg_w, 3) if avg_w is not None else None,
                "avg_confidence": round(avg_c, 3) if avg_c is not None else None,
            },
            "tags": dict(sorted(tag_counts.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))),
        }

    # -- import / export --------------------------------------------------

    def export_to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of all facts and observations."""
        fact_rows = self._conn.execute(
            "SELECT id, kind, key, value, source_session, created_at, updated_at, tags "
            "FROM facts ORDER BY id"
        ).fetchall()
        obs_rows = self._conn.execute(
            "SELECT id, summary, evidence_session_id, weight, confidence, created_at "
            "FROM observations ORDER BY id"
        ).fetchall()
        return {
            "version": SNAPSHOT_VERSION,
            "exported_at": _now(),
            "db_path": str(self.db_path),
            "facts": [asdict(_fact_from_row(r)) for r in fact_rows],
            "observations": [asdict(Observation(**dict(r))) for r in obs_rows],
        }

    def import_from_dict(self, data: dict[str, Any], *, mode: str = "merge") -> tuple[int, int]:
        """Load a snapshot. Returns (n_facts, n_observations) imported.

        mode="merge" appends rows with fresh IDs; mode="replace" wipes
        both tables and reinserts preserving original IDs. The whole import runs
        in one transaction, so a malformed snapshot leaves the DB untouched.
        """
        if mode not in ("merge", "replace"):
            raise ValueError(f"mode must be 'merge' or 'replace', got {mode!r}")
        if not isinstance(data, dict):
            raise ValueError("snapshot must be a dict")
        if data.get("version") != SNAPSHOT_VERSION:
            raise ValueError(
                f"unsupported snapshot version: {data.get('version')!r} "
                f"(expected {SNAPSHOT_VERSION})"
            )
        facts = data.get("facts")
        obs = data.get("observations")
        if not isinstance(facts, list) or not isinstance(obs, list):
            raise ValueError("snapshot must contain list 'facts' and 'observations'")

        # Validate everything before touching the DB.
        for row in facts:
            _validate_row(row, SNAPSHOT_FACT_FIELDS, "fact")
        for row in obs:
            _validate_row(row, SNAPSHOT_OBS_FIELDS, "observation")

        def fact_to_tuple(f: dict[str, Any], include_id: bool) -> tuple[Any, ...]:
            # Security: redact secrets and truncate during import.
            clean_value = redact_secrets(str(f["value"]))[:MAX_MEMORY_CONTENT_CHARS]
            clean_kind = redact_secrets(str(f["kind"]))
            clean_key = redact_secrets(str(f["key"])) if f.get("key") else None
            clean_tags = (
                [redact_secrets(str(t)) for t in f["tags"]]
                if isinstance(f.get("tags"), list)
                else None
            )
            clean_source_session = (
                redact_secrets(str(f["source_session"])) if f.get("source_session") else None
            )

            t = (
                clean_kind,
                clean_key,
                clean_value,
                clean_source_session,
                f["created_at"],
                f["updated_at"],
                _encode_tags(clean_tags),
            )
            return (f["id"],) + t if include_id else t

        def obs_to_tuple(o: dict[str, Any], include_id: bool) -> tuple[Any, ...]:
            # Security: redact secrets and truncate during import.
            clean_summary = redact_secrets(str(o["summary"]))[:MAX_MEMORY_CONTENT_CHARS]
            clean_sid = (
                redact_secrets(str(o["evidence_session_id"]))
                if o.get("evidence_session_id")
                else None
            )
            t = (
                clean_summary,
                clean_sid,
                o["weight"],
                o["confidence"],
                o["created_at"],
            )
            return (o["id"],) + t if include_id else t

        try:
            self._conn.execute("BEGIN IMMEDIATE")
            if mode == "replace":
                self._conn.execute("DELETE FROM facts")
                self._conn.execute("DELETE FROM observations")
                with contextlib.suppress(sqlite3.OperationalError):
                    self._conn.execute(
                        "DELETE FROM sqlite_sequence WHERE name IN ('facts', 'observations')"
                    )

                self._conn.executemany(
                    "INSERT INTO facts (id, kind, key, value, source_session, "
                    "created_at, updated_at, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [fact_to_tuple(f, True) for f in facts],
                )
                self._conn.executemany(
                    "INSERT INTO observations (id, summary, evidence_session_id, "
                    "weight, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    [obs_to_tuple(o, True) for o in obs],
                )
            else:  # merge
                self._conn.executemany(
                    "INSERT INTO facts (kind, key, value, source_session, "
                    "created_at, updated_at, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [fact_to_tuple(f, False) for f in facts],
                )
                self._conn.executemany(
                    "INSERT INTO observations (summary, evidence_session_id, "
                    "weight, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
                    [obs_to_tuple(o, False) for o in obs],
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return (len(facts), len(obs))


def snapshot_to_jsonl(snapshot: dict[str, Any]) -> str:
    """Render an export snapshot as newline-delimited JSON, one row per line."""
    lines: list[str] = []
    for f in snapshot.get("facts", []):
        lines.append(json.dumps({"type": "fact", **f}, ensure_ascii=False))
    for o in snapshot.get("observations", []):
        lines.append(json.dumps({"type": "observation", **o}, ensure_ascii=False))
    return "\n".join(lines) + ("\n" if lines else "")


def snapshot_to_csv(snapshot: dict[str, Any]) -> str:
    """Render an export snapshot as one flat CSV (tags joined by commas)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for f in snapshot.get("facts", []):
        row = dict(f)
        row["type"] = "fact"
        if isinstance(row.get("tags"), list):
            row["tags"] = ",".join(row["tags"])
        writer.writerow(row)
    for o in snapshot.get("observations", []):
        row = dict(o)
        row["type"] = "observation"
        writer.writerow(row)
    return buf.getvalue()
