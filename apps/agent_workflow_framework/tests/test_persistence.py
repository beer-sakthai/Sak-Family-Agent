"""Unit tests for agent_workflow.persistence RunHistoryStore / HistoryStore module."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from agent_workflow.models import (
    RunHistory,
    RunStatus,
    StepResult,
    StepStatus,
)
from agent_workflow.persistence import (
    HistoryStore,
    RunHistoryStore,
    ExecutionStore,
    RunNotFoundError,
    RunCorruptedError,
    PersistenceError,
    save_run_history,
    get_run_history,
    load_run_history,
    list_runs,
    delete_run_history,
    get_step_result,
    get_step_output,
)


class TestHistoryStore(unittest.TestCase):
    """Test suite for HistoryStore log persistence and execution run retrieval."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "workflow_runs"
        self.store = HistoryStore(storage_dir=str(self.storage_dir))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_directory_auto_creation(self):
        new_dir = Path(self.temp_dir.name) / "auto_created_dir"
        self.assertFalse(new_dir.exists())
        store = HistoryStore(storage_dir=str(new_dir))
        self.assertTrue(new_dir.exists())
        history = RunHistory(
            run_id="run_001",
            workflow_name="test_wf",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
        )
        saved_path = store.save_run_history(history)
        self.assertTrue(Path(saved_path).exists())

    def test_save_and_load_run_history_roundtrip(self):
        res1 = StepResult(
            step_id="step1",
            status=StepStatus.COMPLETED,
            output={"result": 100},
            attempts=1,
            start_time="2026-08-01T12:00:00Z",
            end_time="2026-08-01T12:00:01Z",
        )
        history = RunHistory(
            run_id="run_roundtrip",
            workflow_name="roundtrip_wf",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
            end_time="2026-08-01T12:00:02Z",
            step_results={"step1": res1},
        )
        self.store.save_run_history(history)

        loaded = self.store.load_run_history("run_roundtrip")
        self.assertEqual(loaded.run_id, history.run_id)
        self.assertEqual(loaded.workflow_name, history.workflow_name)
        self.assertEqual(loaded.status, RunStatus.COMPLETED)
        self.assertIn("step1", loaded.step_results)
        self.assertEqual(loaded.step_results["step1"].status, StepStatus.COMPLETED)
        self.assertEqual(loaded.step_results["step1"].output, {"result": 100})

    def test_enum_serialization_fidelity(self):
        history = RunHistory(
            run_id="run_enum",
            workflow_name="enum_wf",
            status=RunStatus.FAILED,
            start_time="2026-08-01T12:00:00Z",
        )
        res = StepResult(
            step_id="s1",
            status=StepStatus.FAILED,
            error="Connection timeout",
            attempts=3,
        )
        history.add_step_result(res)
        self.store.save_run_history(history)

        file_path = self.storage_dir / "run_enum.json"
        raw_json = json.loads(file_path.read_text(encoding="utf-8"))
        self.assertEqual(raw_json["status"], "FAILED")
        self.assertEqual(raw_json["step_results"]["s1"]["status"], "FAILED")

        loaded = self.store.load_run_history("run_enum")
        self.assertIsInstance(loaded.status, RunStatus)
        self.assertIsInstance(loaded.step_results["s1"].status, StepStatus)

    def test_custom_types_serialization(self):
        history = RunHistory(
            run_id="run_custom_types",
            workflow_name="custom_wf",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
        )
        res = StepResult(
            step_id="s1",
            status=StepStatus.COMPLETED,
            output={
                "date": datetime(2026, 8, 1, 12, 0, 0),
                "path": Path("/tmp/foo"),
                "set_data": {1, 2, 3},
                "tuple_data": (10, 20),
            },
        )
        history.add_step_result(res)
        self.store.save_run_history(history)

        loaded = self.store.load_run_history("run_custom_types")
        self.assertIn("s1", loaded.step_results)
        output = loaded.step_results["s1"].output
        self.assertEqual(output["path"], "/tmp/foo")
        self.assertEqual(sorted(output["set_data"]), [1, 2, 3])
        self.assertEqual(output["tuple_data"], [10, 20])

    def test_list_runs(self):
        self.assertEqual(self.store.list_runs(), [])
        h1 = RunHistory(run_id="run1", workflow_name="w1", status=RunStatus.COMPLETED, start_time="2026-08-01T12:00:00Z")
        h2 = RunHistory(run_id="run2", workflow_name="w2", status=RunStatus.FAILED, start_time="2026-08-01T12:00:05Z")
        self.store.save_run_history(h1)
        self.store.save_run_history(h2)

        runs = self.store.list_runs()
        self.assertEqual(len(runs), 2)
        # Should be ordered start_time descending: run2 first, then run1
        self.assertEqual(runs[0].run_id, "run2")
        self.assertEqual(runs[1].run_id, "run1")

    def test_delete_run_history(self):
        history = RunHistory(run_id="run_del", workflow_name="wf", status=RunStatus.COMPLETED, start_time="2026-08-01T12:00:00Z")
        self.store.save_run_history(history)
        self.assertTrue(self.store.delete_run_history("run_del"))
        self.assertFalse(self.store.delete_run_history("run_del"))

        with self.assertRaises(RunNotFoundError):
            self.store.load_run_history("run_del")

    def test_get_step_result_and_output(self):
        res1 = StepResult(step_id="s1", status=StepStatus.COMPLETED, output={"val": 42})
        history = RunHistory(run_id="run_query", workflow_name="wf", status=RunStatus.COMPLETED, start_time="2026-08-01T12:00:00Z", step_results={"s1": res1})
        self.store.save_run_history(history)

        step_res = self.store.get_step_result("run_query", "s1")
        self.assertEqual(step_res.step_id, "s1")
        self.assertEqual(step_res.output, {"val": 42})

        step_out = self.store.get_step_output("run_query", "s1")
        self.assertEqual(step_out, {"val": 42})

        with self.assertRaises(KeyError):
            self.store.get_step_result("run_query", "nonexistent_step")

    def test_atomic_write_safety(self):
        history = RunHistory(
            run_id="run_atomic",
            workflow_name="atomic_wf",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
        )
        saved_path = self.store.save_run_history(history)
        self.assertTrue(os.path.exists(saved_path))
        # Ensure no leftover temp files (.tmp) in storage_dir
        tmp_files = list(self.storage_dir.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)

    def test_load_nonexistent_run_id(self):
        with self.assertRaises((RunNotFoundError, FileNotFoundError)):
            self.store.load_run_history("nonexistent_run_id_999")

    def test_load_corrupted_json(self):
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        bad_file = self.storage_dir / "bad_run.json"
        bad_file.write_text("{ invalid json content }", encoding="utf-8")

        with self.assertRaises((RunCorruptedError, ValueError)):
            self.store.load_run_history("bad_run")

    def test_overwrite_existing_run(self):
        history = RunHistory(
            run_id="run_overwrite",
            workflow_name="wf",
            status=RunStatus.RUNNING,
            start_time="2026-08-01T12:00:00Z",
        )
        self.store.save_run_history(history)

        # Update status to COMPLETED and save
        history.status = RunStatus.COMPLETED
        history.end_time = "2026-08-01T12:00:05Z"
        self.store.save_run_history(history)

        loaded = self.store.load_run_history("run_overwrite")
        self.assertEqual(loaded.status, RunStatus.COMPLETED)
        self.assertEqual(loaded.end_time, "2026-08-01T12:00:05Z")

    def test_path_traversal_prevention(self):
        with self.assertRaises(ValueError):
            self.store.load_run_history("../../../etc/passwd")

    def test_class_aliases(self):
        self.assertIs(HistoryStore, RunHistoryStore)
        self.assertIs(ExecutionStore, RunHistoryStore)

    def test_module_convenience_functions(self):
        history = RunHistory(run_id="run_conv", workflow_name="wf", status=RunStatus.COMPLETED, start_time="2026-08-01T12:00:00Z")
        res = StepResult(step_id="s1", status=StepStatus.COMPLETED, output={"conv": True})
        history.add_step_result(res)

        save_run_history(history, storage_dir=self.storage_dir)

        loaded = get_run_history("run_conv", storage_dir=self.storage_dir)
        self.assertEqual(loaded.run_id, "run_conv")

        loaded_alias = load_run_history("run_conv", storage_dir=self.storage_dir)
        self.assertEqual(loaded_alias.run_id, "run_conv")

        runs = list_runs(storage_dir=self.storage_dir)
        self.assertEqual(len(runs), 1)

        out = get_step_output("run_conv", "s1", storage_dir=self.storage_dir)
        self.assertEqual(out, {"conv": True})

        step_res = get_step_result("run_conv", "s1", storage_dir=self.storage_dir)
        self.assertEqual(step_res.step_id, "s1")

        deleted = delete_run_history("run_conv", storage_dir=self.storage_dir)
        self.assertTrue(deleted)


if __name__ == "__main__":
    unittest.main()
