"""Unit tests for ServiceQuoteBot pre-flight verifier."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from sakthai.agent.loop import AgentResult
from sakthai.client import (
    ClientConfig,
    SyntheticTestCase,
    run_client_verification,
    save_client,
)
from sakthai.memory.store import MemoryStore


def test_run_client_verification_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path))

    cfg = ClientConfig(client_id="plumbing-pro", company_name="Plumbing Pro", currency="USD")
    save_client(cfg)

    store = MemoryStore(":memory:")
    store.add_fact(kind="fact", value="Standard drain cleaning: $150")

    mock_agent_result = AgentResult(
        text="Hello! For our standard drain cleaning, the price quote is $150. Thank you Alice!",
        iterations=2,
        stop_reason="end_turn",
        usage={"input_tokens": 50, "output_tokens": 25, "total_tokens": 75},
    )

    custom_tests = (
        SyntheticTestCase(
            name="quote_test",
            customer_message="How much for drain cleaning?",
            expected_keywords=("quote", "price", "150"),
        ),
        SyntheticTestCase(
            name="lead_test",
            customer_message="Please record my name Alice",
            expected_keywords=("alice", "thank"),
            is_lead_capture_test=True,
        ),
    )

    with patch("sakthai.client.verifier.run_persona_task", return_value=mock_agent_result):
        res = run_client_verification(
            "plumbing-pro", test_cases=custom_tests, config=cfg, store=store
        )

        assert res.client_id == "plumbing-pro"
        assert res.all_passed is True
        assert res.total_tests == 2
        assert res.passed_tests == 2
        assert res.failed_tests == 0
        assert "PASSED ✅" in res.summary

        # Check lead was recorded in store
        leads = [f for f in store.list_facts() if f.kind == "lead"]
        assert len(leads) == 1
        assert "Alice Taylor" in leads[0].value


def test_run_client_verification_keyword_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path))

    cfg = ClientConfig(client_id="failing-co", company_name="Failing Co")
    save_client(cfg)

    mock_result = AgentResult(
        text="Irrelevant text without keywords.",
        iterations=1,
        stop_reason="end_turn",
        usage={"input_tokens": 10, "output_tokens": 10, "total_tokens": 20},
    )

    custom_tests = (
        SyntheticTestCase(
            name="strict_test",
            customer_message="Tell me the price",
            expected_keywords=("specific_unmatched_keyword",),
        ),
    )

    with patch("sakthai.client.verifier.run_persona_task", return_value=mock_result):
        res = run_client_verification("failing-co", test_cases=custom_tests, config=cfg)
        assert res.all_passed is False
        assert res.failed_tests == 1
        assert "FAILED ❌" in res.summary
