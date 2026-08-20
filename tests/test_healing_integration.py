# tests/test_healing_integration.py
import sqlite3

from sakthai.healing.models import ErrorSeverity
from sakthai.healing.supervisor import SelfHealingSupervisor


def test_end_to_end_resilience_flow(tmp_path):
    # Setup test memory store
    db_file = tmp_path / "memory.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE facts (id TEXT PRIMARY KEY, content TEXT);")
    conn.execute("INSERT INTO facts VALUES ('fact-1', 'Initial valid state');")
    conn.commit()
    conn.close()

    supervisor = SelfHealingSupervisor(
        dlq=None,
        snapshot_mgr=None,
    )
    cp_id = supervisor.snapshot_mgr.create_checkpoint(db_file, label="e2e_test")
    assert cp_id != ""

    # Mutate state to simulate corruption
    conn = sqlite3.connect(db_file)
    conn.execute("INSERT INTO facts VALUES ('fact-2', 'Corrupt uncommitted fact');")
    conn.commit()
    conn.close()

    # Simulate database lock/corruption error
    corrupt_exc = Exception("sqlite3.OperationalError: database is locked")
    res = supervisor.handle_exception(
        persona="saksee",
        exception=corrupt_exc,
        payload={"action": "save_observation", "data": "failed_data"},
        db_path=db_file,
        checkpoint_id=cp_id,
    )

    assert res.remediated is True
    assert res.severity == ErrorSeverity.STATE_CORRUPT
    assert res.rolled_back is True
    assert res.dlq_id is not None

    # Verify database was restored to pre-checkpoint state
    conn = sqlite3.connect(db_file)
    rows = conn.execute("SELECT * FROM facts").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "fact-1"


def test_circuit_breaker_isolation_and_reopen():
    supervisor = SelfHealingSupervisor()
    cb = supervisor.get_circuit_breaker("saktan")

    # Trip breaker
    for _ in range(3):
        supervisor.handle_exception(
            persona="saktan",
            exception=Exception("503 Service Unavailable"),
            payload={"action": "reconcile_books"},
        )

    assert cb.allow_execution() is False
    health = supervisor.get_health_status("saktan")
    assert health["circuit_state"] == "open"
    assert health["healthy"] is False
