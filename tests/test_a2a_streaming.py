# tests/test_a2a_streaming.py
import asyncio

import pytest

from sakthai.a2a.models import ChunkType, StreamChunk
from sakthai.a2a.streaming import A2AMeshBroker


@pytest.mark.asyncio
async def test_streaming_broker_publish_and_subscribe():
    broker = A2AMeshBroker()
    queue = broker.subscribe(persona="saksee")

    chunk = StreamChunk(
        seq=0,
        persona="saksee",
        turn=1,
        chunk_type=ChunkType.TOKEN,
        delta="Hello from SakSee",
    )
    published_chunk = await broker.publish_chunk(chunk)
    assert published_chunk.seq == 1

    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received.seq == 1
    assert received.delta == "Hello from SakSee"


@pytest.mark.asyncio
async def test_streaming_broker_sse_generator():
    broker = A2AMeshBroker()
    queue = broker.subscribe()

    chunk = StreamChunk(
        seq=0,
        persona="sakking",
        turn=1,
        chunk_type=ChunkType.TOOL_CALL,
        delta="ast_security_scan",
    )
    await broker.publish_chunk(chunk)

    gen = broker.sse_generator(queue)
    sse_text = await anext(gen)
    assert "id: 1" in sse_text
    assert "event: agent_delta" in sse_text
    assert "ast_security_scan" in sse_text


def test_a2a_models_and_consensus():
    from sakthai.a2a.models import ConsensusSession, VoteBallot, VoteChoice

    chunk = StreamChunk(
        seq=1,
        persona="SakSee",
        turn=1,
        chunk_type=ChunkType.VOTE,
        delta="approve",
    )
    chunk_dict = chunk.to_dict()
    assert chunk_dict["chunk_type"] == "vote"
    assert "timestamp" in chunk_dict

    session = ConsensusSession(
        session_id="sess_1",
        topic="Architecture Refactor",
        domain="core",
        min_ballots=2,
    )

    b1 = VoteBallot(
        session_id="sess_1",
        persona="SakSit",
        choice=VoteChoice.APPROVE,
        weight=1.0,
    )
    b2 = VoteBallot(
        session_id="sess_1",
        persona="SakKing",
        choice=VoteChoice.APPROVE,
        weight=1.0,
    )
    session.add_ballot(b1)
    assert not session.is_resolved()
    session.add_ballot(b2)
    assert session.is_resolved()
    assert session.outcome == "APPROVED"

    sess_dict = session.to_dict()
    assert sess_dict["outcome"] == "APPROVED"
    assert len(sess_dict["ballots"]) == 2

    # Test SakThai Veto
    veto_session = ConsensusSession(
        session_id="sess_veto",
        topic="Risky Change",
        domain="security",
        min_ballots=5,
    )
    veto_ballot = VoteBallot(
        session_id="sess_veto",
        persona="SakThai",
        choice=VoteChoice.VETO,
    )
    veto_session.add_ballot(veto_ballot)
    assert veto_session.is_resolved()
    assert veto_session.outcome == "VETOED"
