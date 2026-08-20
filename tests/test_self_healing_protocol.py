"""Unit and integration tests for Self-Healing Multi-Agent Recovery Protocol."""

import tempfile
import unittest
from pathlib import Path

from sakthai.healing.circuit_breaker import DynamicCircuitBreaker
from sakthai.healing.dlq import DeadLetterQueue
from sakthai.healing.models import CircuitState, IncidentEnvelope, classify_exception
from sakthai.healing.snapshot import MemorySnapshotManager
from sakthai.healing.supervisor import ErrorSeverity, SelfHealingSupervisor
from sakthai.memory.store import MemoryStore


class TestDeadLetterQueue(unittest.TestCase):
    """Test persistent Dead-Letter Queue."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_recovery.db"
        self.dlq = DeadLetterQueue(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_enqueue_and_list_pending(self):
        item_id = self.dlq.enqueue(
            persona="SakSee",
            action="Browse HuggingFace Spaces",
            payload={"space": "sakthai/vision-agent"},
            error=RuntimeError("HTTP 429 Rate Limit Exceeded"),
        )
        self.assertTrue(item_id.startswith("dlq_"))

        pending = self.dlq.list_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].persona, "SakSee")
        self.assertEqual(pending[0].status, "pending")
        self.assertEqual(pending[0].error_type, "RuntimeError")

    def test_retry_failure_and_quarantine(self):
        item_id = self.dlq.enqueue(
            persona="SakKing",
            action="AST Security Check",
            payload={"target": "main.py"},
            error=ValueError("Invalid AST node"),
            max_retries=2,
        )

        # 1st failure
        self.dlq.record_retry_failure(item_id, "Retry 1 failed")
        item = self.dlq.get_item(item_id)
        self.assertEqual(item.retry_count, 1)
        self.assertEqual(item.status, "pending")

        # 2nd failure -> hits max_retries (2) -> status becomes quarantined
        self.dlq.record_retry_failure(item_id, "Retry 2 failed")
        item = self.dlq.get_item(item_id)
        self.assertEqual(item.retry_count, 2)
        self.assertEqual(item.status, "quarantined")

    def test_mark_replayed(self):
        item_id = self.dlq.enqueue(
            persona="SakSit",
            action="Drafting Docs",
            payload={},
            error=Exception("Network Timeout"),
        )
        self.assertTrue(self.dlq.mark_replayed(item_id))
        item = self.dlq.get_item(item_id)
        self.assertEqual(item.status, "replayed")


class TestMemorySnapshotAndRollback(unittest.TestCase):
    """Test point-in-time snapshot and transactional rollback."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_memory.db"
        self.store = MemoryStore(db_path=self.db_path)
        self.snapshot_mgr = MemorySnapshotManager()

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_checkpoint_and_rollback(self):
        # 1. Store initial stable state
        self.store.add_fact("Initial stable user fact", kind="note", key="user_role")
        self.store.add_observation("Initial stable observation", confidence=0.9)

        self.assertEqual(len(self.store.list_facts()), 1)
        self.assertEqual(len(self.store.top_observations()), 1)

        # 2. Create checkpoint
        ckpt_id = self.snapshot_mgr.create_checkpoint(self.store, label="pre_task_exec")
        self.assertTrue(ckpt_id.startswith("ckpt_"))

        # 3. Simulate corrupting / aborted writes
        self.store.add_fact("Corrupted partial write", kind="garbage", key="err")
        self.store.add_observation("Corrupted partial observation", confidence=0.1)
        self.assertEqual(len(self.store.list_facts()), 2)
        self.assertEqual(len(self.store.top_observations()), 2)

        # 4. Trigger rollback
        success = self.snapshot_mgr.rollback(self.store, ckpt_id)
        self.assertTrue(success)

        # 5. Verify restored state
        facts = self.store.list_facts()
        observations = self.store.top_observations()
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].value, "Initial stable user fact")
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].summary, "Initial stable observation")


class TestSelfHealingSupervisor(unittest.TestCase):
    """Test central self-healing supervisor classification and remediation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_recovery.db"
        self.dlq = DeadLetterQueue(db_path=self.db_path)
        self.supervisor = SelfHealingSupervisor(dlq=self.dlq)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_error_classification(self):
        self.assertEqual(
            self.supervisor.classify_error(Exception("HTTP 429 Too Many Requests")),
            ErrorSeverity.TRANSIENT,
        )
        self.assertEqual(
            self.supervisor.classify_error(Exception("OperationalError: database is locked")),
            ErrorSeverity.STATE_CORRUPT,
        )
        self.assertEqual(
            self.supervisor.classify_error(Exception("SyntaxError: invalid syntax")),
            ErrorSeverity.FATAL,
        )

    def test_handle_execution_failure_and_replay(self):
        res = self.supervisor.handle_execution_failure(
            persona="SakThai",
            action="Execute Workflow",
            payload={"step": 1},
            error=ConnectionResetError("Connection reset by peer"),
        )
        self.assertTrue(res.remediated)
        self.assertEqual(res.severity, ErrorSeverity.TRANSIENT)
        self.assertIsNotNone(res.dlq_id)

        # Replay DLQ item with mock executor
        replayed_items = []

        def mock_executor(item):
            replayed_items.append(item.item_id)

        ok = self.supervisor.replay_dlq_item(res.dlq_id, mock_executor)
        self.assertTrue(ok)
        self.assertEqual(replayed_items, [res.dlq_id])


class TestDynamicCircuitBreaker(unittest.TestCase):
    """Test dynamic circuit breaker state transitions."""

    def test_state_transitions(self):
        cb = DynamicCircuitBreaker(failure_threshold=2, recovery_time_sec=0.1)
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.allow_execution())

        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failure_count, 1)

        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertFalse(cb.allow_execution())

        import time

        time.sleep(0.15)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        self.assertTrue(cb.allow_execution())

        cb.record_success()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failure_count, 0)

    def test_reset(self):
        cb = DynamicCircuitBreaker(failure_threshold=1)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        cb.reset()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failure_count, 0)


class TestHealingModels(unittest.TestCase):
    """Test incident envelope and classification functions."""

    def test_incident_envelope_to_dict(self):
        envelope = IncidentEnvelope(
            incident_id="inc_123",
            persona="SakThai",
            severity=ErrorSeverity.TRANSIENT,
            error_message="Rate limit 429",
            stack_trace="trace",
        )
        data = envelope.to_dict()
        self.assertEqual(data["incident_id"], "inc_123")
        self.assertEqual(data["severity"], "transient")
        self.assertIn("timestamp", data)

    def test_classify_exceptions(self):
        self.assertEqual(classify_exception("429 Too Many"), ErrorSeverity.TRANSIENT)
        self.assertEqual(classify_exception("connection reset"), ErrorSeverity.TRANSIENT)
        self.assertEqual(classify_exception("sqlite_busy"), ErrorSeverity.STATE_CORRUPT)
        self.assertEqual(classify_exception("unclosed transaction"), ErrorSeverity.STATE_CORRUPT)
        self.assertEqual(classify_exception("syntax error"), ErrorSeverity.FATAL)


class TestMemorySnapshotFileAndRelease(unittest.TestCase):
    """Test MemorySnapshotManager file-based snapshots and release."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_dir = Path(self.temp_dir.name) / "snapshots"
        self.snapshot_mgr = MemorySnapshotManager(backup_dir=self.backup_dir)
        self.db_path = Path(self.temp_dir.name) / "test.db"

        # Create dummy SQLite DB
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE dummy (id INTEGER, val TEXT)")
            conn.execute("INSERT INTO dummy VALUES (1, 'initial')")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_file_snapshot_and_rollback(self):
        ckpt_id = self.snapshot_mgr.create_checkpoint(self.db_path, label="file_test")
        self.assertTrue(ckpt_id.startswith("ckpt_file_test"))
        self.assertEqual(self.snapshot_mgr.active_checkpoints_count, 1)
        self.assertIn(ckpt_id, self.snapshot_mgr.list_checkpoints())

        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO dummy VALUES (2, 'corrupt')")

        # Test rollback from memory cache
        success = self.snapshot_mgr.rollback(self.db_path, ckpt_id)
        self.assertTrue(success)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM dummy").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1], "initial")

        # Test rollback from disk cache after memory cache cleared
        self.snapshot_mgr._snapshots.clear()
        success2 = self.snapshot_mgr.rollback(self.db_path, ckpt_id)
        self.assertTrue(success2)

        self.snapshot_mgr.release_checkpoint(ckpt_id)
        self.assertEqual(self.snapshot_mgr.active_checkpoints_count, 0)

    def test_create_checkpoint_nonexistent_path(self):
        bad_path = Path(self.temp_dir.name) / "does_not_exist.db"
        res = self.snapshot_mgr.create_checkpoint(bad_path)
        self.assertEqual(res, "")

    def test_rollback_nonexistent_checkpoint(self):
        self.assertFalse(self.snapshot_mgr.rollback(self.db_path, "ckpt_nonexistent"))

    def test_rollback_store_error(self):
        # Trigger exception branch on store rollback
        self.assertFalse(self.snapshot_mgr.rollback(None, "ckpt_test"))


class TestDeadLetterQueueAdvanced(unittest.TestCase):
    """Test advanced DLQ operations (peek, list_dead, record_retry_attempt)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_dlq.db"
        self.dlq = DeadLetterQueue(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_enqueue_dlq_item_directly(self):
        from sakthai.healing.models import DLQItem

        item = DLQItem(
            dlq_id="dlq_custom_123",
            incident_id="dlq_custom_123",
            persona="SakKing",
            payload={"key": "val"},
            error_message="Direct Item Error",
        )
        res_id = self.dlq.enqueue(item)
        self.assertEqual(res_id, "dlq_custom_123")

    def test_record_retry_failure_nonexistent(self):
        self.assertFalse(self.dlq.record_retry_failure("nonexistent_id"))

    def test_peek_and_resolve(self):
        item_id = self.dlq.enqueue(
            persona="SakJules",
            action="Deploy Gate",
            payload={"build": 1},
            error="Deployment timed out",
        )
        peeked = self.dlq.peek(limit=10)
        self.assertEqual(len(peeked), 1)
        self.assertEqual(peeked[0].dlq_id, item_id)

        self.assertTrue(self.dlq.resolve(item_id))
        self.assertEqual(len(self.dlq.list_pending()), 0)

    def test_record_retry_attempt_transition_to_dead(self):
        item_id = self.dlq.enqueue(
            persona="SakTan",
            action="Sync DB",
            payload={},
            error="Connection Error",
            max_retries=1,
        )
        ok = self.dlq.record_retry_attempt(item_id)
        self.assertFalse(ok)
        dead = self.dlq.list_dead()
        self.assertEqual(len(dead), 1)

    def test_quarantine_method(self):
        item_id = self.dlq.enqueue(
            persona="SakKing",
            action="Security Check",
            payload={},
            error="Hard failure",
        )
        self.assertTrue(self.dlq.quarantine(item_id))
        item = self.dlq.get_item(item_id)
        self.assertEqual(item.status, "quarantined")


class TestSupervisorHealthAndExceptions(unittest.TestCase):
    """Test supervisor exception handling, rollback hook, and health check."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "supervisor_test.db"
        self.store = MemoryStore(db_path=self.db_path)
        self.dlq = DeadLetterQueue(db_path=self.db_path)
        self.snapshot_mgr = MemorySnapshotManager(backup_dir=Path(self.temp_dir.name) / "snapshots")
        self.supervisor = SelfHealingSupervisor(dlq=self.dlq, snapshot_mgr=self.snapshot_mgr)

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_handle_exception_with_rollback(self):
        self.store.add_fact("Original State", kind="note", key="status")
        ckpt = self.snapshot_mgr.create_checkpoint(self.store, label="sup_test")

        self.store.add_fact("Bad State", kind="error", key="err")

        res = self.supervisor.handle_exception(
            persona="SakThai",
            exception=Exception("DB Error"),
            payload={},
            db_path=None,
            checkpoint_id=ckpt,
        )
        self.assertIsNotNone(res.dlq_id)

    def test_replay_dlq_item_failure(self):
        res = self.supervisor.handle_execution_failure(
            persona="SakSee",
            action="Failing Task",
            payload={},
            error=Exception("Fail"),
        )

        def failing_executor(item):
            raise RuntimeError("Replay execution exploded")

        ok = self.supervisor.replay_dlq_item(res.dlq_id, failing_executor)
        self.assertFalse(ok)

    def test_get_health_status(self):
        status = self.supervisor.get_health_status("SakSit")
        self.assertEqual(status["persona"], "SakSit")
        self.assertEqual(status["circuit_state"], "closed")
        self.assertTrue(status["healthy"])


if __name__ == "__main__":
    unittest.main()
