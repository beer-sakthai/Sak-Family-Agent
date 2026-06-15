"""Tests for the dashboard data layer (no Streamlit needed)."""

from __future__ import annotations

import json
from pathlib import Path

from sakthai.dashboard.data import (
    SOURCE_DEMO,
    SOURCE_LIVE,
    collect_dashboard_data,
    export_dashboard_json,
)
from sakthai.memory.store import MemoryStore


def test_empty_store_returns_demo(tmp_path: Path) -> None:
    data = collect_dashboard_data(tmp_path / "empty.db")
    assert data["source"] == SOURCE_DEMO
    assert data["kpis"]["total_facts"] > 0  # demo sample is populated


def test_live_data_reflects_store(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        store.add_fact("uses vim", kind="pref")
        store.add_fact("lives in Bangkok", kind="profile")
        store.add_observation("works late", weight=0.8)

    data = collect_dashboard_data(db, days=7)
    assert data["source"] == SOURCE_LIVE
    assert data["kpis"]["total_facts"] == 2
    assert data["kpis"]["total_observations"] == 1
    assert len(data["growth"]["labels"]) == 7
    assert data["growth"]["facts"][-1] == 2  # cumulative
    kinds = {c["name"] for c in data["categories"]}
    assert {"Pref", "Profile", "Observations"} <= kinds
    assert data["recent_facts"][0]["value"] in {"uses vim", "lives in Bangkok"}


def test_export_dashboard_json(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        store.add_fact("a fact")
    dest = tmp_path / "out" / "data.json"
    written = export_dashboard_json(dest, db)
    assert written.exists()
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert payload["source"] == SOURCE_LIVE
    assert payload["kpis"]["total_facts"] == 1
