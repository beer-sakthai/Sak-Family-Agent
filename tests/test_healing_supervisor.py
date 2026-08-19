# tests/test_healing_supervisor.py
import pytest

from sakthai.healing.dlq import DeadLetterQueue
from sakthai.healing.models import ErrorSeverity
from sakthai.healing.snapshot import MemorySnapshotManager
from sakthai.healing.supervisor import SelfHealingSupervisor


@pytest.fixture
def supervisor(tmp_path):
    dlq = DeadLetterQueue(db_path=tmp_path / "dlq.db")
    snapshot_mgr = MemorySnapshotManager(backup_dir=tmp_path / "snaps")
    return SelfHealingSupervisor(dlq=dlq, snapshot_mgr=snapshot_mgr)


def test_supervisor_handle_transient_error(supervisor):
    result = supervisor.handle_exception(
        persona="saksee",
        exception=Exception("HTTP 429 Rate Limit"),
        payload={"url": "https://api.example.com"},
    )
    assert result.remediated is True
    assert result.severity == ErrorSeverity.TRANSIENT
    assert "enqueued" in result.action_taken
    assert result.dlq_id is not None


def test_supervisor_circuit_breaker_tripping(supervisor):
    cb = supervisor.get_circuit_breaker("sakking")
    for _ in range(3):
        supervisor.handle_exception("sakking", Exception("500 internal"), {"task": "eval"})
    assert cb.allow_execution() is False


def test_supervisor_replay_dlq(supervisor):
    result = supervisor.handle_exception(
        persona="sakthai",
        exception=Exception("Temporary drop"),
        payload={"task": "research"},
    )
    assert result.dlq_id is not None

    executed = []

    def dummy_executor(item):
        executed.append(item.persona)

    replayed = supervisor.replay_dlq_item(result.dlq_id, dummy_executor)
    assert replayed is True
    assert executed == ["sakthai"]
