"""Typed Sak Family handoff orchestration and specialist routing."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..agent.coordinator import run_parallel_persona_tasks, run_persona_task
from ..agent.loop import AgentResult
from ..memory.store import MemoryStore
from .handoff import (
    AgentName,
    AgentRef,
    ChargeLevel,
    Constraints,
    Correlation,
    Evidence,
    HandoffEnvelope,
    HandoffStatus,
    HandoffValidationError,
    Payload,
    Recovery,
    TaskSpec,
    utc_now,
)


@dataclass(frozen=True)
class AgentRecord:
    """Registry entry for one specialist lane."""

    name: AgentName
    role: str
    lane: str
    deputy_rank: int | None = None

    def ref(self) -> AgentRef:
        return AgentRef(self.name.value, self.role)


@dataclass(frozen=True)
class RoutingRule:
    """Specialist routing contract for a message type."""

    message_type: str
    owner: AgentName
    allowed_senders: tuple[AgentName, ...]
    default_recipient: AgentName
    fallback: AgentName | None = None


AGENT_REGISTRY: dict[str, AgentRecord] = {
    "sakthai": AgentRecord(
        AgentName.SAKTHAI, "Main Lead / Hugging Face Master", "orchestration, Hub, inference"
    ),
    "sakking": AgentRecord(
        AgentName.SAKKING, "General Assistant / Runner", "general execution and coding", 1
    ),
    "saktan": AgentRecord(
        AgentName.SAKTAN,
        "Keeper of Operations & Daily Flow",
        "operations, routines, memory health",
        2,
    ),
    "saksee": AgentRecord(
        AgentName.SAKSEE, "Web / Browser Specialist", "live web, browser and monitoring", 3
    ),
    "saksit": AgentRecord(
        AgentName.SAKSIT, "Social / Content Specialist", "content, model cards and storytelling"
    ),
    "sakjules": AgentRecord(
        AgentName.SAKJULES,
        "GitHub, CI/CD & Automation",
        "quality, security, schedules and delivery",
    ),
}

ROUTING_MATRIX: dict[str, RoutingRule] = {
    "data-request": RoutingRule(
        "data-request", AgentName.SAKSEE, (AgentName.SAKSIT, AgentName.SAKKING), AgentName.SAKSEE
    ),
    "monitoring-result": RoutingRule(
        "monitoring-result", AgentName.SAKSIT, (AgentName.SAKSEE,), AgentName.SAKSIT
    ),
    "rate-limit-ban": RoutingRule(
        "rate-limit-ban", AgentName.SAKTAN, (AgentName.SAKSEE,), AgentName.SAKTAN
    ),
    "hub-draft": RoutingRule(
        "hub-draft", AgentName.SAKTHAI, (AgentName.SAKSIT,), AgentName.SAKTHAI
    ),
    "awaiting-review": RoutingRule(
        "awaiting-review", AgentName.SAKTHAI, (AgentName.SAKSIT,), AgentName.SAKTHAI
    ),
    "hub-approved": RoutingRule(
        "hub-approved", AgentName.SAKTHAI, (AgentName.BEER,), AgentName.SAKTHAI
    ),
    "hub-complete": RoutingRule(
        "hub-complete", AgentName.SAKTHAI, (AgentName.SAKTHAI,), AgentName.SAKTHAI
    ),
    "schedule-request": RoutingRule(
        "schedule-request", AgentName.SAKJULES, (AgentName.SAKTAN,), AgentName.SAKJULES
    ),
    "schedule-confirmed": RoutingRule(
        "schedule-confirmed", AgentName.SAKTAN, (AgentName.SAKJULES,), AgentName.SAKTAN
    ),
    "ci-failure": RoutingRule(
        "ci-failure", AgentName.SAKKING, (AgentName.SAKJULES,), AgentName.SAKKING
    ),
    "ci-stalled": RoutingRule("ci-stalled", AgentName.BEER, (AgentName.SAKJULES,), AgentName.BEER),
    "conflict": RoutingRule("conflict", AgentName.SAKTHAI, tuple(AgentName), AgentName.SAKTHAI),
    "deputy-chain": RoutingRule(
        "deputy-chain",
        AgentName.SAKTHAI,
        (AgentName.SAKTHAI, AgentName.SAKKING, AgentName.SAKTAN),
        AgentName.SAKKING,
    ),
    "cycle-paused": RoutingRule(
        "cycle-paused", AgentName.SAKTAN, (AgentName.SAKSIT, AgentName.SAKTHAI), AgentName.SAKTAN
    ),
    "cycle-interrupted": RoutingRule(
        "cycle-interrupted", AgentName.SAKTHAI, tuple(AgentName), AgentName.SAKTHAI
    ),
}

_TRANSITIONS: dict[HandoffStatus, frozenset[HandoffStatus]] = {
    HandoffStatus.REQUESTED: frozenset(
        {HandoffStatus.ACKNOWLEDGED, HandoffStatus.BLOCKED, HandoffStatus.REJECTED}
    ),
    HandoffStatus.ACKNOWLEDGED: frozenset(
        {
            HandoffStatus.CLAIMED,
            HandoffStatus.IN_PROGRESS,
            HandoffStatus.BLOCKED,
            HandoffStatus.REJECTED,
        }
    ),
    HandoffStatus.CLAIMED: frozenset(
        {
            HandoffStatus.IN_PROGRESS,
            HandoffStatus.COMPLETED,
            HandoffStatus.PAUSED,
            HandoffStatus.BLOCKED,
            HandoffStatus.INTERRUPTED,
        }
    ),
    HandoffStatus.IN_PROGRESS: frozenset(
        {
            HandoffStatus.COMPLETED,
            HandoffStatus.PAUSED,
            HandoffStatus.BLOCKED,
            HandoffStatus.ESCALATED,
            HandoffStatus.INTERRUPTED,
        }
    ),
    HandoffStatus.PAUSED: frozenset({HandoffStatus.IN_PROGRESS, HandoffStatus.BLOCKED}),
    HandoffStatus.BLOCKED: frozenset({HandoffStatus.ACKNOWLEDGED, HandoffStatus.REJECTED}),
    HandoffStatus.INTERRUPTED: frozenset({HandoffStatus.ACKNOWLEDGED, HandoffStatus.BLOCKED}),
    HandoffStatus.ESCALATED: frozenset({HandoffStatus.ACKNOWLEDGED, HandoffStatus.BLOCKED}),
    HandoffStatus.COMPLETED: frozenset(),
    HandoffStatus.REJECTED: frozenset(),
}

_CHARGE_ORDER = {
    ChargeLevel.NONE: 0,
    ChargeLevel.LOW: 1,
    ChargeLevel.ACTIVE: 2,
    ChargeLevel.CRITICAL: 3,
}


def _record_for(agent: str | AgentName) -> AgentRecord:
    name = agent.value if isinstance(agent, AgentName) else agent
    try:
        return AGENT_REGISTRY[name]
    except KeyError as exc:
        if name == AgentName.BEER.value:
            return AgentRecord(AgentName.BEER, "Beer / approval authority", "approval")
        raise HandoffValidationError(f"Unknown registered agent {name!r}") from exc


def _new_id() -> str:
    return f"ho_{uuid.uuid4().hex}"


class HandoffOrchestrator:
    """Create, validate, persist, transition and dispatch typed handoffs."""

    protocol_version = "1.0.0-draft"

    def __init__(
        self,
        *,
        store: MemoryStore | None = None,
        stores: Mapping[str, MemoryStore] | None = None,
        max_depth: int = 4,
    ) -> None:
        self.store = store
        self.stores = dict(stores or {})
        self.max_depth = max_depth
        self._envelopes: dict[str, HandoffEnvelope] = {}

    def route(
        self, message_type: str, sender: str | AgentName, recipient: str | AgentName | None = None
    ) -> AgentRecord:
        """Resolve the specialist owner and enforce sender/recipient boundaries."""

        try:
            rule = ROUTING_MATRIX[message_type]
        except KeyError as exc:
            raise HandoffValidationError(f"No routing rule for {message_type!r}") from exc
        sender_name = AgentName(sender) if isinstance(sender, str) else sender
        if sender_name not in rule.allowed_senders:
            raise HandoffValidationError(
                f"{message_type} cannot be sent by {sender_name.value}; expected one of "
                f"{', '.join(item.value for item in rule.allowed_senders)}"
            )
        target = recipient.value if isinstance(recipient, AgentName) else recipient
        if target is not None and target != rule.default_recipient.value:
            raise HandoffValidationError(
                f"{message_type} must route to {rule.default_recipient.value}, not {target}"
            )
        return _record_for(rule.default_recipient)

    def create(
        self,
        *,
        sender: str | AgentName,
        message_type: str,
        task: TaskSpec,
        payload: Payload,
        recipient: str | AgentName | None = None,
        evidence: Sequence[Evidence] = (),
        constraints: Constraints | None = None,
        recovery: Recovery | None = None,
        parent_handoff_id: str | None = None,
        related_handoff_ids: Sequence[str] = (),
        handoff_id: str | None = None,
    ) -> HandoffEnvelope:
        """Create, validate, persist and index a requested handoff."""

        sender_name = AgentName(sender) if isinstance(sender, str) else sender
        target = self.route(message_type, sender_name, recipient)
        if parent_handoff_id is not None:
            self._check_parent(parent_handoff_id)
        now = utc_now()
        envelope = HandoffEnvelope(
            protocol_version=self.protocol_version,
            handoff_id=handoff_id or _new_id(),
            message_type=message_type,
            status=HandoffStatus.REQUESTED,
            sender=_record_for(sender_name).ref(),
            recipient=(target.ref(),),
            created_at=now,
            updated_at=now,
            correlation=Correlation(parent_handoff_id, tuple(related_handoff_ids)),
            task=task,
            payload=payload,
            evidence=tuple(evidence),
            constraints=constraints or Constraints(),
            recovery=recovery
            or Recovery(True, "request created", "recipient acknowledges ownership"),
        )
        envelope.validate()
        self._envelopes[envelope.handoff_id] = envelope
        self._persist(envelope)
        return envelope

    def transition(
        self,
        envelope: HandoffEnvelope,
        status: HandoffStatus,
        *,
        evidence: Sequence[Evidence] = (),
        recovery: Recovery | None = None,
        current_charge: ChargeLevel = ChargeLevel.ACTIVE,
        approval_refs: Sequence[str] = (),
    ) -> HandoffEnvelope:
        """Advance a handoff through a legal state transition."""

        if status not in _TRANSITIONS[envelope.status]:
            raise HandoffValidationError(
                f"Illegal transition {envelope.status.value} -> {status.value}"
            )
        if _CHARGE_ORDER[current_charge] < _CHARGE_ORDER[envelope.constraints.charge_required]:
            raise HandoffValidationError(
                f"Current charge {current_charge.value} is below required {envelope.constraints.charge_required.value}"
            )
        refs = tuple(approval_refs) or envelope.constraints.approval_refs
        if (
            status == HandoffStatus.COMPLETED
            and envelope.constraints.approval_required
            and not refs
        ):
            raise HandoffValidationError("Completion requires an explicit approval reference")
        if status == HandoffStatus.COMPLETED and not envelope.evidence and not evidence:
            raise HandoffValidationError("Completion requires evidence")
        next_recovery = recovery or envelope.recovery
        next_constraints = envelope.constraints
        if approval_refs:
            next_constraints = Constraints(
                envelope.constraints.charge_required,
                envelope.constraints.approval_required,
                refs,
                envelope.constraints.cost_limit_usd,
            )
        updated = HandoffEnvelope(
            protocol_version=envelope.protocol_version,
            handoff_id=envelope.handoff_id,
            message_type=envelope.message_type,
            status=status,
            sender=envelope.sender,
            recipient=envelope.recipient,
            created_at=envelope.created_at,
            updated_at=utc_now(),
            correlation=envelope.correlation,
            task=envelope.task,
            payload=envelope.payload,
            evidence=envelope.evidence + tuple(evidence),
            constraints=next_constraints,
            recovery=next_recovery,
        )
        updated.validate()
        self._envelopes[updated.handoff_id] = updated
        self._persist(updated)
        return updated

    def get(self, handoff_id: str) -> HandoffEnvelope | None:
        """Return the latest in-process envelope for an id."""

        return self._envelopes.get(handoff_id)

    def dispatch(
        self,
        envelope: HandoffEnvelope,
        *,
        client: Any = None,
        verbose: bool = False,
        max_iterations: int = 8,
    ) -> AgentResult:
        """Dispatch a single-recipient envelope through the existing persona runner."""

        if len(envelope.recipient) != 1:
            raise HandoffValidationError(
                "dispatch handles one recipient; use dispatch_parallel for fan-out"
            )
        recipient = envelope.recipient[0].agent
        result = run_persona_task(
            persona=recipient,
            task=self._prompt(envelope),
            max_iterations=max_iterations,
            client=client,
            verbose=verbose,
        )
        return result

    def dispatch_parallel(
        self,
        envelopes: Sequence[HandoffEnvelope],
        *,
        client: Any = None,
        verbose: bool = False,
        max_iterations: int = 8,
    ) -> list[AgentResult]:
        """Dispatch independent handoffs through the existing parallel runner."""

        tasks = [
            {
                "persona": envelope.recipient[0].agent,
                "task": self._prompt(envelope),
                "max_iterations": max_iterations,
            }
            for envelope in envelopes
            if len(envelope.recipient) == 1
        ]
        if len(tasks) != len(envelopes):
            raise HandoffValidationError("Each parallel handoff must have one primary recipient")
        return run_parallel_persona_tasks(tasks, client=client, verbose=verbose)

    def _prompt(self, envelope: HandoffEnvelope) -> str:
        return json.dumps(envelope.to_dict(), sort_keys=True, indent=2)

    def _persist(self, envelope: HandoffEnvelope) -> None:
        if self.store is None and not self.stores:
            return
        summary = json.dumps(envelope.to_dict(), sort_keys=True, separators=(",", ":"))
        tags = [envelope.message_type, envelope.status.value, envelope.sender.agent]
        tags.extend(item.agent for item in envelope.recipient)
        target_store = self.stores.get(envelope.sender.agent, self.store)
        if target_store is not None:
            target_store.add_fact(summary, kind="handoff", key=envelope.handoff_id, tags=tags)

    def _check_parent(self, parent_handoff_id: str) -> None:
        parent = self._envelopes.get(parent_handoff_id)
        if parent is None:
            raise HandoffValidationError(f"Unknown parent handoff {parent_handoff_id!r}")
        seen: set[str] = set()
        current: HandoffEnvelope | None = parent
        depth = 0
        while current is not None:
            if current.handoff_id in seen:
                raise HandoffValidationError("Handoff parent cycle detected")
            seen.add(current.handoff_id)
            depth += 1
            if depth > self.max_depth:
                raise HandoffValidationError(f"Handoff depth exceeds maximum {self.max_depth}")
            parent_id = current.correlation.parent_handoff_id
            current = self._envelopes.get(parent_id) if parent_id else None


def stable_handoff_fingerprint(envelope: HandoffEnvelope) -> str:
    """Return a deterministic fingerprint for audit and duplicate detection."""

    data = dict(envelope.to_dict())
    data["status"] = HandoffStatus.REQUESTED.value
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


__all__ = [
    "AGENT_REGISTRY",
    "ROUTING_MATRIX",
    "AgentRecord",
    "HandoffEnvelope",
    "HandoffOrchestrator",
    "HandoffStatus",
    "RoutingRule",
    "stable_handoff_fingerprint",
]
