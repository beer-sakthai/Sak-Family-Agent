"""Operational daemons for SakTan: SQLite WAL maintenance and Fleet Drift Watchdog.

Provides automated, idle-time WAL checkpoints/vacuums to keep memory databases compact,
and continuous fleet drift monitoring across all 6 House of Sak personas.
"""

from __future__ import annotations

import logging
import sqlite3
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
