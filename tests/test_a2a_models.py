# tests/test_a2a_models.py
from datetime import UTC, datetime

from sakthai.a2a.models import (
    ChunkType,
    ConsensusSession,
    StreamChunk,
    VoteBallot,
    VoteChoice,
)


def test_chunk_type_values():
    assert ChunkType.TOKEN == "token"
    assert ChunkType.TOOL_CALL == "tool_call"
    assert ChunkType.TOOL_RESULT == "tool_result"
    assert ChunkType.VOTE == "vote"


def test_vote_choice_values():
    assert VoteChoice.APPROVE == "approve"
    assert VoteChoice.REJECT == "reject"
    assert VoteChoice.ABSTAIN == "abstain"
    assert VoteChoice.VETO == "veto"


def test_stream_chunk_serialization():
    now = datetime.now(UTC)
    chunk = StreamChunk(
        seq=1,
        persona="saksee",
        turn=2,
        chunk_type=ChunkType.TOKEN,
        delta="Analyzing visual elements...",
        timestamp=now,
        metadata={"model": "gemini-2.5-flash"},
    )
    d = chunk.to_dict()
    assert d["seq"] == 1
    assert d["persona"] == "saksee"
    assert d["chunk_type"] == "token"
    assert d["delta"] == "Analyzing visual elements..."
    assert d["timestamp"] == now.isoformat()


def test_vote_ballot_serialization():
    now = datetime.now(UTC)
    ballot = VoteBallot(
        session_id="session-001",
        persona="sakking",
        choice=VoteChoice.APPROVE,
        weight=2.0,
        rationale="Passed AST guardrails.",
        timestamp=now,
    )
    d = ballot.to_dict()
    assert d["session_id"] == "session-001"
    assert d["persona"] == "sakking"
    assert d["choice"] == "approve"
    assert d["weight"] == 2.0


def test_consensus_session_evaluation():
    session = ConsensusSession(
        session_id="session-002",
        topic="Deploy v2.6.0",
        domain="security",
        quorum_threshold=0.6,
    )
    b1 = VoteBallot("session-002", "sakking", VoteChoice.APPROVE, weight=2.0)
    b2 = VoteBallot("session-002", "sakjules", VoteChoice.APPROVE, weight=2.0)
    b3 = VoteBallot("session-002", "saksee", VoteChoice.REJECT, weight=1.0)
    session.add_ballot(b1)
    session.add_ballot(b2)
    session.add_ballot(b3)

    assert session.is_resolved() is True
    assert session.outcome == "APPROVED"
