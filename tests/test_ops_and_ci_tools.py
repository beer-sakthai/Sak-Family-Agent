"""Unit tests for SakJules CI feedback synthesizer and SakTan ops daemons in agent/tools.py."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC
from pathlib import Path
from typing import Any

from sakthai.agent.tools import Tool, tool_by_name
from sakthai.cycle.ops_daemon import (
    FamilyHeartbeatDaemon,
    FleetDriftWatchdog,
    SQLiteWALVacuumDaemon,
    TelegramDigestScheduler,
)
from sakthai.memory.store import MemoryStore


def test_synthesize_ci_feedback_metadata() -> None:
    tool = tool_by_name("synthesize_ci_feedback")
    assert tool is not None
    assert isinstance(tool, Tool)
    assert tool.name == "synthesize_ci_feedback"
    schema = tool.schema()
    assert "ci_log" in schema["input_schema"]["properties"]
    assert "review_comments" in schema["input_schema"]["properties"]


def test_synthesize_ci_feedback_handler(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("synthesize_ci_feedback")
    assert tool is not None

    sample_log = """
    FAILED tests/test_agent.py::test_run - AssertionError: expected True got False
    personas/sakthai/agent/tools.py:120: error: Incompatible types in assignment [assignment]
    personas/sakthai/web/server.py:45:1: E501 line too long (105 > 100 characters)
    Total coverage: 95.2% (required >= 96.0%)
    """
    review_comments = [
        "Please fix the bandit security warning regarding urllib without ssl validation.",
    ]

    out = tool.handler({"ci_log": sample_log, "review_comments": review_comments}, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["total_findings"] >= 4
    categories = [f["category"] for f in data["findings"]]
    assert "test_failure" in categories
    assert "type_error" in categories
    assert "lint_style" in categories
    assert "coverage_drop" in categories
    assert "security_guardrail" in categories
    assert len(data["action_checklist"]) >= 4

    # Verify memory recorded
    facts = store.search_by_tag("ci-feedback", limit=5)
    assert len(facts) > 0


def test_sqlite_wal_vacuum_daemon(tmp_path: Any) -> None:
    # Create test sqlite db with active wal mode
    db_path = tmp_path / "test_memory.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE test_data (id INTEGER PRIMARY KEY, content TEXT);")
    for _ in range(100):
        conn.execute("INSERT INTO test_data (content) VALUES (?)", ("x" * 2000,))
    conn.commit()
    conn.close()

    daemon = SQLiteWALVacuumDaemon(db_paths=[db_path])
    res = daemon.vacuum_all(force=True)
    assert res["status"] == "ok"
    assert res["databases_scanned"] == 1
    assert len(res["results"]) == 1
    assert res["results"][0]["checkpoint_status"] == "success"


def test_fleet_drift_watchdog(tmp_path: Any) -> None:
    watchdog = FleetDriftWatchdog()
    res = watchdog.check_drift()
    assert res["status"] == "ok"
    assert "personas" in res
    assert "drift_score" in res
    assert len(res["personas"]) == 6
    # Core personas exist
    for p in ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan"):
        assert p in res["personas"]


def test_vacuum_family_databases_tool(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("vacuum_family_databases")
    assert tool is not None

    out = tool.handler({"force": True}, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert "databases_scanned" in data


def test_check_fleet_drift_tool(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("check_fleet_drift")
    assert tool is not None

    out = tool.handler({"verbose": True}, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert "drift_score" in data


def test_sqlite_wal_vacuum_skipped_when_below_threshold(tmp_path: Any) -> None:
    db_path = tmp_path / "test_skip.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t (id INT);")
    conn.commit()
    conn.close()

    daemon = SQLiteWALVacuumDaemon(db_paths=[db_path, tmp_path / "non_existent.db"])
    res = daemon.vacuum_all(force=False, threshold_bytes=100_000_000)
    assert res["status"] == "ok"
    assert res["results"][0]["action"] == "skipped"


def test_sqlite_wal_vacuum_handles_error(tmp_path: Any) -> None:
    bad_db = tmp_path / "bad.db"
    bad_db.write_text("not a sqlite database", encoding="utf-8")

    daemon = SQLiteWALVacuumDaemon(db_paths=[bad_db])
    res = daemon.vacuum_all(force=True)
    assert res["status"] == "ok"
    assert res["results"][0]["action"] == "error"
    assert res["results"][0]["checkpoint_status"] == "failed"


def test_sqlite_wal_vacuum_discover_paths(tmp_path: Any, monkeypatch: Any) -> None:
    fake_home = tmp_path / ".sakthai"
    fake_home.mkdir()
    (fake_home / "memory.db").touch()
    (fake_home / "sakking").mkdir()
    (fake_home / "sakking" / "memory.db").touch()

    # Also test user home ~/.saktan/memory.db
    fake_user_home = tmp_path / "user_home"
    (fake_user_home / ".saktan").mkdir(parents=True)
    (fake_user_home / ".saktan" / "memory.db").touch()
    monkeypatch.setattr(Path, "home", lambda: fake_user_home)

    monkeypatch.setenv("SAKTHAI_HOME", str(fake_home))
    daemon = SQLiteWALVacuumDaemon()
    discovered_str = [str(p) for p in daemon.db_paths]
    assert str(fake_home / "memory.db") in discovered_str
    assert str(fake_home / "sakking" / "memory.db") in discovered_str
    assert str(fake_user_home / ".saktan" / "memory.db") in discovered_str


def test_fleet_drift_watchdog_detects_anomalies(tmp_path: Any) -> None:
    # Create fake repo root with incomplete personas
    fake_root = tmp_path / "repo"
    personas_dir = fake_root / "personas"
    personas_dir.mkdir(parents=True)

    # Missing SOUL, config, mcp in sakthai
    (personas_dir / "sakthai").mkdir()

    watchdog = FleetDriftWatchdog(repo_root=fake_root)
    res = watchdog.check_drift()
    assert res["healthy"] is False
    assert res["drift_score"] > 0
    assert res["anomalies_count"] > 0


def test_synthesize_ci_feedback_clean(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("synthesize_ci_feedback")
    assert tool is not None

    out = tool.handler({"ci_log": "All tests passed with flying colors."}, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["findings"][0]["category"] == "ci_clean"


def test_family_heartbeat_daemon(tmp_path: Any) -> None:
    db_file = tmp_path / "heartbeats.db"
    daemon = FamilyHeartbeatDaemon(db_path=db_file)

    rec1 = daemon.record_heartbeat("sakking", status="ok", details={"load": 0.12})
    assert rec1["persona"] == "sakking"
    assert rec1["status"] == "ok"
    assert rec1["details"]["load"] == 0.12

    rec2 = daemon.record_heartbeat("saktan", status="idle")
    assert rec2["persona"] == "saktan"

    recent_all = daemon.get_recent_heartbeats(limit=10)
    assert len(recent_all) == 2

    recent_sakking = daemon.get_recent_heartbeats(persona="sakking", limit=10)
    assert len(recent_sakking) == 1
    assert recent_sakking[0]["persona"] == "sakking"

    summary = daemon.get_fleet_health_summary()
    assert summary["fleet_size"] == 6
    assert summary["summary"]["sakking"]["status"] == "ok"
    assert summary["summary"]["saktan"]["status"] == "idle"
    assert summary["summary"]["sakthai"]["status"] == "unseen"


def test_telegram_digest_scheduler() -> None:
    from datetime import datetime

    scheduler = TelegramDigestScheduler(morning_hour=8, evening_hour=21)

    # 08:00 UTC
    dt_morning = datetime(2026, 11, 28, 8, 30, tzinfo=UTC)
    res_m = scheduler.should_send_digest(dt_morning)
    assert res_m["should_send"] is True
    assert res_m["digest_type"] == "morning"

    # 21:00 UTC
    dt_evening = datetime(2026, 11, 28, 21, 15, tzinfo=UTC)
    res_e = scheduler.should_send_digest(dt_evening)
    assert res_e["should_send"] is True
    assert res_e["digest_type"] == "evening"

    # Off-hour 14:00 UTC
    dt_off = datetime(2026, 11, 28, 14, 0, tzinfo=UTC)
    res_off = scheduler.should_send_digest(dt_off)
    assert res_off["should_send"] is False
    assert res_off["digest_type"] is None

    # Payload building
    payload = scheduler.build_digest_payload(
        persona_reports={"sakking": {"healthy": True, "skill_count": 10, "has_soul": True}},
        heartbeats=[{"persona": "sakking", "status": "ok"}],
        digest_type="morning",
    )
    assert payload["digest_type"] == "morning"
    assert "Morning Briefing" in payload["text"]
    assert "sakking" in payload["text"]
