"""Multi-Agent Domain-Weighted Consensus and Quorum Voting Engine."""

from __future__ import annotations

import logging
import uuid

from .models import ConsensusSession, VoteBallot, VoteChoice

logger = logging.getLogger(__name__)

# Domain weight mappings: primary domain specialists get 2.0x weight
DOMAIN_WEIGHTS: dict[str, dict[str, float]] = {
    "security": {
        "sakking": 2.0,
        "sakjules": 2.0,
        "sakthai": 1.5,
        "saksee": 1.0,
        "saksit": 1.0,
        "saktan": 1.0,
    },
    "devops": {
        "sakjules": 2.0,
        "sakking": 1.5,
        "sakthai": 1.5,
        "saksee": 1.0,
        "saksit": 1.0,
        "saktan": 1.0,
    },
    "vision": {
        "saksee": 2.0,
        "saksit": 1.5,
        "sakthai": 1.5,
        "sakking": 1.0,
        "sakjules": 1.0,
        "saktan": 1.0,
    },
    "content": {
        "saksit": 2.0,
        "saksee": 1.5,
        "sakthai": 1.5,
        "sakking": 1.0,
        "sakjules": 1.0,
        "saktan": 1.0,
    },
    "governance": {
        "saktan": 2.0,
        "sakthai": 1.5,
        "sakking": 1.5,
        "sakjules": 1.0,
        "saksee": 1.0,
        "saksit": 1.0,
    },
    "general": {
        "sakthai": 1.5,
        "sakking": 1.0,
        "saksee": 1.0,
        "saksit": 1.0,
        "sakjules": 1.0,
        "saktan": 1.0,
    },
}


class ConsensusEngine:
    """Manages voting sessions, domain weight calculation, and quorum resolution."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConsensusSession] = {}

    def create_session(
        self,
        topic: str,
        domain: str = "general",
        quorum_threshold: float = 0.6,
        min_ballots: int = 3,
        session_id: str | None = None,
    ) -> ConsensusSession:
        sid = session_id or f"vote_{uuid.uuid4().hex[:8]}"
        session = ConsensusSession(
            session_id=sid,
            topic=topic,
            domain=domain,
            quorum_threshold=quorum_threshold,
            min_ballots=min_ballots,
        )
        self._sessions[sid] = session
        return session

    def submit_vote(
        self,
        session_id: str,
        persona: str,
        choice: VoteChoice,
        rationale: str = "",
    ) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False

        domain_weights = DOMAIN_WEIGHTS.get(session.domain, DOMAIN_WEIGHTS["general"])
        weight = domain_weights.get(persona.lower(), 1.0)

        ballot = VoteBallot(
            session_id=session_id,
            persona=persona.lower(),
            choice=choice,
            weight=weight,
            rationale=rationale,
        )
        session.add_ballot(ballot)
        return True

    def get_session(self, session_id: str) -> ConsensusSession:
        if session_id not in self._sessions:
            raise KeyError(f"Voting session {session_id} not found.")
        return self._sessions[session_id]

    def list_active_sessions(self) -> list[ConsensusSession]:
        return [s for s in self._sessions.values() if not s.resolved]
