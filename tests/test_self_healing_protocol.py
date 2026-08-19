"""Unit and integration tests for Self-Healing Multi-Agent Recovery Protocol."""

import tempfile
import unittest
from pathlib import Path

from sakthai.healing.dlq import DeadLetterQueue
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


if __name__ == "__main__":
    unittest.main()
