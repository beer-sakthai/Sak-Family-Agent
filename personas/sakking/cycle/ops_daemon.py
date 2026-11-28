"""Operational daemons for SakTan: SQLite WAL maintenance and Fleet Drift Watchdog.

Provides automated, idle-time WAL checkpoints/vacuums to keep memory databases compact,
and continuous fleet drift monitoring across all 6 House of Sak personas.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import sakthai_home

logger = logging.getLogger(__name__)

ALL_PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")


class SQLiteWALVacuumDaemon:
    """Daemon responsible for inspecting and compacting family SQLite memory stores."""

    def __init__(self, db_paths: list[Path] | None = None) -> None:
        self.db_paths = db_paths or self._discover_db_paths()

    def _discover_db_paths(self) -> list[Path]:
        home = sakthai_home()
        paths: list[Path] = []
        root_db = home / "memory.db"
        if root_db.is_file():
            paths.append(root_db)

        for p in ALL_PERSONAS:
            pdb = home / p / "memory.db"
            if pdb.is_file():
                paths.append(pdb)
            # Also check user home ~/.<persona>/memory.db
            user_pdb = Path.home() / f".{p}" / "memory.db"
            if user_pdb.is_file() and user_pdb not in paths:
                paths.append(user_pdb)
        return paths

    def vacuum_all(self, force: bool = False, threshold_bytes: int = 1_000_000) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        total_reclaimed = 0

        for db in self.db_paths:
            if not db.is_file():
                continue
            wal_file = Path(f"{db}-wal")
            initial_db_size = db.stat().st_size
            initial_wal_size = wal_file.stat().st_size if wal_file.is_file() else 0
            initial_total = initial_db_size + initial_wal_size

            should_compact = force or (initial_wal_size >= threshold_bytes)
            if not should_compact:
                results.append(
                    {
                        "database": str(db),
                        "action": "skipped",
                        "reason": f"WAL size {initial_wal_size} below threshold {threshold_bytes}",
                    }
                )
                continue

            try:
                conn = sqlite3.connect(str(db))
                cur = conn.cursor()
                cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                checkpoint_result = cur.fetchone()
                cur.execute("VACUUM;")
                conn.close()

                final_db_size = db.stat().st_size
                final_wal_size = wal_file.stat().st_size if wal_file.is_file() else 0
                final_total = final_db_size + final_wal_size
                reclaimed = max(0, initial_total - final_total)
                total_reclaimed += reclaimed

                results.append(
                    {
                        "database": str(db),
                        "action": "compacted",
                        "checkpoint_status": "success",
                        "checkpoint_result": list(checkpoint_result) if checkpoint_result else None,
                        "initial_bytes": initial_total,
                        "final_bytes": final_total,
                        "bytes_reclaimed": reclaimed,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to vacuum database %s: %s", db, exc)
                results.append(
                    {
                        "database": str(db),
                        "action": "error",
                        "checkpoint_status": "failed",
                        "error": str(exc),
                    }
                )

        return {
            "status": "ok",
            "databases_scanned": len(self.db_paths),
            "total_bytes_reclaimed": total_reclaimed,
            "results": results,
        }


class FleetDriftWatchdog:
    """Monitors configuration, skills, and memory drift across all 6 personas."""

    def __init__(self, repo_root: Path | None = None) -> None:
        if repo_root is not None:
            self.repo_root = repo_root
        else:
            # Walk up to find repo root
            self.repo_root = Path(__file__).resolve().parents[3]

    def check_drift(self) -> dict[str, Any]:
        persona_reports: dict[str, Any] = {}
        anomalies: list[str] = []
        drift_points = 0

        personas_dir = self.repo_root / "personas"

        for p in ALL_PERSONAS:
            p_dir = personas_dir / p
            if not p_dir.is_dir():
                anomalies.append(f"Persona directory missing: personas/{p}")
                drift_points += 5
                continue

            soul_file = p_dir / "SOUL.md"
            config_file = p_dir / "config" / "config.yaml"
            mcp_file = p_dir / "config" / "mcp.json"
            skills_dir = p_dir / "skills"

            has_soul = soul_file.is_file()
            has_config = config_file.is_file()
            has_mcp = mcp_file.is_file()
            skill_count = len(list(skills_dir.glob("Sak*"))) if skills_dir.is_dir() else 0

            if not has_soul:
                anomalies.append(f"{p}: Missing SOUL.md")
                drift_points += 2
            if not has_config:
                anomalies.append(f"{p}: Missing config/config.yaml")
                drift_points += 2
            if not has_mcp:
                anomalies.append(f"{p}: Missing config/mcp.json")
                drift_points += 1

            persona_reports[p] = {
                "exists": True,
                "has_soul": has_soul,
                "has_config": has_config,
                "has_mcp": has_mcp,
                "skill_count": skill_count,
            }

        drift_score = min(1.0, drift_points / 20.0)

        return {
            "status": "ok",
            "drift_score": round(drift_score, 2),
            "healthy": drift_score == 0.0,
            "anomalies_count": len(anomalies),
            "anomalies": anomalies,
            "personas": persona_reports,
        }


class FamilyHeartbeatDaemon:
    """Daemon responsible for recording and querying periodic persona heartbeat telemetry."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is not None:
            self.db_path = db_path
        else:
            self.db_path = sakthai_home() / "memory" / "family_heartbeat.db"
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS heartbeats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp REAL NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_heartbeats_persona ON heartbeats(persona);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp ON heartbeats(timestamp);"
            )
            conn.commit()
        finally:
            conn.close()

    def record_heartbeat(
        self,
        persona: str,
        status: str = "ok",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a heartbeat entry for a persona."""
        ts = time.time()
        details_str = json.dumps(details or {})
        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO heartbeats (persona, status, details, timestamp) VALUES (?, ?, ?, ?)",
                (persona.strip().lower(), status, details_str, ts),
            )
            record_id = cur.lastrowid or 0
            conn.commit()
        finally:
            conn.close()

        return {
            "id": record_id,
            "persona": persona.strip().lower(),
            "status": status,
            "timestamp": ts,
            "details": details or {},
        }

    def get_recent_heartbeats(
        self,
        persona: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Retrieve recent heartbeat entries, optionally filtered by persona."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            if persona:
                cur.execute(
                    "SELECT id, persona, status, details, timestamp FROM heartbeats "
                    "WHERE persona = ? ORDER BY timestamp DESC LIMIT ?",
                    (persona.strip().lower(), limit),
                )
            else:
                cur.execute(
                    "SELECT id, persona, status, details, timestamp FROM heartbeats "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = cur.fetchall()
        finally:
            conn.close()

        results: list[dict[str, Any]] = []
        for r in rows:
            try:
                parsed_details = json.loads(r[3]) if r[3] else {}
            except Exception:
                parsed_details = {}
            results.append(
                {
                    "id": r[0],
                    "persona": r[1],
                    "status": r[2],
                    "details": parsed_details,
                    "timestamp": r[4],
                }
            )
        return results

    def get_fleet_health_summary(self) -> dict[str, Any]:
        """Aggregate the latest heartbeat status for each family persona."""
        summary: dict[str, Any] = {}
        for p in ALL_PERSONAS:
            recent = self.get_recent_heartbeats(persona=p, limit=1)
            if recent:
                summary[p] = {
                    "status": recent[0]["status"],
                    "last_seen": recent[0]["timestamp"],
                    "details": recent[0]["details"],
                }
            else:
                summary[p] = {
                    "status": "unseen",
                    "last_seen": None,
                    "details": {},
                }
        return {
            "fleet_size": len(ALL_PERSONAS),
            "summary": summary,
        }


class TelegramDigestScheduler:
    """Scheduler hooks for Telegram morning and evening family operational digests."""

    def __init__(self, morning_hour: int = 8, evening_hour: int = 21) -> None:
        self.morning_hour = morning_hour
        self.evening_hour = evening_hour

    def should_send_digest(self, current_dt: datetime | None = None) -> dict[str, Any]:
        """Check whether the current time matches morning or evening digest schedule."""
        dt = current_dt or datetime.now(UTC)
        hour = dt.hour
        if hour == self.morning_hour:
            return {"should_send": True, "digest_type": "morning", "hour": hour}
        if hour == self.evening_hour:
            return {"should_send": True, "digest_type": "evening", "hour": hour}
        return {"should_send": False, "digest_type": None, "hour": hour}

    def build_digest_payload(
        self,
        persona_reports: dict[str, Any] | None = None,
        heartbeats: list[dict[str, Any]] | None = None,
        digest_type: str = "morning",
    ) -> dict[str, Any]:
        """Build structured Telegram notification markdown payload."""
        now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        if digest_type == "morning":
            header = f"🌅 **House of Sak — Morning Briefing** ({now_str})"
        else:
            header = f"🌙 **House of Sak — Evening Wrap-Up** ({now_str})"

        lines = [header, ""]
        if persona_reports:
            lines.append("### Fleet Persona Status:")
            for persona, rep in persona_reports.items():
                status_icon = "🟢" if rep.get("healthy", True) else "🟡"
                lines.append(
                    f"- {status_icon} **{persona}**: skills={rep.get('skill_count', 0)}, "
                    f"soul={rep.get('has_soul', False)}"
                )
            lines.append("")

        if heartbeats:
            lines.append("### Recent Telemetry:")
            for hb in heartbeats[:5]:
                lines.append(f"- `[{hb.get('persona', '?')}]`: {hb.get('status', 'ok')}")
            lines.append("")

        lines.append("Ready for commands · Type `sakthai status` for full diagnostics.")
        message_text = "\n".join(lines)

        return {
            "digest_type": digest_type,
            "timestamp": now_str,
            "text": message_text,
            "channel": "telegram",
        }
