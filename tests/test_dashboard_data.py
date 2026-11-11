"""Tests for sakthai.dashboard.data — KPI collection, lead/revenue parsing, MRR.

All tests inject a temp-file ``MemoryStore`` (via the shared ``store`` fixture)
or a sandboxed ``SAKTHAI_HOME``; nothing touches the real database.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sakthai.config import PERSONA_NAMES, persona_model_defaults
from sakthai.dashboard.data import _team_roster, collect_dashboard_data
from sakthai.memory.store import MemoryStore


def _days_ago(n: int) -> str:
    return (datetime.now(UTC) - timedelta(days=n)).strftime("%Y-%m-%d")


def _add_lead(store: MemoryStore, **payload: Any) -> int:
    return store.add_fact(json.dumps(payload), kind="lead", key=payload.get("name"))


def _add_revenue(store: MemoryStore, **payload: Any) -> int:
    return store.add_fact(json.dumps(payload), kind="revenue", key=payload.get("client"))


# ---------------------------------------------------------------------------
# Basic shape and KPIs
# ---------------------------------------------------------------------------


def test_empty_store_yields_zeroed_database_report(store: MemoryStore) -> None:
    data = collect_dashboard_data(store=store)
    assert data["source"] == "database"
    assert data["kpis"] == {
        "total_facts": 0,
        "total_facts_delta": 0,
        "total_observations": 0,
        "total_observations_delta": 0,
    }
    sqb = data["servicequotebot"]
    assert sqb["total_leads"] == 0
    assert sqb["conversion_rate"] == 0.0
    assert sqb["revenue_growth"] == {"labels": [], "values": []}


def test_kpis_count_facts_and_observations(store: MemoryStore) -> None:
    store.add_fact("alpha", kind="note")
    store.add_fact("beta", kind="note")
    store.add_observation("an observation", weight=2.0, confidence=0.9)

    data = collect_dashboard_data(store=store)
    assert data["kpis"]["total_facts"] == 2
    assert data["kpis"]["total_observations"] == 1
    # Everything was created just now, so it all falls in the 7-day delta.
    assert data["kpis"]["total_facts_delta"] == 2
    assert data["kpis"]["total_observations_delta"] == 1
    assert data["top_observations"][0]["label"] == "an observation"


def test_recent_facts_exclude_lead_and_revenue_kinds(store: MemoryStore) -> None:
    store.add_fact("general note", kind="note")
    _add_lead(store, name="Alice")
    _add_revenue(store, client="Alice Co", amount=10.0)

    data = collect_dashboard_data(store=store)
    kinds = {f["kind"] for f in data["recent_facts"]}
    assert kinds == {"note"}


def test_uninjected_store_opens_default_db(sakthai_home: Path) -> None:
    data = collect_dashboard_data()
    assert data["source"] == "database"
    assert (sakthai_home / "memory.db").exists()


# ---------------------------------------------------------------------------
# Lead parsing
# ---------------------------------------------------------------------------


def test_lead_with_malformed_json_becomes_query_payload(store: MemoryStore) -> None:
    store.add_fact("not json {", kind="lead")
    data = collect_dashboard_data(store=store)
    leads = data["servicequotebot"]["recent_leads"]
    assert len(leads) == 1
    assert leads[0]["query"] == "not json {"
    assert leads[0]["converted"] is False


def test_lead_with_non_dict_json_becomes_query_payload(store: MemoryStore) -> None:
    store.add_fact("[1, 2]", kind="lead")
    data = collect_dashboard_data(store=store)
    leads = data["servicequotebot"]["recent_leads"]
    assert leads[0]["query"] == "[1, 2]"


def test_lead_gets_id_and_date_stamped(store: MemoryStore) -> None:
    fact_id = _add_lead(store, name="Alice", email="alice@example.com")
    data = collect_dashboard_data(store=store)
    lead = data["servicequotebot"]["recent_leads"][0]
    assert lead["id"] == fact_id
    assert lead["date"] == datetime.now(UTC).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Revenue parsing, totals, and MRR
# ---------------------------------------------------------------------------


def test_revenue_totals_sum_all_amounts(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=100.0, type="setup", date=_days_ago(1))
    _add_revenue(store, client="B", amount=50.5, type="setup", date=_days_ago(2))
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["total_revenue"] == 150.5


def test_revenue_with_malformed_json_falls_back_to_key(store: MemoryStore) -> None:
    store.add_fact("oops not json", kind="revenue", key="Fallback Client")
    data = collect_dashboard_data(store=store)
    sqb = data["servicequotebot"]
    assert sqb["total_revenue"] == 0.0
    assert sqb["recent_revenue"][0]["client"] == "Fallback Client"


def test_mrr_counts_recent_monthly_revenue(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=100.0, type="monthly", date=_days_ago(10))
    _add_revenue(store, client="B", amount=40.0, type="subscription", date=_days_ago(5))
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["mrr"] == 140.0


def test_mrr_excludes_monthly_revenue_older_than_30_days(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=100.0, type="monthly", date=_days_ago(45))
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["mrr"] == 0.0
    assert data["servicequotebot"]["total_revenue"] == 100.0


def test_mrr_excludes_future_dated_monthly_revenue(store: MemoryStore) -> None:
    # A future date must not count toward MRR (a negative delta would slip
    # through an unbounded `<= 30 days` comparison).
    _add_revenue(store, client="A", amount=100.0, type="monthly", date=_days_ago(-60))
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["mrr"] == 0.0
    assert data["servicequotebot"]["total_revenue"] == 100.0


def test_mrr_includes_monthly_revenue_dated_today_and_30_days_ago(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=100.0, type="monthly", date=_days_ago(0))
    _add_revenue(store, client="B", amount=25.0, type="monthly", date=_days_ago(30))
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["mrr"] == 125.0


def test_mrr_excludes_setup_revenue(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=100.0, type="setup", date=_days_ago(1))
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["mrr"] == 0.0


def test_mrr_unparseable_date_falls_back_to_created_at(store: MemoryStore) -> None:
    # The fact was created just now, so the created_at fallback is within the
    # 30-day window and the amount still counts toward MRR.
    _add_revenue(store, client="A", amount=75.0, type="monthly", date="not-a-date")
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["mrr"] == 75.0


def test_revenue_missing_date_defaults_to_created_at(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=10.0, type="setup")
    data = collect_dashboard_data(store=store)
    rev = data["servicequotebot"]["recent_revenue"][0]
    assert rev["date"] == datetime.now(UTC).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Lead → revenue conversion matching
# ---------------------------------------------------------------------------


def test_lead_converted_when_name_matches_client(store: MemoryStore) -> None:
    _add_lead(store, name="Alice")
    _add_revenue(store, client="Alice Co", amount=10.0)
    data = collect_dashboard_data(store=store)
    sqb = data["servicequotebot"]
    assert sqb["recent_leads"][0]["converted"] is True
    assert sqb["conversion_rate"] == 100.0


def test_lead_converted_when_email_matches_client(store: MemoryStore) -> None:
    _add_lead(store, name="Zed", email="zed@example.com")
    _add_revenue(store, client="billing: zed@example.com", amount=10.0)
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["recent_leads"][0]["converted"] is True


def test_lead_converted_when_phone_matches_client(store: MemoryStore) -> None:
    _add_lead(store, name="Zed", phone="0812345678")
    _add_revenue(store, client="acct 0812345678", amount=10.0)
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["recent_leads"][0]["converted"] is True


def test_unmatched_lead_lowers_conversion_rate(store: MemoryStore) -> None:
    _add_lead(store, name="Alice")
    _add_lead(store, name="Nobody")
    _add_revenue(store, client="Alice Co", amount=10.0)
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["conversion_rate"] == 50.0


def test_revenue_without_client_is_skipped_in_matching(store: MemoryStore) -> None:
    _add_lead(store, name="Alice")
    _add_revenue(store, amount=10.0)  # no client field
    data = collect_dashboard_data(store=store)
    assert data["servicequotebot"]["recent_leads"][0]["converted"] is False


# ---------------------------------------------------------------------------
# Revenue growth timeline
# ---------------------------------------------------------------------------


def test_timeline_groups_by_date_and_accumulates(store: MemoryStore) -> None:
    _add_revenue(store, client="A", amount=10.0, date="2026-01-01")
    _add_revenue(store, client="B", amount=5.0, date="2026-01-01")
    _add_revenue(store, client="C", amount=20.0, date="2026-02-01")
    data = collect_dashboard_data(store=store)
    growth = data["servicequotebot"]["revenue_growth"]
    assert growth["labels"] == ["2026-01-01", "2026-02-01"]
    assert growth["values"] == [15.0, 35.0]


# ---------------------------------------------------------------------------
# Fallback stub on unexpected errors
# ---------------------------------------------------------------------------


def test_broken_store_yields_fallback_stub() -> None:
    class _BrokenStore:
        def list_facts(self, limit: int) -> list[Any]:
            raise RuntimeError("db exploded")

    data = collect_dashboard_data(store=_BrokenStore())  # type: ignore[arg-type]
    assert data["source"] == "fallback_stub"
    assert data["kpis"]["total_facts"] == 0
    assert data["servicequotebot"]["recent_leads"] == []


# ---------------------------------------------------------------------------
# Team roster
# ---------------------------------------------------------------------------


def test_team_roster_lists_every_persona_from_its_own_config() -> None:
    """The roster follows the persona configs, not a hand-kept table that drifts."""
    roster = _team_roster()

    assert [row["handle"] for row in roster] == [f"@{p}_agent_bot" for p in PERSONA_NAMES]
    for name, row in zip(PERSONA_NAMES, roster, strict=True):
        provider, model = persona_model_defaults(name)
        assert row["model"] == f"{model} ({provider})"
        assert row["agent"].lower() == name
        assert row["role"], f"{name} has no role in config/workspace.yaml"


def test_team_roster_keeps_a_persona_whose_config_is_missing_or_broken(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "saktan" / "config").mkdir(parents=True)
    (tmp_path / "saktan" / "config" / "workspace.yaml").write_text("role: [unclosed\n")
    (tmp_path / "sakking" / "config").mkdir(parents=True)
    (tmp_path / "sakking" / "config" / "workspace.yaml").write_text("- a list, not a mapping\n")
    monkeypatch.setattr("sakthai.config.PERSONAS_DIR", tmp_path)

    roster = _team_roster()

    assert [row["agent"] for row in roster] == list(PERSONA_NAMES)
    assert all(row["role"] == "" and row["model"] == "" for row in roster)
