"""Store customer leads in the memory database."""

from __future__ import annotations

import json
from typing import Any

from ..memory.store import MemoryStore

VALID_LEAD_STATUSES: tuple[str, ...] = ("NEW", "QUOTED", "WON", "LOST")


def capture_lead(
    *,
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    query: str,
    status: str | None = None,
    deal_value: float | None = None,
    monthly_recurring_revenue: float | None = None,
    notes: str | None = None,
    store: MemoryStore | None = None,
) -> int:
    """Store a lead as a structured fact and return its id."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")

    payload: dict[str, Any] = {"query": query.strip()}
    for field_name, raw in (("name", name), ("phone", phone), ("email", email)):
        if isinstance(raw, str) and raw.strip():
            payload[field_name] = raw.strip()

    if "name" not in payload and "phone" not in payload and "email" not in payload:
        raise ValueError("At least one of `name`, `phone`, or `email` is required.")

    if status is not None:
        st = status.upper().strip()
        payload["status"] = st if st in VALID_LEAD_STATUSES else "NEW"
    if deal_value is not None:
        payload["deal_value"] = float(deal_value)
    if monthly_recurring_revenue is not None:
        payload["monthly_recurring_revenue"] = float(monthly_recurring_revenue)
    if isinstance(notes, str) and notes.strip():
        payload["notes"] = notes.strip()

    lead_key = payload.get("name") or payload.get("email") or payload.get("phone")
    encoded = json.dumps(payload, ensure_ascii=False)
    if store is not None:
        return store.add_fact(encoded, kind="lead", key=lead_key)
    with MemoryStore() as memory_store:
        return memory_store.add_fact(encoded, kind="lead", key=lead_key)
