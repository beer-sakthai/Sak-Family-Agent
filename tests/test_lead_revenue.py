"""Tests for lead revenue tracking and CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.lead import (
    LeadRevenueMetrics,
    calculate_lead_revenue_metrics,
    capture_lead,
    get_lead_by_id,
    list_leads,
    update_lead_status,
)
from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _isolated_home(sakthai_home: Path) -> Path:
    return sakthai_home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_lead_revenue_metrics_defaults() -> None:
    metrics = LeadRevenueMetrics()
    assert metrics.total_leads == 0
    assert metrics.conversion_rate == 0.0
    d = metrics.to_dict()
    assert d["total_leads"] == 0
    assert d["total_mrr"] == 0.0


def test_capture_and_get_lead_by_id(store: MemoryStore) -> None:
    lead_id = capture_lead(
        name="Alice Corp",
        email="alice@example.com",
        query="Interested in premium support",
        status="NEW",
        deal_value=5000.0,
        monthly_recurring_revenue=500.0,
        notes="High intent lead",
        store=store,
    )

    lead = get_lead_by_id(lead_id, store=store)
    assert lead is not None
    assert lead["id"] == lead_id
    assert lead["name"] == "Alice Corp"
    assert lead["email"] == "alice@example.com"
    assert lead["status"] == "NEW"
    assert lead["deal_value"] == 5000.0
    assert lead["monthly_recurring_revenue"] == 500.0
    assert lead["notes"] == "High intent lead"


def test_get_lead_by_id_missing_or_wrong_kind(store: MemoryStore) -> None:
    assert get_lead_by_id(99999, store=store) is None

    # Fact with kind="note" should not be treated as a lead
    note_id = store.add_fact("General note", kind="note")
    assert get_lead_by_id(note_id, store=store) is None


def test_list_leads_and_filtering(store: MemoryStore) -> None:
    id1 = capture_lead(name="Bob", phone="123", query="Service 1", status="NEW", store=store)
    capture_lead(
        name="Charlie", email="c@test.com", query="Service 2", status="QUOTED", store=store
    )
    id3 = capture_lead(
        name="Dave", email="d@test.com", query="Service 3", status="WON", store=store
    )

    all_leads = list_leads(store=store)
    assert len(all_leads) == 3

    new_leads = list_leads(status="new", store=store)
    assert len(new_leads) == 1
    assert new_leads[0]["id"] == id1

    won_leads = list_leads(status="WON", store=store)
    assert len(won_leads) == 1
    assert won_leads[0]["id"] == id3

    lost_leads = list_leads(status="LOST", store=store)
    assert len(lost_leads) == 0


def test_update_lead_status(store: MemoryStore) -> None:
    lead_id = capture_lead(
        name="Eve",
        email="eve@test.com",
        query="Need enterprise rollout",
        deal_value=10000.0,
        store=store,
    )

    # Move to QUOTED
    ok = update_lead_status(
        lead_id, "QUOTED", deal_value=12000.0, notes="Sent quotation v1", store=store
    )
    assert ok is True

    lead = get_lead_by_id(lead_id, store=store)
    assert lead is not None
    assert lead["status"] == "QUOTED"
    assert lead["deal_value"] == 12000.0
    assert lead["notes"] == "Sent quotation v1"

    # Move to WON with MRR
    ok = update_lead_status(lead_id, "won", monthly_recurring_revenue=1000.0, store=store)
    assert ok is True

    lead = get_lead_by_id(lead_id, store=store)
    assert lead is not None
    assert lead["status"] == "WON"
    assert lead["monthly_recurring_revenue"] == 1000.0
    assert lead["deal_value"] == 12000.0  # preserved


def test_update_lead_status_validation_and_errors(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="Invalid lead status"):
        update_lead_status(1, "INVALID_STATUS", store=store)

    # Absent lead id returns False
    assert update_lead_status(9999, "LOST", store=store) is False


def test_calculate_lead_revenue_metrics(store: MemoryStore) -> None:
    # Empty store
    empty_metrics = calculate_lead_revenue_metrics(store=store)
    assert empty_metrics.total_leads == 0
    assert empty_metrics.conversion_rate == 0.0

    # Populate mixed leads
    capture_lead(
        name="Lead 1", email="l1@test.com", query="Q1", status="NEW", deal_value=1000.0, store=store
    )
    capture_lead(
        name="Lead 2",
        email="l2@test.com",
        query="Q2",
        status="QUOTED",
        deal_value=2000.0,
        store=store,
    )
    capture_lead(
        name="Lead 3",
        email="l3@test.com",
        query="Q3",
        status="WON",
        deal_value=4000.0,
        monthly_recurring_revenue=400.0,
        store=store,
    )
    capture_lead(
        name="Lead 4",
        email="l4@test.com",
        query="Q4",
        status="WON",
        deal_value=6000.0,
        monthly_recurring_revenue=600.0,
        store=store,
    )
    capture_lead(
        name="Lead 5",
        email="l5@test.com",
        query="Q5",
        status="LOST",
        deal_value=5000.0,
        store=store,
    )

    metrics = calculate_lead_revenue_metrics(store=store)
    assert metrics.total_leads == 5
    assert metrics.new_leads == 1
    assert metrics.quoted_leads == 1
    assert metrics.won_leads == 2
    assert metrics.lost_leads == 1
    # 2 won out of 5 total = 40.0%
    assert metrics.conversion_rate == 40.0
    # Pipeline value (NEW + QUOTED) = 1000 + 2000 = 3000.0
    assert metrics.total_pipeline_value == 3000.0
    # Won revenue = 4000 + 6000 = 10000.0
    assert metrics.total_won_revenue == 10000.0
    # Won MRR = 400 + 600 = 1000.0
    assert metrics.total_mrr == 1000.0
    # Average deal size = 10000 / 2 = 5000.0
    assert metrics.average_deal_size == 5000.0


def test_cli_lead_capture_and_list(runner: CliRunner) -> None:
    # Capture lead
    result = runner.invoke(
        main,
        [
            "lead",
            "capture",
            "-q",
            "Commercial cleaning quote",
            "-n",
            "Acme Office",
            "-p",
            "+1-800-555-0199",
            "--deal-value",
            "2500",
            "--mrr",
            "300",
        ],
    )
    assert result.exit_code == 0
    assert "Captured lead #" in result.output

    # List leads formatted
    res_list = runner.invoke(main, ["lead", "list"])
    assert res_list.exit_code == 0
    assert "Found 1 lead(s):" in res_list.output
    assert "Acme Office" in res_list.output
    assert "$2,500.00" in res_list.output

    # List leads JSON
    res_json = runner.invoke(main, ["lead", "list", "--json"])
    assert res_json.exit_code == 0
    parsed = json.loads(res_json.output)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "Acme Office"
    assert parsed[0]["deal_value"] == 2500.0


def test_cli_lead_stats(runner: CliRunner) -> None:
    # Initially 0 leads
    res = runner.invoke(main, ["lead", "stats"])
    assert res.exit_code == 0
    assert "Total Leads:        0" in res.output

    # Capture and win a lead
    runner.invoke(
        main,
        [
            "lead",
            "capture",
            "-q",
            "HVAC service",
            "-n",
            "TechCorp",
            "--deal-value",
            "1500",
            "--status",
            "won",
        ],
    )

    res_stats = runner.invoke(main, ["lead", "stats"])
    assert res_stats.exit_code == 0
    assert "Total Leads:        1" in res_stats.output
    assert "1 WON" in res_stats.output
    assert "$1,500.00" in res_stats.output

    # Stats JSON
    res_json = runner.invoke(main, ["lead", "stats", "--json"])
    assert res_json.exit_code == 0
    stats = json.loads(res_json.output)
    assert stats["total_leads"] == 1
    assert stats["won_leads"] == 1
    assert stats["total_won_revenue"] == 1500.0


def test_cli_lead_update_and_errors(runner: CliRunner) -> None:
    runner.invoke(main, ["lead", "capture", "-q", "Plumbing repair", "-n", "PlumbLead"])

    # Update status to quoted and set deal value
    res_up = runner.invoke(
        main, ["lead", "update", "1", "--status", "quoted", "--deal-value", "750"]
    )
    assert res_up.exit_code == 0
    assert "Updated lead #1 to status [QUOTED]" in res_up.output

    # Update nonexistent lead
    res_err = runner.invoke(main, ["lead", "update", "9999", "--status", "won"])
    assert res_err.exit_code != 0
    assert "Lead #9999 not found" in res_err.output


def test_cli_lead_capture_validation_error(runner: CliRunner) -> None:
    # Missing both name, phone, and email
    res = runner.invoke(main, ["lead", "capture", "-q", "Anonymous inquiry"])
    assert res.exit_code != 0
    assert "At least one of `name`, `phone`, or `email` is required" in res.output
