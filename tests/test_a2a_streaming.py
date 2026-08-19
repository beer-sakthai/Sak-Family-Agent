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


# ─── ConsensusEngine tests ────────────────────────────────────────────────────


def test_consensus_engine_full_lifecycle():
    from sakthai.a2a.consensus import ConsensusEngine
    from sakthai.a2a.models import VoteChoice

    engine = ConsensusEngine()
    session = engine.create_session(
        topic="Deploy to prod",
        domain="devops",
        quorum_threshold=0.6,
        min_ballots=2,
        session_id="vote_test_1",
    )
    assert session.session_id == "vote_test_1"

    active = engine.list_active_sessions()
    assert len(active) == 1

    ok1 = engine.submit_vote("vote_test_1", "SakJules", VoteChoice.APPROVE, "LGTM")
    assert ok1 is True
    ok2 = engine.submit_vote("vote_test_1", "SakKing", VoteChoice.APPROVE, "Good")
    assert ok2 is True

    retrieved = engine.get_session("vote_test_1")
    assert retrieved.is_resolved()

    active_after = engine.list_active_sessions()
    assert len(active_after) == 0


def test_consensus_engine_submit_vote_unknown_session():
    from sakthai.a2a.consensus import ConsensusEngine
    from sakthai.a2a.models import VoteChoice

    engine = ConsensusEngine()
    result = engine.submit_vote("nonexistent", "SakSee", VoteChoice.REJECT)
    assert result is False


def test_consensus_engine_get_session_missing_raises():
    from sakthai.a2a.consensus import ConsensusEngine

    engine = ConsensusEngine()
    raised = False
    try:
        engine.get_session("does_not_exist")
    except KeyError:
        raised = True
    assert raised


def test_consensus_engine_domain_weight_fallback():
    from sakthai.a2a.consensus import ConsensusEngine
    from sakthai.a2a.models import VoteChoice

    engine = ConsensusEngine()
    session = engine.create_session(topic="X", domain="unknown_domain", min_ballots=1)
    ok = engine.submit_vote(session.session_id, "SakSee", VoteChoice.APPROVE)
    assert ok is True


# ─── A2AMeshBroker missing branches ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_streaming_broker_unsubscribe():
    broker = A2AMeshBroker()
    queue = broker.subscribe(persona="saksit")
    assert len(broker._subscribers) == 1
    broker.unsubscribe(queue)
    assert len(broker._subscribers) == 0


@pytest.mark.asyncio
async def test_streaming_broker_history_trimming():
    broker = A2AMeshBroker(max_history_size=2)
    for i in range(3):
        chunk = StreamChunk(
            seq=0, persona="saksee", turn=1, chunk_type=ChunkType.TOKEN, delta=f"tok{i}"
        )
        await broker.publish_chunk(chunk)
    assert len(broker._history) == 2


@pytest.mark.asyncio
async def test_streaming_broker_queue_full():
    broker = A2AMeshBroker()
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    broker._subscribers.append((q, None))

    c1 = StreamChunk(seq=0, persona="saksee", turn=1, chunk_type=ChunkType.TOKEN, delta="a")
    await broker.publish_chunk(c1)
    # Queue is now full; second publish must not raise
    c2 = StreamChunk(seq=0, persona="saksee", turn=1, chunk_type=ChunkType.TOKEN, delta="b")
    await broker.publish_chunk(c2)


@pytest.mark.asyncio
async def test_sse_generator_stops_on_stop_reason():
    broker = A2AMeshBroker()
    queue = broker.subscribe()

    chunk = StreamChunk(
        seq=0,
        persona="sakking",
        turn=1,
        chunk_type=ChunkType.TOKEN,
        delta="done",
        stop_reason="end_turn",
    )
    await broker.publish_chunk(chunk)

    results = []
    async for sse in broker.sse_generator(queue):
        results.append(sse)
    assert len(results) == 1
    assert "event: agent_delta" in results[0]


# ─── MemorySnapshotManager error branches ────────────────────────────────────


def test_snapshot_file_backup_restore_error(tmp_path):
    """Triggers the disk-fallback path with a corrupt file (lines 73-83)."""
    import sqlite3

    from sakthai.healing.snapshot import MemorySnapshotManager

    backup_dir = tmp_path / "snaps"
    mgr = MemorySnapshotManager(backup_dir=backup_dir)
    db_path = tmp_path / "db.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE t (id INTEGER)")

    # Create the checkpoint to get a valid checkpoint_id
    ckpt_id = mgr.create_checkpoint(db_path, label="err_test")
    assert ckpt_id

    # Remove from memory so rollback falls through to disk lookup
    mgr._snapshots.pop(ckpt_id, None)
    # Place a corrupt (empty) file where the backup would be found
    fake_backup = backup_dir / f"{ckpt_id}.db"
    fake_backup.parent.mkdir(parents=True, exist_ok=True)
    # Write truncated/corrupt data so sqlite3 backup() fails
    fake_backup.write_bytes(b"\x00\x01\x02corrupt")  # invalid SQLite header

    result = mgr.rollback(db_path, ckpt_id)
    assert result is False


def test_snapshot_memory_store_rollback_error(tmp_path):
    from sakthai.healing.snapshot import MemorySnapshotManager
    from sakthai.memory.store import MemoryStore

    db_path = tmp_path / "mem.db"
    store = MemoryStore(db_path=db_path)
    mgr = MemorySnapshotManager()
    ckpt_id = mgr.create_checkpoint(store, label="mem_err")
    store.close()
    result = mgr.rollback(store, ckpt_id)
    assert result is False


# ─── SelfHealingSupervisor missing branches ──────────────────────────────────


def test_supervisor_rollback_with_store(tmp_path):
    from sakthai.healing.dlq import DeadLetterQueue
    from sakthai.healing.snapshot import MemorySnapshotManager
    from sakthai.healing.supervisor import SelfHealingSupervisor
    from sakthai.memory.store import MemoryStore

    db_path = tmp_path / "sup_test.db"
    store = MemoryStore(db_path=db_path)
    store.add_fact("Stable fact", kind="note", key="state")

    dlq = DeadLetterQueue(db_path=tmp_path / "dlq.db")
    mgr = MemorySnapshotManager(backup_dir=tmp_path / "snaps")
    sup = SelfHealingSupervisor(dlq=dlq, snapshot_mgr=mgr)

    ckpt_id = mgr.create_checkpoint(store, label="pre_exec")
    store.add_fact("Bad write", kind="error", key="err")

    res = sup.handle_execution_failure(
        persona="SakThai",
        action="Execute Workflow",
        payload={"step": 2},
        error=RuntimeError("DB locked"),
        store=store,
        checkpoint_id=ckpt_id,
    )
    assert res.rolled_back is True
    assert "memory_rollback" in res.action_taken
    assert "enqueued_dlq" in res.action_taken


def test_supervisor_replay_dlq_item_not_found(tmp_path):
    from sakthai.healing.dlq import DeadLetterQueue
    from sakthai.healing.supervisor import SelfHealingSupervisor

    dlq = DeadLetterQueue(db_path=tmp_path / "dlq2.db")
    sup = SelfHealingSupervisor(dlq=dlq)

    ok = sup.replay_dlq_item("nonexistent_id", lambda item: None)
    assert ok is False
