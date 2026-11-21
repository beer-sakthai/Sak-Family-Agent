"""Typed handoff protocol models for the Sak Family team."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class HandoffValidationError(ValueError):
    """Raised when a handoff envelope violates the protocol contract."""


class AgentName(StrEnum):
    """Registered Sak Family agents."""

    SAKTHAI = "sakthai"
    SAKKING = "sakking"
    SAKTAN = "saktan"
    SAKSEE = "saksee"
    SAKSIT = "saksit"
    SAKJULES = "sakjules"
    BEER = "beer"


class HandoffStatus(StrEnum):
    """Durable handoff lifecycle states."""

    REQUESTED = "requested"
    ACKNOWLEDGED = "acknowledged"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    INTERRUPTED = "interrupted"


class ChargeLevel(StrEnum):
    """Minimum charge level required for an operation."""

    NONE = "none"
    LOW = "low"
    ACTIVE = "active"
    CRITICAL = "critical"


@dataclass(frozen=True)
class AgentRef:
    """An agent identity carried inside an envelope."""

    agent: str
    role: str

    def validate(self) -> None:
        if self.agent not in {a.value for a in AgentName}:
            raise HandoffValidationError(f"Unknown agent {self.agent!r}")
        if not self.role.strip():
            raise HandoffValidationError("Agent role must be non-empty")


@dataclass(frozen=True)
class Correlation:
    """Parent and sibling links for related handoffs."""

    parent_handoff_id: str | None = None
    related_handoff_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskSpec:
    """Observable work objective and acceptance criteria."""

    title: str
    objective: str
    scope: str
    acceptance_criteria: tuple[str, ...]

    def validate(self) -> None:
        if not self.title.strip() or not self.objective.strip():
            raise HandoffValidationError("Task title and objective are required")
        if not self.acceptance_criteria or any(
            not item.strip() for item in self.acceptance_criteria
        ):
            raise HandoffValidationError("At least one non-empty acceptance criterion is required")


@dataclass(frozen=True)
class Payload:
    """Small structured transfer; large content belongs in artifacts."""

    summary: str
    details: str = ""
    artifacts: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.summary.strip():
            raise HandoffValidationError("Payload summary must be non-empty")
        if any("\n" in artifact and not artifact.strip() for artifact in self.artifacts):
            raise HandoffValidationError("Artifact references must be non-empty")


@dataclass(frozen=True)
class Evidence:
    """Auditable evidence attached to a factual or live result."""

    kind: str
    reference: str
    detail: str = ""
    retrieved_at: str | None = None

    def validate(self) -> None:
        if not self.kind.strip() or not self.reference.strip():
            raise HandoffValidationError("Evidence kind and reference are required")
        if self.retrieved_at is not None:
            parse_timestamp(self.retrieved_at)


@dataclass(frozen=True)
class Constraints:
    """Explicit limits; constraints never grant authority."""

    charge_required: ChargeLevel = ChargeLevel.ACTIVE
    approval_required: bool = False
    approval_refs: tuple[str, ...] = ()
    cost_limit_usd: float = 0.0

    def validate(self) -> None:
        if self.cost_limit_usd < 0:
            raise HandoffValidationError("cost_limit_usd cannot be negative")
        if self.approval_refs and not self.approval_required:
            raise HandoffValidationError("Approval references require approval_required=true")


@dataclass(frozen=True)
class Recovery:
    """Checkpoint and exact next action for resumable work."""

    resumable: bool
    checkpoint: str
    next_action: str

    def validate(self, *, required: bool = False) -> None:
        if required and (not self.checkpoint.strip() or not self.next_action.strip()):
            raise HandoffValidationError("Recovery checkpoint and next_action are required")
        if self.resumable and not self.next_action.strip():
            raise HandoffValidationError("Resumable handoffs require recovery.next_action")


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    """Parse a timestamp and require an explicit UTC offset."""

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HandoffValidationError(f"Invalid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise HandoffValidationError("Timestamps must include a UTC offset")
    return parsed


def _tuple(value: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(value or ())


@dataclass(frozen=True)
class HandoffEnvelope:
    """A typed, serializable and append-oriented inter-agent handoff."""

    protocol_version: str
    handoff_id: str
    message_type: str
    status: HandoffStatus
    sender: AgentRef
    recipient: tuple[AgentRef, ...]
    created_at: str
    updated_at: str
    correlation: Correlation
    task: TaskSpec
    payload: Payload
    evidence: tuple[Evidence, ...] = ()
    constraints: Constraints = field(default_factory=Constraints)
    recovery: Recovery = field(default_factory=lambda: Recovery(True, "", ""))

    def validate(self) -> None:
        """Validate the logical protocol invariants."""

        if self.protocol_version != "1.0.0-draft":
            raise HandoffValidationError("Unsupported protocol version")
        if not self.handoff_id.startswith("ho_") or len(self.handoff_id) < 8:
            raise HandoffValidationError("handoff_id must start with ho_ and be stable")
        if not self.message_type or self.message_type != self.message_type.lower():
            raise HandoffValidationError("message_type must be lowercase")
        self.sender.validate()
        if not self.recipient:
            raise HandoffValidationError("At least one recipient is required")
        for recipient in self.recipient:
            recipient.validate()
        parse_timestamp(self.created_at)
        parse_timestamp(self.updated_at)
        self.task.validate()
        self.payload.validate()
        self.constraints.validate()
        for item in self.evidence:
            item.validate()
        self.recovery.validate(
            required=self.status
            in {
                HandoffStatus.PAUSED,
                HandoffStatus.BLOCKED,
                HandoffStatus.INTERRUPTED,
                HandoffStatus.REJECTED,
            }
        )
        if self.sender.agent in {r.agent for r in self.recipient} and len(self.recipient) == 1:
            # Internal checkpoints are valid, but the route remains explicit.
            return

    def to_dict(self) -> dict[str, Any]:
        """Serialize the envelope using the protocol's JSON field names."""

        data = asdict(self)
        data["status"] = self.status.value
        data["recipient"] = list(data["recipient"])
        data["evidence"] = list(data["evidence"])
        data["constraints"]["charge_required"] = self.constraints.charge_required.value
        data["correlation"]["related_handoff_ids"] = list(self.correlation.related_handoff_ids)
        data["task"]["acceptance_criteria"] = list(self.task.acceptance_criteria)
        data["payload"]["artifacts"] = list(self.payload.artifacts)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HandoffEnvelope:
        """Deserialize and validate an envelope mapping."""

        sender_data = data["sender"]
        recipient_data = data["recipient"]
        task_data = data["task"]
        payload_data = data["payload"]
        constraints_data = data.get("constraints", {})
        recovery_data = data.get("recovery", {})
        correlation_data = data.get("correlation", {})
        envelope = cls(
            protocol_version=str(data["protocol_version"]),
            handoff_id=str(data["handoff_id"]),
            message_type=str(data["message_type"]),
            status=HandoffStatus(str(data["status"])),
            sender=AgentRef(str(sender_data["agent"]), str(sender_data["role"])),
            recipient=tuple(
                AgentRef(str(item["agent"]), str(item["role"])) for item in recipient_data
            ),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            correlation=Correlation(
                correlation_data.get("parent_handoff_id"),
                _tuple(correlation_data.get("related_handoff_ids")),
            ),
            task=TaskSpec(
                str(task_data["title"]),
                str(task_data["objective"]),
                str(task_data.get("scope", "")),
                _tuple(task_data.get("acceptance_criteria")),
            ),
            payload=Payload(
                str(payload_data["summary"]),
                str(payload_data.get("details", "")),
                _tuple(payload_data.get("artifacts")),
            ),
            evidence=tuple(
                Evidence(
                    str(item["kind"]),
                    str(item["reference"]),
                    str(item.get("detail", "")),
                    item.get("retrieved_at"),
                )
                for item in data.get("evidence", [])
            ),
            constraints=Constraints(
                ChargeLevel(str(constraints_data.get("charge_required", ChargeLevel.ACTIVE.value))),
                bool(constraints_data.get("approval_required", False)),
                _tuple(constraints_data.get("approval_refs")),
                float(constraints_data.get("cost_limit_usd", 0.0)),
            ),
            recovery=Recovery(
                bool(recovery_data.get("resumable", True)),
                str(recovery_data.get("checkpoint", "")),
                str(recovery_data.get("next_action", "")),
            ),
        )
        envelope.validate()
        return envelope
