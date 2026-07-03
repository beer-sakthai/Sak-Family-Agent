"""Unit tests for lead capture validation (``sakthai.lead.capture``).

``capture_lead`` was previously reached only through the ``capture_lead`` agent
tool. These pin its validation guards, ``lead_key`` precedence, payload shape,
and both the injected-store and default-``MemoryStore()`` branches directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.lead.capture import capture_lead
from sakthai.memory.store import MemoryStore


def test_query_is_required_and_must_be_non_empty(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="query"):
        capture_lead(name="Ada", query="   ", store=store)


def test_query_must_be_a_string(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="query"):
        capture_lead(name="Ada", query=None, store=store)  # type: ignore[arg-type]


def test_at_least_one_contact_field_is_required(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="name.*phone.*email"):
        capture_lead(query="Need a quote", store=store)


def test_blank_contact_fields_do_not_count_as_provided(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="name.*phone.*email"):
        capture_lead(name="  ", phone="", email="   ", query="Need a quote", store=store)


def test_lead_key_prefers_name_over_email_and_phone(store: MemoryStore) -> None:
    capture_lead(
        name="Ada",
        email="ada@example.com",
        phone="+1-555-0100",
        query="Website refresh",
        store=store,
    )
    (fact,) = store.list_facts()
    assert fact.key == "Ada"


def test_lead_key_falls_back_to_email_then_phone(store: MemoryStore) -> None:
    capture_lead(email="grace@example.com", phone="+1-555-0199", query="Quote", store=store)
    email_lead = store.list_facts()[0]
    assert email_lead.key == "grace@example.com"

    capture_lead(phone="+1-555-0123", query="Quote", store=store)
    phone_lead = store.list_facts()[0]
    assert phone_lead.key == "+1-555-0123"


def test_payload_is_json_with_stripped_values(store: MemoryStore) -> None:
    lead_id = capture_lead(
        name="  Ada  ",
        email="  ada@example.com ",
        query="  Need a quote  ",
        store=store,
    )
    assert isinstance(lead_id, int)
    (fact,) = store.list_facts()
    assert fact.kind == "lead"
    assert json.loads(fact.value) == {
        "query": "Need a quote",
        "name": "Ada",
        "email": "ada@example.com",
    }


def test_payload_preserves_non_ascii_characters(store: MemoryStore) -> None:
    capture_lead(name="Renée", query="Besoin d'un devis", store=store)
    (fact,) = store.list_facts()
    # ensure_ascii=False keeps the raw character rather than a \uXXXX escape.
    assert "Renée" in fact.value
    assert json.loads(fact.value)["name"] == "Renée"


def test_default_store_branch_writes_to_sakthai_home(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No ``store=`` argument: exercises the ``with MemoryStore() as ...`` branch,
    # kept hermetic by pointing SAKTHAI_HOME (via the fixture) at a temp dir.
    lead_id = capture_lead(name="Ada", query="Need a quote")
    assert isinstance(lead_id, int)

    with MemoryStore() as verify:
        facts = verify.list_facts()
    assert len(facts) == 1
    assert facts[0].kind == "lead"
    assert facts[0].key == "Ada"
