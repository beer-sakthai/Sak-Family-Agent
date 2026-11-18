"""Tests for the typed Sak Family handoff orchestrator."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from sakthai.agent.loop import AgentResult
from sakthai.memory.store import MemoryStore
from sakthai.team import (
    ROUTING_MATRIX,
    AgentRef,
    ChargeLevel,
    Constraints,
    Correlation,
    Evidence,
    HandoffOrchestrator,
    HandoffStatus,
    HandoffValidationError,
    Payload,
    Recovery,
    TaskSpec,
    stable_handoff_fingerprint,
)
from sakthai.team.handoff import HandoffEnvelope


def task(title: str = "Retrieve current metric") -> TaskSpec:
    return TaskSpec(
        title=title,
        objective="Provide verified data for a model-card paragraph",
        scope="one model page and two metrics",
        acceptance_criteria=(
            "Value is retrieved from an approved source",
            "retrieved_at is recorded",
        ),
    )


def test_registry_contains_six_agents_and_matrix_owners() -> None:
    assert set(ROUTING_MATRIX) >= {"data-request", "monitoring-result", "hub-draft", "hub-approved"}
    assert ROUTING_MATRIX["data-request"].default_recipient.value == "saksee"
    assert ROUTING_MATRIX["hub-draft"].default_recipient.value == "sakthai"


def test_create_round_trips_and_persists_to_sender_shard(tmp_path: Path) -> None:
    with MemoryStore(tmp_path / "saksit.db") as store:
        orchestrator = HandoffOrchestrator(stores={"saksit": store})
        envelope = orchestrator.create(
            sender="saksit",
            message_type="data-request",
            task=task(),
            payload=Payload("Retrieve current download count"),
        )
        assert envelope.status is HandoffStatus.REQUESTED
        assert envelope.recipient[0].agent == "saksee"
        restored = HandoffEnvelope.from_dict(envelope.to_dict())
        assert restored == envelope
        assert store.get_fact_by_key("handoff", envelope.handoff_id) is not None


def test_lifecycle_follows_sequence_and_requires_evidence_for_completion() -> None:
    orchestrator = HandoffOrchestrator()
    envelope = orchestrator.create(
        sender="saksit",
        message_type="data-request",
        task=task(),
        payload=Payload("Retrieve current download count"),
    )
    acknowledged = orchestrator.transition(envelope, HandoffStatus.ACKNOWLEDGED)
    claimed = orchestrator.transition(acknowledged, HandoffStatus.CLAIMED)
    with pytest.raises(HandoffValidationError, match="requires evidence"):
        orchestrator.transition(claimed, HandoffStatus.COMPLETED)
    completed = orchestrator.transition(
        claimed,
        HandoffStatus.COMPLETED,
        evidence=(
            Evidence("url", "https://example.test/model", retrieved_at="2026-11-17T06:00:00Z"),
        ),
        recovery=Recovery(True, "fields validated", "SakSit drafts against verified evidence"),
    )
    assert completed.status is HandoffStatus.COMPLETED
    assert completed.handoff_id == envelope.handoff_id


def test_approval_and_charge_gates_are_enforced() -> None:
    orchestrator = HandoffOrchestrator()
    envelope = orchestrator.create(
        sender="saksit",
        message_type="hub-draft",
        task=task("Prepare Hub draft"),
        payload=Payload("Draft is awaiting Beer review"),
        constraints=Constraints(ChargeLevel.ACTIVE, approval_required=True),
        recovery=Recovery(True, "draft complete", "Beer grants exact-scope approval"),
    )
    acknowledged = orchestrator.transition(envelope, HandoffStatus.ACKNOWLEDGED)
    with pytest.raises(HandoffValidationError, match="below required"):
        orchestrator.transition(acknowledged, HandoffStatus.CLAIMED, current_charge=ChargeLevel.LOW)
    claimed = orchestrator.transition(acknowledged, HandoffStatus.CLAIMED)
    evidence = Evidence("approval", "approval://beer/hub-write-1")
    with pytest.raises(HandoffValidationError, match="approval reference"):
        orchestrator.transition(claimed, HandoffStatus.COMPLETED, evidence=(evidence,))
    completed = orchestrator.transition(
        claimed,
        HandoffStatus.COMPLETED,
        evidence=(evidence,),
        approval_refs=("beer-approval-1",),
    )
    assert completed.constraints.approval_refs == ("beer-approval-1",)


def test_routing_rejects_wrong_specialist_and_illegal_transition() -> None:
    orchestrator = HandoffOrchestrator()
    with pytest.raises(HandoffValidationError, match="cannot be sent"):
        orchestrator.create(
            sender="saksee",
            message_type="data-request",
            task=task(),
            payload=Payload("wrong sender"),
        )
    envelope = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("request")
    )
    with pytest.raises(HandoffValidationError, match="Illegal transition"):
        orchestrator.transition(envelope, HandoffStatus.COMPLETED)


def test_paused_blocked_interrupted_require_recovery() -> None:
    orchestrator = HandoffOrchestrator()
    envelope = orchestrator.create(
        sender="saksee",
        message_type="rate-limit-ban",
        task=task("Stop retries"),
        payload=Payload("HTTP 429"),
    )
    with pytest.raises(HandoffValidationError, match="Recovery"):
        orchestrator.transition(
            envelope,
            HandoffStatus.BLOCKED,
            recovery=Recovery(True, "", ""),
        )
    blocked = orchestrator.transition(
        envelope,
        HandoffStatus.BLOCKED,
        recovery=Recovery(True, "429 observed", "SakTan decides whether to wait or re-scope"),
    )
    assert blocked.recovery.next_action.startswith("SakTan")


def test_parent_depth_and_cycle_protection() -> None:
    orchestrator = HandoffOrchestrator(max_depth=1)
    parent = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("parent")
    )
    child = orchestrator.create(
        sender="saksee",
        message_type="monitoring-result",
        task=task("Return metric"),
        payload=Payload("result"),
        parent_handoff_id=parent.handoff_id,
    )
    assert child.correlation.parent_handoff_id == parent.handoff_id
    with pytest.raises(HandoffValidationError, match="maximum"):
        orchestrator.create(
            sender="saksit",
            message_type="data-request",
            task=task(),
            payload=Payload("too deep"),
            parent_handoff_id=child.handoff_id,
        )


def test_dispatch_uses_existing_persona_runner() -> None:
    orchestrator = HandoffOrchestrator()
    envelope = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("request")
    )
    result = AgentResult(text="ok", iterations=1, stop_reason="end_turn", usage={"total_tokens": 1})
    with patch("sakthai.team.orchestrator.run_persona_task", return_value=result) as runner:
        actual = orchestrator.dispatch(envelope)
    assert actual is result
    assert runner.call_args.kwargs["persona"] == "saksee"
    assert envelope.handoff_id in runner.call_args.kwargs["task"]


def test_schema_accepts_serialized_envelope() -> None:
    schema = json.loads(Path("schemas/inter-agent-handoff.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["handoff_id"]["pattern"].startswith("^ho_")
    assert "recipient" in schema["required"]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (AgentRef("unknown", "role"), "Unknown agent"),
        (AgentRef("saksee", ""), "role must be non-empty"),
    ],
)
def test_component_validation_rejects_invalid_agent_refs(value: AgentRef, message: str) -> None:
    with pytest.raises(HandoffValidationError, match=message):
        value.validate()


def test_component_validation_rejects_empty_task_payload_evidence_and_constraints() -> None:
    with pytest.raises(HandoffValidationError, match="title and objective"):
        TaskSpec("", "objective", "scope", ("criterion",)).validate()
    with pytest.raises(HandoffValidationError, match="acceptance criterion"):
        TaskSpec("title", "objective", "scope", ("",)).validate()
    with pytest.raises(HandoffValidationError, match="Payload summary"):
        Payload("").validate()
    with pytest.raises(HandoffValidationError, match="Artifact references"):
        Payload("summary", artifacts=("\n",)).validate()
    with pytest.raises(HandoffValidationError, match="Evidence kind"):
        Evidence("", "ref").validate()
    with pytest.raises(HandoffValidationError, match="negative"):
        Constraints(cost_limit_usd=-1).validate()
    with pytest.raises(HandoffValidationError, match="approval_required"):
        Constraints(approval_refs=("approval",)).validate()
    with pytest.raises(HandoffValidationError, match="next_action"):
        Recovery(True, "checkpoint", "").validate()


def test_timestamp_and_envelope_identity_validation() -> None:
    orchestrator = HandoffOrchestrator()
    envelope = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("request")
    )
    for field, value, message in [
        ("protocol_version", "bad", "Unsupported protocol"),
        ("handoff_id", "bad", "handoff_id"),
        ("message_type", "Bad Type", "message_type"),
        ("created_at", "not-a-date", "Invalid ISO"),
    ]:
        with pytest.raises(HandoffValidationError, match=message):
            replace(envelope, **{field: value}).validate()
    with pytest.raises(HandoffValidationError, match="UTC offset"):
        replace(envelope, created_at="2026-11-17T06:00:00").validate()
    with pytest.raises(HandoffValidationError, match="recipient"):
        replace(envelope, recipient=()).validate()


def test_recovery_required_for_rejection_and_invalid_route_is_rejected() -> None:
    orchestrator = HandoffOrchestrator()
    with pytest.raises(HandoffValidationError, match="No routing rule"):
        orchestrator.route("not-a-message", "saksit")
    with pytest.raises(HandoffValidationError, match="must route"):
        orchestrator.route("data-request", "saksit", "saktan")
    envelope = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("request")
    )
    with pytest.raises(HandoffValidationError, match="Recovery"):
        orchestrator.transition(envelope, HandoffStatus.REJECTED, recovery=Recovery(True, "", ""))


def test_from_dict_defaults_and_fingerprint_are_stable() -> None:
    orchestrator = HandoffOrchestrator()
    envelope = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("request")
    )
    data = envelope.to_dict()
    data.pop("evidence")
    data.pop("constraints")
    data["correlation"] = {}
    restored = HandoffEnvelope.from_dict(data)
    assert stable_handoff_fingerprint(envelope) == stable_handoff_fingerprint(restored)
    assert orchestrator.get(envelope.handoff_id) is envelope


def test_dispatch_parallel_requires_primary_recipients() -> None:
    orchestrator = HandoffOrchestrator()
    first = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("one")
    )
    second = orchestrator.create(
        sender="saksee", message_type="monitoring-result", task=task(), payload=Payload("two")
    )
    result = AgentResult(text="ok", iterations=1, stop_reason="end_turn", usage={"total_tokens": 1})
    with patch(
        "sakthai.team.orchestrator.run_parallel_persona_tasks", return_value=[result, result]
    ) as runner:
        assert orchestrator.dispatch_parallel([first, second]) == [result, result]
    assert len(runner.call_args.args[0]) == 2
    multi = replace(
        first, recipient=(first.recipient[0], AgentRef("saksee", "Web / Browser Specialist"))
    )
    with pytest.raises(HandoffValidationError, match="one primary recipient"):
        orchestrator.dispatch_parallel([multi])


def test_unknown_parent_and_parent_cycle_are_rejected() -> None:
    orchestrator = HandoffOrchestrator()
    with pytest.raises(HandoffValidationError, match="Unknown parent"):
        orchestrator.create(
            sender="saksit",
            message_type="data-request",
            task=task(),
            payload=Payload("child"),
            parent_handoff_id="ho_missing",
        )
    parent = orchestrator.create(
        sender="saksit", message_type="data-request", task=task(), payload=Payload("parent")
    )
    cyclic = replace(parent, correlation=Correlation(parent.handoff_id))
    orchestrator._envelopes[parent.handoff_id] = cyclic
    with pytest.raises(HandoffValidationError, match="parent cycle"):
        orchestrator.create(
            sender="saksit",
            message_type="data-request",
            task=task(),
            payload=Payload("child"),
            parent_handoff_id=parent.handoff_id,
        )
