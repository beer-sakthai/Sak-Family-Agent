"""Unit tests for the DashboardDataCollector."""

from __future__ import annotations

from sakthai.dashboard.data import DashboardDataCollector
from sakthai.memory.store import MemoryStore


def test_dashboard_collector_with_empty_store(store: MemoryStore) -> None:
    """Verify collector returns a valid, empty structure for a new store."""
    collector = DashboardDataCollector(store)
    data = collector.collect()

    assert data["source"] == "demo"
    assert data["kpis"]["total_facts"] == 5  # from DEMO_DATA
    assert data["kpis"]["total_observations"] == 2
    assert len(data["recent_facts"]) == 5


def test_dashboard_collector_with_data(store: MemoryStore) -> None:
    """Verify KPIs and lists are populated correctly."""
    store.learn("fact 1", "test", "key1")
    store.learn("fact 2", "test", "key2")
    store.consolidate_memory(age_seconds=0)  # Create an observation

    collector = DashboardDataCollector(store)
    data = collector.collect()

    assert data["kpis"]["total_facts"] == 2
    assert data["kpis"]["total_observations"] == 1
    assert len(data["recent_facts"]) == 2
    assert len(data["top_observations"]) == 1
    assert data["categories"][0]["name"] == "Test"
    assert data["categories"][0]["count"] == 2
