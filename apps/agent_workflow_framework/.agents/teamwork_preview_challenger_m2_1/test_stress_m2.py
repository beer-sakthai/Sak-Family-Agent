"""Empirical Stress Test Harness for Milestone 2 (State & Persistence).

Executes adversarial stress testing on StateContext, state interpolation,
and RunHistoryStore persistence.
"""

import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_workflow.state import StateContext, StateInterpolationError
from agent_workflow.persistence import (
    RunHistoryStore,
    RunHistory,
    StepResult,
    RunStatus,
    StepStatus,
    RunNotFoundError,
    RunCorruptedError,
    PersistenceError,
)


class TestStateInterpolationStress(unittest.TestCase):
    """Stress tests for StateContext and template interpolation."""

    def setUp(self):
        self.ctx = StateContext()

    def test_multithreaded_concurrent_read_write(self):
        """Stress test high concurrency reads, writes, and interpolations on shared StateContext."""
        num_threads = 50
        iterations_per_thread = 100
        errors = []

        def worker(thread_id):
            try:
                for i in range(iterations_per_thread):
                    step_id = f"step_{thread_id}_{i % 10}"
                    self.ctx.set_step_output(step_id, {
                        "counter": i,
                        "thread": thread_id,
                        "data": {"nested": [i, i * 2, i * 3]}
                    })

                    # Read back direct output
                    out = self.ctx.get_step_output(step_id)
                    assert out["counter"] == i

                    # Interpolate exact scalar
                    val = self.ctx.interpolate(f"${{steps.{step_id}.output.counter}}")
                    assert val == i

                    # Interpolate nested array element
                    elem = self.ctx.interpolate(f"${{steps.{step_id}.output.data.nested.1}}")
                    assert elem == i * 2

                    # Embedded string interpolation
                    msg = self.ctx.interpolate(f"Thread {thread_id} run ${{steps.{step_id}.output.counter}}")
                    assert msg == f"Thread {thread_id} run {i}"

            except Exception as e:
                errors.append((thread_id, e))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        self.assertEqual(errors, [], f"Thread concurrency errors encountered: {errors}")

    def test_deeply_nested_structures_and_array_navigation(self):
        """Test deep nesting (15 levels) and complex array navigation paths."""
        nested_data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": {"l": {"m": {"n": {"o": 42}}}}}}}}}}}}}}}
        self.ctx.set_step_output("deep_step", nested_data)

        res = self.ctx.interpolate("${steps.deep_step.output.a.b.c.d.e.f.g.h.i.j.k.l.m.n.o}")
        self.assertEqual(res, 42)

        # Complex mixture of lists and dicts
        complex_tree = {
            "users": [
                {"id": 101, "roles": ["admin", "editor"]},
                {"id": 102, "roles": ["viewer"], "metadata": {"active": True, "scores": [98.5, 100.0]}}
            ]
        }
        self.ctx.set_step_output("tree_step", complex_tree)

        self.assertEqual(self.ctx.interpolate("${steps.tree_step.output.users.0.id}"), 101)
        self.assertEqual(self.ctx.interpolate("${steps.tree_step.output.users.0.roles.1}"), "editor")
        self.assertEqual(self.ctx.interpolate("${steps.tree_step.output.users.1.metadata.active}"), True)
        self.assertEqual(self.ctx.interpolate("${steps.tree_step.output.users.1.metadata.scores.1}"), 100.0)

    def test_array_index_edge_cases(self):
        """Test array index navigation out-of-bounds, negative index, and non-integer keys on lists."""
        self.ctx.set_step_output("arr_step", {"list": ["zero", "one", "two"]})

        # Out of bounds index
        with self.assertRaises(StateInterpolationError) as cm:
            self.ctx.interpolate("${steps.arr_step.output.list.5}")
        self.assertIn("Index 5 out of range", str(cm.exception))

        # Accessing non-integer property on list
        with self.assertRaises(StateInterpolationError) as cm:
            self.ctx.interpolate("${steps.arr_step.output.list.invalid_key}")
        self.assertIn("Cannot access non-integer key", str(cm.exception))

        # Traversing past primitive value
        self.ctx.set_step_output("prim_step", {"num": 100})
        with self.assertRaises(StateInterpolationError) as cm:
            self.ctx.interpolate("${steps.prim_step.output.num.child}")
        self.assertIn("non-container object", str(cm.exception))

    def test_type_preservation_and_embedded_string_conversion(self):
        """Test exact type preservation vs string embedding JSON conversion."""
        test_payload = {
            "integer": 12345,
            "float_num": 99.99,
            "boolean": False,
            "null_val": None,
            "dict_obj": {"k": "v"},
            "list_arr": [1, 2, "3"],
        }
        self.ctx.set_step_output("types_step", test_payload)

        # Exact matches preserve types
        self.assertIs(type(self.ctx.interpolate("${steps.types_step.output.integer}")), int)
        self.assertIs(type(self.ctx.interpolate("${steps.types_step.output.float_num}")), float)
        self.assertIs(type(self.ctx.interpolate("${steps.types_step.output.boolean}")), bool)
        self.assertIsNone(self.ctx.interpolate("${steps.types_step.output.null_val}"))
        self.assertEqual(self.ctx.interpolate("${steps.types_step.output.dict_obj}"), {"k": "v"})
        self.assertEqual(self.ctx.interpolate("${steps.types_step.output.list_arr}"), [1, 2, "3"])

        # Embedded in string converts objects/lists to JSON strings and primitives to str
        embedded_dict = self.ctx.interpolate("Data: ${steps.types_step.output.dict_obj}")
        self.assertEqual(embedded_dict, 'Data: {"k": "v"}')

        embedded_list = self.ctx.interpolate("List: ${steps.types_step.output.list_arr}")
        self.assertEqual(embedded_list, 'List: [1, 2, "3"]')

        embedded_bool = self.ctx.interpolate("Status: ${steps.types_step.output.boolean}")
        self.assertEqual(embedded_bool, 'Status: False')

        embedded_none = self.ctx.interpolate("Null: ${steps.types_step.output.null_val}")
        self.assertEqual(embedded_none, 'Null: None')

    def test_malformed_and_invalid_template_strings(self):
        """Test detection of malformed ${steps...} expressions."""
        self.ctx.set_step_output("s1", {"val": 10})

        malformed_examples = [
            "Bad ${steps.s1.invalid}",
            "Bad ${steps}",
            "Bad ${steps.s1}",
            "Bad ${steps.s1.input.key}",
            "Bad ${steps.s1.output.}",
            "Bad ${steps.123@step.output.val}",
        ]

        for expr in malformed_examples:
            with self.subTest(expr=expr):
                with self.assertRaises(StateInterpolationError):
                    self.ctx.interpolate(expr)

    def test_missing_steps_and_keys(self):
        """Test exception throwing and inheritance for missing step IDs and keys."""
        with self.assertRaises(StateInterpolationError) as cm:
            self.ctx.interpolate("${steps.nonexistent.output.key}")
        self.assertTrue(issubclass(StateInterpolationError, KeyError))

        self.ctx.set_step_output("s1", {"exist": 1})
        with self.assertRaises(StateInterpolationError) as cm:
            self.ctx.interpolate("${steps.s1.output.missing_key}")
        self.assertTrue(issubclass(StateInterpolationError, KeyError))


class TestPersistenceStoreStress(unittest.TestCase):
    """Stress tests for RunHistoryStore execution persistence."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = RunHistoryStore(storage_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_concurrent_history_saves(self):
        """Stress test concurrent atomic file writes and reads across threads."""
        num_threads = 20
        errors = []

        def worker(tid):
            try:
                run_id = f"concurrent_run_{tid}"
                history = RunHistory(
                    run_id=run_id,
                    workflow_name=f"wf_{tid}",
                    status=RunStatus.RUNNING,
                    start_time="2026-08-01T12:00:00Z",
                )
                for step_idx in range(20):
                    res = StepResult(
                        step_id=f"step_{step_idx}",
                        status=StepStatus.COMPLETED,
                        output={"step": step_idx, "tid": tid},
                    )
                    history.add_step_result(res)
                    self.store.save_run_history(history)

                history.status = RunStatus.COMPLETED
                self.store.save_run_history(history)

                loaded = self.store.load_run_history(run_id)
                assert loaded.status == RunStatus.COMPLETED
                assert len(loaded.step_results) == 20
            except Exception as e:
                errors.append((tid, e))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        self.assertEqual(errors, [], f"Concurrent persistence errors: {errors}")

        # Check no orphaned .tmp files
        tmp_files = list(Path(self.temp_dir.name).glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0, f"Found orphan temp files: {tmp_files}")

    def test_large_history_payload_roundtrip(self):
        """Test performance and serialization of large workflow run history (1,000 steps)."""
        history = RunHistory(
            run_id="large_run_1000",
            workflow_name="large_workflow",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
            end_time="2026-08-01T12:05:00Z",
        )
        for i in range(1000):
            res = StepResult(
                step_id=f"step_{i:04d}",
                status=StepStatus.COMPLETED,
                output={"index": i, "payload": "x" * 500, "metrics": [float(i), i * 1.5]},
                attempts=1,
            )
            history.add_step_result(res)

        saved_path = self.store.save_run_history(history)
        self.assertTrue(os.path.exists(saved_path))

        loaded = self.store.load_run_history("large_run_1000")
        self.assertEqual(len(loaded.step_results), 1000)
        self.assertEqual(loaded.step_results["step_0999"].output["index"], 999)

    def test_path_traversal_and_malformed_ids(self):
        """Test robustness against path traversal attacks in run_id."""
        invalid_ids = [
            "../outside_run",
            "../../etc/passwd",
            "foo/bar",
            "run\\windows\\path",
            "",
            None,
            "run space id",
            "run$id!bad",
        ]

        for bad_id in invalid_ids:
            with self.subTest(bad_id=bad_id):
                with self.assertRaises(ValueError):
                    self.store.get_run_path(bad_id)

    def test_corrupted_json_recovery(self):
        """Test handling of truncated or invalid JSON history files."""
        corrupt_id = "corrupt_run"
        target_path = self.store.get_run_path(corrupt_id)
        target_path.write_text('{"run_id": "corrupt_run", "status": "COMPLETED", "step_results": ', encoding="utf-8")

        with self.assertRaises(RunCorruptedError):
            self.store.load_run_history(corrupt_id)

        # Test JSON containing non-object root (e.g., JSON list)
        list_root_id = "list_root_run"
        target_path_list = self.store.get_run_path(list_root_id)
        target_path_list.write_text('[1, 2, 3]', encoding="utf-8")

        with self.assertRaises(RunCorruptedError):
            self.store.load_run_history(list_root_id)


if __name__ == "__main__":
    unittest.main()
