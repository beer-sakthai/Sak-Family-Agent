"""Store customer leads in the memory database."""

from __future__ import annotations

import json
from typing import Any

from ..memory.store import MemoryStore


def capture_lead(
    *,
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    query: str,
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

    lead_key = payload.get("name") or payload.get("email") or payload.get("phone")
    encoded = json.dumps(payload, ensure_ascii=False)
    if store is not None:
        return store.add_fact(encoded, kind="lead", key=lead_key)
    with MemoryStore() as memory_store:
        return memory_store.add_fact(encoded, kind="lead", key=lead_key)
