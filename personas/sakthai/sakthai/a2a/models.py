"""Domain models for Cross-Persona A2A Distributed Streaming & Consensus Mesh."""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class ChunkType(enum.StrEnum):
    TOKEN = "token"  # nosec B105
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    VOTE = "vote"


class VoteChoice(enum.StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    VETO = "veto"


@dataclass
class StreamChunk:
    seq: int
    persona: str
    turn: int
    chunk_type: ChunkType
    delta: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    stop_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["chunk_type"] = self.chunk_type.value
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class VoteBallot:
    session_id: str
    persona: str
    choice: VoteChoice
    weight: float = 1.0
    rationale: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["choice"] = self.choice.value
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class ConsensusSession:
    session_id: str
    topic: str
    domain: str
    quorum_threshold: float = 0.6
    min_ballots: int = 3
    ballots: list[VoteBallot] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    outcome: str = "PENDING"  # PENDING, APPROVED, REJECTED, VETOED

    def add_ballot(self, ballot: VoteBallot) -> None:
        self.ballots.append(ballot)
        self.evaluate()

    def evaluate(self) -> None:
        # 1. Check for SakThai VETO immediately
        for b in self.ballots:
            if b.choice == VoteChoice.VETO and b.persona.lower() == "sakthai":
                self.resolved = True
                self.outcome = "VETOED"
                return

        if len(self.ballots) < self.min_ballots:
            return

        approve_weight = sum(b.weight for b in self.ballots if b.choice == VoteChoice.APPROVE)
        reject_weight = sum(b.weight for b in self.ballots if b.choice == VoteChoice.REJECT)
        total_weight = approve_weight + reject_weight

        if total_weight == 0:
            return

        approval_ratio = approve_weight / total_weight
        if approval_ratio >= self.quorum_threshold:
            self.resolved = True
            self.outcome = "APPROVED"
        else:
            self.resolved = True
            self.outcome = "REJECTED"

    def is_resolved(self) -> bool:
        return self.resolved

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "domain": self.domain,
            "quorum_threshold": self.quorum_threshold,
            "min_ballots": self.min_ballots,
            "resolved": self.resolved,
            "outcome": self.outcome,
            "created_at": self.created_at.isoformat(),
            "ballots": [b.to_dict() for b in self.ballots],
        }
