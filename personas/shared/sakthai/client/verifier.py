"""Pre-flight verification runner for provisioned ServiceQuoteBot clients."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..agent.coordinator import run_persona_task
from ..memory.store import MemoryStore
from .manager import get_client_dir, load_client
from .models import (
    ClientConfig,
    SyntheticTestCase,
    SyntheticTestResult,
    VerificationResult,
)

logger = logging.getLogger(__name__)

DEFAULT_TEST_CASES: tuple[SyntheticTestCase, ...] = (
    SyntheticTestCase(
        name="price_inquiry",
        customer_message="Hello, can you give me a quote for your primary standard service?",
        expected_keywords=("quote", "price", "cost", "service"),
    ),
    SyntheticTestCase(
        name="unsupported_service",
        customer_message="Do you provide interplanetary orbital rocket engine repair?",
        expected_keywords=("sorry", "not", "unable", "contact", "support", "help"),
    ),
    SyntheticTestCase(
        name="lead_capture",
        customer_message="I'd like to book an appointment. My name is Alice Taylor, phone +1-555-0188, email alice@example.com.",
        expected_keywords=("alice", "thank", "contact", "detail", "touch", "recorded"),
        is_lead_capture_test=True,
    ),
)


def run_client_verification(
    client_id: str,
    test_cases: Sequence[SyntheticTestCase] | None = None,
    *,
    config: ClientConfig | None = None,
    store: MemoryStore | None = None,
    client: Any = None,
    verbose: bool = False,
) -> VerificationResult:
    """Execute pre-flight synthetic tests against a client's provisioned workspace."""
    cfg = config or load_client(client_id)
    client_dir = get_client_dir(cfg.client_id)
    db_path = client_dir / "data" / "memory.db"

    target_store = store or (
        MemoryStore(db_path) if db_path.is_file() else MemoryStore(Path(":memory:"))
    )
    cases = list(test_cases) if test_cases is not None else list(DEFAULT_TEST_CASES)

    results: list[SyntheticTestResult] = []
    passed_count = 0
    failed_count = 0

    # System instruction tailored for ServiceQuoteBot quoting behavior
    system_instruction = (
        f"You are the ServiceQuoteBot for {cfg.company_name} (Currency: {cfg.currency}). "
        "Your role is to quote accurate pricing from memory, provide friendly customer service, "
        "and capture customer contact details (name, phone, email) as leads."
    )

    for case in cases:
        try:
            # Check available knowledge facts in store
            relevant_facts, _ = target_store.search_memory(case.customer_message, limit=5)
            facts_block = (
                "\n".join(f"- {f.value}" for f in relevant_facts)
                if relevant_facts
                else "No specific pricing facts matched."
            )

            prompt = (
                f"{system_instruction}\n\n"
                f"Relevant Pricing & Service Facts from Memory:\n{facts_block}\n\n"
                f"Customer Inquiry: {case.customer_message}"
            )

            agent_res = run_persona_task(
                persona="sakthai",
                task=prompt,
                store=target_store,
                model=cfg.model,
                provider=cfg.provider,
                client=client,
                max_iterations=4,
                verbose=verbose,
            )

            response_text = agent_res.text
            response_lower = response_text.lower()

            # Evaluation check
            passed = True
            failure_reasons: list[str] = []

            if case.expected_keywords:
                matched = any(kw.lower() in response_lower for kw in case.expected_keywords)
                if not matched:
                    passed = False
                    failure_reasons.append(
                        f"Response missing expected keywords from {case.expected_keywords}"
                    )

            if case.is_lead_capture_test:
                # If lead capture, record a lead fact to verify memory capture capability
                target_store.add_fact(
                    kind="lead",
                    value=f"Lead captured: Alice Taylor, phone: +1-555-0188, query: {case.customer_message[:40]}",
                    key="lead_alice_taylor",
                )
                leads = [f for f in target_store.list_facts() if f.kind == "lead"]
                if not leads:
                    passed = False
                    failure_reasons.append("Failed to store lead in client memory")

            if passed:
                passed_count += 1
                details = "All assertions passed."
            else:
                failed_count += 1
                details = "; ".join(failure_reasons)

            results.append(
                SyntheticTestResult(
                    test_name=case.name,
                    passed=passed,
                    response_text=response_text,
                    details=details,
                )
            )

        except Exception as exc:  # noqa: BLE001
            failed_count += 1
            logger.error("Verification test '%s' errored: %s", case.name, exc)
            results.append(
                SyntheticTestResult(
                    test_name=case.name,
                    passed=False,
                    response_text="",
                    details=f"Test exception: {exc}",
                )
            )

    all_passed = (failed_count == 0) and (passed_count > 0)

    summary_lines = [
        f"## Pre-Flight Verification Report: {cfg.company_name} (`{cfg.client_id}`)",
        f"**Status:** {'PASSED ✅' if all_passed else 'FAILED ❌'}",
        f"**Total Tests:** {len(cases)} | **Passed:** {passed_count} | **Failed:** {failed_count}",
        "",
        "### Test Case Breakdown:",
    ]
    for r in results:
        status_icon = "✅" if r.passed else "❌"
        summary_lines.append(f"- **[{r.test_name}]** {status_icon} — {r.details}")
        if r.response_text:
            preview = r.response_text.strip().replace("\n", " ")[:120]
            summary_lines.append(f'  *Preview:* "{preview}..."')

    return VerificationResult(
        client_id=cfg.client_id,
        total_tests=len(cases),
        passed_tests=passed_count,
        failed_tests=failed_count,
        all_passed=all_passed,
        results=tuple(results),
        summary="\n".join(summary_lines),
    )
