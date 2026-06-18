"""Smoke tests for the React dashboard integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.dashboard.data import SOURCE_LIVE, export_dashboard_json
from sakthai.memory.store import MemoryStore

_DIST_PATH = Path(__file__).parent.parent / "dashboard" / "dist"


@pytest.mark.skipif(
    not _DIST_PATH.exists(), reason="dashboard/dist not built — run 'npm run build'"
)
def test_dashboard_dist_exists() -> None:
    assert _DIST_PATH.exists()
    assert (_DIST_PATH / "index.html").exists()


def test_dashboard_export_integration(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        store.add_fact("integration test fact", kind="note")

    dest = tmp_path / "data.json"
    export_dashboard_json(dest, db)

    assert dest.exists()
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["source"] == SOURCE_LIVE
    assert data["kpis"]["total_facts"] == 1
    assert data["recent_facts"][0]["value"] == "integration test fact"
    # Ensure new fields are present
    assert "skills" in data
    assert "recent_sessions" in data
    assert "total_tokens" in data["kpis"]
