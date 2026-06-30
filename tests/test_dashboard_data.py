"""Tests for the dashboard data layer (no Streamlit needed)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from sakthai.dashboard.data import (
    SOURCE_DEMO,
    SOURCE_LIVE,
    collect_dashboard_data,
    export_dashboard_json,
)
from sakthai.memory.store import SNAPSHOT_VERSION, MemoryStore

_DAY = 86_400


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


def test_growth_window_boundaries(tmp_path: Path) -> None:
    """Facts/observations outside the window are counted as a baseline, not binned.

    Exercises the boundary branches in the growth builder: items at or before the
    window start fold into the carried baseline (``*_before_start``), and items
    dated past the window's last day fall outside every bin (``idx`` out of range).
    """
    db = tmp_path / "memory.db"
    now = int(time.time())
    snapshot = {
        "version": SNAPSHOT_VERSION,
        "facts": [
            # Older than the 7-day window start -> baseline (before_start branch).
            _fact_row(1, "ancient", created_at=now - 100 * _DAY),
            # Comfortably inside the window -> binned.
            _fact_row(2, "today", created_at=now - _DAY),
            # Dated into the future -> idx >= days, skipped (out-of-range branch).
            _fact_row(3, "future", created_at=now + 5 * _DAY),
        ],
        "observations": [
            _obs_row(1, "old obs", created_at=now - 100 * _DAY),  # baseline
            _obs_row(2, "recent obs", created_at=now - _DAY),  # binned
            _obs_row(3, "future obs", created_at=now + 5 * _DAY),  # out-of-range
        ],
    }
    with MemoryStore(db) as store:
        store.import_from_dict(snapshot, mode="replace")

    data = collect_dashboard_data(db, days=7)
    assert data["source"] == SOURCE_LIVE
    # Raw KPI counts include every row.
    assert data["kpis"]["total_facts"] == 3
    assert data["kpis"]["total_observations"] == 3
    # The cumulative growth series spans only the window: baseline (1) + the one
    # in-window item (1). The future-dated row falls outside every bin and so is
    # absent from the series.
    assert data["growth"]["facts"][-1] == 2
    assert data["growth"]["observations"][-1] == 2
    # The carried baseline means the series never starts at zero.
    assert data["growth"]["facts"][0] >= 1
    assert data["growth"]["observations"][0] >= 1


def _fact_row(fid: int, value: str, *, created_at: int) -> dict[str, object]:
    return {
        "id": fid,
        "kind": "note",
        "key": None,
        "value": value,
        "source_session": None,
        "created_at": created_at,
        "updated_at": created_at,
        "tags": [],
    }


def _obs_row(oid: int, summary: str, *, created_at: int) -> dict[str, object]:
    return {
        "id": oid,
        "summary": summary,
        "evidence_session_id": None,
        "weight": 1.0,
        "confidence": 0.5,
        "created_at": created_at,
    }


def test_unreadable_store_falls_back_to_demo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.memory.store as store_mod

    def _boom(*_a: object, **_kw: object) -> None:
        raise RuntimeError("disk full")

    monkeypatch.setattr(store_mod, "MemoryStore", _boom)

    data = collect_dashboard_data(tmp_path / "broken.db")
    assert data["source"] == SOURCE_DEMO

def test_collect_data_clamped_days(tmp_path: Path) -> None:
    """Ensure that extremely large 'days' values are clamped to prevent DoS."""
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        store.add_fact("test fact")

    # Pass a huge number of days
    data = collect_dashboard_data(db, days=1_000_000)

    # Verify that the growth series length is capped at the internal max (365)
    assert len(data["growth"]["labels"]) == 365
    assert len(data["growth"]["facts"]) == 365
    assert len(data["growth"]["observations"]) == 365
