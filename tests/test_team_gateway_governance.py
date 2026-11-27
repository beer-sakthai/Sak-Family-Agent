"""Unit tests for PortfolioCacheEngine and SQLiteConflictListener in team/gateway.py."""

from __future__ import annotations

from typing import Any

from sakthai.memory.store import MemoryStore
from sakthai.team.gateway import PortfolioCacheEngine, SQLiteConflictListener


def test_portfolio_cache_engine_get_and_refresh(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    engine = PortfolioCacheEngine(store=store)

    # Initial get populates cache
    data = engine.get_cached_portfolio(owner="Nanthasit")
    assert data["status"] == "ok"
    assert data["owner"] == "Nanthasit"
    assert data["total_models"] == 23
    assert data["total_datasets"] == 15
    assert data["total_spaces"] == 6

    # Subsequent call returns cached data quickly
    data2 = engine.get_cached_portfolio(owner="Nanthasit")
    assert data2["cached_at"] == data["cached_at"]

    # Refresh updates the timestamp
    data3 = engine.refresh_portfolio_cache(owner="Nanthasit")
    assert data3["status"] == "ok"


def test_sqlite_conflict_listener_poll_and_notify(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    listener = SQLiteConflictListener(store=store)

    # Initially no conflicts
    conflicts = listener.poll_conflicts()
    assert len(conflicts) == 0

    # Add a conflict fact
    store.add_fact(
        kind="alert",
        value="Browser rate-limit conflict between SakSee and SakKing",
        key="conflict_1",
        tags=["conflict", "saksee", "sakking"],
    )

    conflicts = listener.poll_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0]["tags"] == ["conflict", "saksee", "sakking"]

    # Register listener callback
    received: list[dict[str, Any]] = []
    listener.on_conflict_detected(lambda c: received.append(c))

    notified = listener.notify_if_any()
    assert notified == 1
    assert len(received) == 1
    assert "SakSee and SakKing" in received[0]["value"]


def test_portfolio_cache_engine_default_store_and_error(tmp_path: Any, monkeypatch: Any) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    engine = PortfolioCacheEngine()
    store = engine._get_store()
    assert store is not None

    # Error handling when adding fact fails
    class FailingStore:
        def list_facts(self, *a: Any, **kw: Any) -> list[Any]:
            return []

        def add_fact(self, *a: Any, **kw: Any) -> None:
            raise OSError("Disk full")

    failing_engine = PortfolioCacheEngine(store=FailingStore())
    data = failing_engine.refresh_portfolio_cache(owner="Nanthasit")
    assert data["status"] == "ok"


def test_sqlite_conflict_listener_default_store_and_callback_error(
    tmp_path: Any, monkeypatch: Any
) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    listener = SQLiteConflictListener()
    store = listener._get_store()
    assert store is not None

    # Callback exception handling
    store.add_fact(kind="alert", value="Test error", tags=["conflict"])
    listener.on_conflict_detected(lambda c: (_ for _ in ()).throw(ValueError("Boom")))
    notified = listener.notify_if_any()
    assert notified == 1
