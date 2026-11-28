"""Tests for Hugging Face Hub Triple-Gate programmatic safety enforcement."""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.hf import (
    TripleGateError,
    assert_hf_write_allowed,
    triple_gate_hub_write,
)
from sakthai.memory.store import MemoryStore
from sakthai.team.handoff import ChargeLevel


def test_assert_hf_write_allowed_passes_when_all_gates_satisfied(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    # Gate 1: Charge >= 50% (default active)
    # Gate 2: No deputy-chain tag
    # Gate 3: Beer's hub-approved tag exists
    store.add_fact(
        kind="decision",
        value="Beer approved upload for Nanthasit/sakthai-combined-v6",
        key="hub_approval_v6",
        tags=["hub-approved", "sakthai"],
    )

    allowed = assert_hf_write_allowed(
        store=store,
        target_repo="Nanthasit/sakthai-combined-v6",
        current_charge=ChargeLevel.ACTIVE,
    )
    assert allowed is True


def test_assert_hf_write_allowed_fails_when_charge_too_low(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    store.add_fact(
        kind="decision",
        value="Approved",
        key="appr",
        tags=["hub-approved"],
    )

    with pytest.raises(TripleGateError, match=r"(?i)Gate 1 violation.*charge"):
        assert_hf_write_allowed(
            store=store,
            target_repo="Nanthasit/sakthai-combined-v6",
            current_charge=ChargeLevel.LOW,
        )


def test_assert_hf_write_allowed_fails_when_deputy_chain_active(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    store.add_fact(
        kind="decision",
        value="Approved",
        key="appr",
        tags=["hub-approved"],
    )
    # Active deputy-chain emergency
    store.add_fact(
        kind="emergency",
        value="SakThai charge dropped below 20%, delegated to sakking",
        key="deputy_active",
        tags=["deputy-chain", "emergency"],
    )

    with pytest.raises(TripleGateError, match="Gate 2 violation.*deputy-chain"):
        assert_hf_write_allowed(
            store=store,
            target_repo="Nanthasit/sakthai-combined-v6",
            current_charge=ChargeLevel.ACTIVE,
        )


def test_assert_hf_write_allowed_fails_when_hub_approved_missing(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    # No hub-approved tag present

    with pytest.raises(TripleGateError, match="Gate 3 violation.*hub-approved"):
        assert_hf_write_allowed(
            store=store,
            target_repo="Nanthasit/sakthai-combined-v6",
            current_charge=ChargeLevel.ACTIVE,
        )


def test_triple_gate_hub_write_decorator(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    store.add_fact(
        kind="decision",
        value="Approved",
        key="appr",
        tags=["hub-approved"],
    )

    @triple_gate_hub_write
    def push_model(
        repo_id: str, store: MemoryStore, current_charge: Any = ChargeLevel.ACTIVE
    ) -> str:
        return f"pushed {repo_id}"

    result = push_model("Nanthasit/model", store=store)
    assert result == "pushed Nanthasit/model"

    # Fails when charge drops
    with pytest.raises(TripleGateError):
        push_model("Nanthasit/model", store=store, current_charge=ChargeLevel.LOW)
