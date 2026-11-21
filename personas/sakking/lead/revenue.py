"""Revenue and conversion metrics tracking for captured customer leads."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from ..memory.store import MemoryStore
from .capture import VALID_LEAD_STATUSES


@dataclass
class LeadRevenueMetrics:
    """Metrics snapshot for customer leads and pipeline revenue."""

    total_leads: int = 0
    new_leads: int = 0
    quoted_leads: int = 0
    won_leads: int = 0
    lost_leads: int = 0
    conversion_rate: float = 0.0
    total_pipeline_value: float = 0.0
    total_won_revenue: float = 0.0
    total_mrr: float = 0.0
    average_deal_size: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _decode_lead_fact(fact_id: int, value: str, created_at: int, updated_at: int) -> dict[str, Any]:
    try:
        data = json.loads(value)
        if not isinstance(data, dict):
            data = {"query": str(value)}
    except (ValueError, TypeError):
        data = {"query": str(value)}

    data["id"] = fact_id
    data["created_at"] = created_at
    data["updated_at"] = updated_at
    data.setdefault("status", "NEW")
    data.setdefault("deal_value", 0.0)
    data.setdefault("monthly_recurring_revenue", 0.0)
    return data


def get_lead_by_id(lead_id: int, store: MemoryStore | None = None) -> dict[str, Any] | None:
    """Retrieve a lead by fact id, returning parsed dictionary or None."""
    if store is not None:
        fact = store.get_fact(lead_id)
    else:
        with MemoryStore() as memory_store:
            fact = memory_store.get_fact(lead_id)

    if fact is None or fact.kind != "lead":
        return None

    return _decode_lead_fact(fact.id, fact.value, fact.created_at, fact.updated_at)


def list_leads(
    status: str | None = None,
    store: MemoryStore | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """List captured leads, optionally filtered by status."""
    if store is not None:
        facts = store.list_facts(limit=limit, kind="lead")
    else:
        with MemoryStore() as memory_store:
            facts = memory_store.list_facts(limit=limit, kind="lead")

    leads: list[dict[str, Any]] = []
    target_status = status.upper().strip() if isinstance(status, str) and status.strip() else None

    for fact in facts:
        lead = _decode_lead_fact(fact.id, fact.value, fact.created_at, fact.updated_at)
        if target_status is not None and lead.get("status") != target_status:
            continue
        leads.append(lead)

    return leads


def update_lead_status(
    lead_id: int,
    status: str,
    *,
    deal_value: float | None = None,
    monthly_recurring_revenue: float | None = None,
    notes: str | None = None,
    store: MemoryStore | None = None,
) -> bool:
    """Update lead status, deal value, recurring revenue, or notes."""
    status_upper = status.upper().strip()
    if status_upper not in VALID_LEAD_STATUSES:
        raise ValueError(
            f"Invalid lead status '{status}'. Valid statuses: {', '.join(VALID_LEAD_STATUSES)}"
        )

    def _perform_update(target_store: MemoryStore) -> bool:
        fact = target_store.get_fact(lead_id)
        if fact is None or fact.kind != "lead":
            return False

        try:
            payload = json.loads(fact.value)
            if not isinstance(payload, dict):
                payload = {"query": fact.value}
        except (ValueError, TypeError):
            payload = {"query": fact.value}

        payload["status"] = status_upper
        if deal_value is not None:
            payload["deal_value"] = float(deal_value)
        if monthly_recurring_revenue is not None:
            payload["monthly_recurring_revenue"] = float(monthly_recurring_revenue)
        if notes is not None:
            payload["notes"] = notes.strip()

        encoded = json.dumps(payload, ensure_ascii=False)
        return target_store.update_fact(lead_id, encoded)

    if store is not None:
        return _perform_update(store)
    with MemoryStore() as memory_store:
        return _perform_update(memory_store)


def calculate_lead_revenue_metrics(
    store: MemoryStore | None = None,
) -> LeadRevenueMetrics:
    """Calculate conversion and pipeline/won revenue metrics from all leads."""
    leads = list_leads(store=store, limit=10000)

    total_leads = len(leads)
    new_leads = 0
    quoted_leads = 0
    won_leads = 0
    lost_leads = 0
    pipeline_val = 0.0
    won_rev = 0.0
    won_mrr = 0.0

    for lead in leads:
        st = lead.get("status", "NEW")
        val = float(lead.get("deal_value") or 0.0)
        mrr = float(lead.get("monthly_recurring_revenue") or 0.0)

        if st == "NEW":
            new_leads += 1
            pipeline_val += val
        elif st == "QUOTED":
            quoted_leads += 1
            pipeline_val += val
        elif st == "WON":
            won_leads += 1
            won_rev += val
            won_mrr += mrr
        elif st == "LOST":
            lost_leads += 1

    conversion_rate = round((won_leads / total_leads * 100.0), 2) if total_leads > 0 else 0.0
    avg_deal_size = round(won_rev / won_leads, 2) if won_leads > 0 else 0.0

    return LeadRevenueMetrics(
        total_leads=total_leads,
        new_leads=new_leads,
        quoted_leads=quoted_leads,
        won_leads=won_leads,
        lost_leads=lost_leads,
        conversion_rate=conversion_rate,
        total_pipeline_value=round(pipeline_val, 2),
        total_won_revenue=round(won_rev, 2),
        total_mrr=round(won_mrr, 2),
        average_deal_size=avg_deal_size,
    )
