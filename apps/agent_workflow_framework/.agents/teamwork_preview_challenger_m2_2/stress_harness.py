#!/usr/bin/env python3
"""Empirical Stress Test Harness for Milestone 2 (State Passing & Execution Persistence).

Executes comprehensive stress scenarios against agent_workflow.persistence and agent_workflow.state.
"""

import copy
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime, date
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_workflow.models import (
    RunHistory,
    RunStatus,
    StepResult,
    StepStatus,
)
from agent_workflow.persistence import (
    RunHistoryStore,
    HistoryStore,
    ExecutionStore,
    RunNotFoundError,
    RunCorruptedError,
    PersistenceError,
)
from agent_workflow.state import StateContext, StateInterpolationError


def worker_process_save(storage_dir_str: str, worker_id: int, num_runs: int):
    """Subprocess target function for multi-process stress testing."""
    store = RunHistoryStore(storage_dir_str)
    successes = 0
    for i in range(num_runs):
        run_id = f"proc_run_{worker_id}_{i}"
        history = RunHistory(
            run_id=run_id,
            workflow_name=f"proc_wf_{worker_id}",
            status=RunStatus.COMPLETED if i % 2 == 0 else RunStatus.FAILED,
            start_time="2026-08-01T12:00:00Z",
            end_time="2026-08-01T12:00:01Z",
            step_results={
                "step1": StepResult(
                    step_id="step1",
                    status=StepStatus.COMPLETED,
                    output={"worker": worker_id, "iteration": i, "payload": "x" * 100},
                )
            },
        )
        store.save_run_history(history)
        loaded = store.load_run_history(run_id)
        if loaded.run_id == run_id and loaded.step_results["step1"].output["worker"] == worker_id:
            successes += 1
    return successes


class StressTestHarness:
    def __init__(self):
        self.results = []
        self.temp_dir = tempfile.mkdtemp(prefix="m2_stress_")
        self.storage_dir = Path(self.temp_dir) / "runs"

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def log(self, test_name: str, passed: bool, details: str):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {details}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })

    def run_all(self):
        print("==================================================")
        print("STARTING MILESTONE 2 EMPIRICAL STRESS TEST HARNESS")
        print("==================================================")

        self.test_multithreaded_concurrency()
        self.test_multiprocess_concurrency()
        self.test_concurrent_same_run_write()
        self.test_corrupted_json_recovery()
        self.test_list_runs_skips_corrupted()
        self.test_path_traversal_hardening()
        self.test_nonexistent_directory_handling()
        self.test_large_payload_serialization()
        self.test_atomic_temp_file_cleanup()
        self.test_enum_and_custom_types_fidelity()
        self.test_state_context_deep_stress()
        self.test_state_context_concurrency()

        print("\n==================================================")
        print("STRESS TEST HARNESS SUMMARY")
        print("==================================================")
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        print(f"Total Tests: {total} | Passed: {passed} | Failed: {failed}")
        return failed == 0

    def test_multithreaded_concurrency(self):
        test_name = "Concurrency - Multi-threaded Reads & Writes"
        store = RunHistoryStore(self.storage_dir / "mt_store")
        num_threads = 16
        ops_per_thread = 20
        errors = []

        def worker(thread_idx):
            try:
                for i in range(ops_per_thread):
                    run_id = f"mt_run_{thread_idx}_{i}"
                    history = RunHistory(
                        run_id=run_id,
                        workflow_name=f"wf_{thread_idx}",
                        status=RunStatus.RUNNING,
                        start_time=datetime.now().isoformat(),
                        step_results={
                            "s1": StepResult(step_id="s1", status=StepStatus.RUNNING, output={"thread": thread_idx})
                        }
                    )
                    store.save_run_history(history)

                    # Read back
                    loaded = store.load_run_history(run_id)
                    if loaded.run_id != run_id:
                        errors.append(f"Thread {thread_idx}: run_id mismatch")

                    # Update status
                    history.status = RunStatus.COMPLETED
                    history.step_results["s1"].status = StepStatus.COMPLETED
                    store.save_run_history(history)

                    loaded2 = store.load_run_history(run_id)
                    if loaded2.status != RunStatus.COMPLETED:
                        errors.append(f"Thread {thread_idx}: updated status mismatch")
            except Exception as e:
                errors.append(f"Thread {thread_idx} exception: {e}")

        start_t = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for f in as_completed(futures):
                f.result()
        duration = time.time() - start_t

        passed = len(errors) == 0
        details = f"{num_threads * ops_per_thread * 2} write ops across {num_threads} threads completed in {duration:.2f}s. Errors: {len(errors)}"
        self.log(test_name, passed, details)

    def test_multiprocess_concurrency(self):
        test_name = "Concurrency - Multi-process Atomic File Persistence"
        storage_path = str(self.storage_dir / "mp_store")
        num_procs = 4
        runs_per_proc = 25
        errors = []

        start_t = time.time()
        with ProcessPoolExecutor(max_workers=num_procs) as executor:
            futures = [executor.submit(worker_process_save, storage_path, i, runs_per_proc) for i in range(num_procs)]
            for i, f in enumerate(futures):
                try:
                    res = f.result()
                    if res != runs_per_proc:
                        errors.append(f"Process {i} only completed {res}/{runs_per_proc} ops successfully")
                except Exception as e:
                    errors.append(f"Process {i} raised exception: {e}")
        duration = time.time() - start_t

        # Verify total stored runs
        store = RunHistoryStore(storage_path)
        all_runs = store.list_runs()
        expected_runs = num_procs * runs_per_proc
        passed = len(errors) == 0 and len(all_runs) == expected_runs
        details = f"{len(all_runs)}/{expected_runs} runs saved across {num_procs} processes in {duration:.2f}s. Errors: {len(errors)}"
        self.log(test_name, passed, details)

    def test_concurrent_same_run_write(self):
        test_name = "Concurrency - Contended Writes to Same Run ID"
        store = RunHistoryStore(self.storage_dir / "same_run_store")
        run_id = "contended_run_001"
        num_threads = 10
        updates_per_thread = 10
        errors = []

        # Initialize run
        history = RunHistory(
            run_id=run_id,
            workflow_name="contended_wf",
            status=RunStatus.RUNNING,
            start_time="2026-08-01T12:00:00Z"
        )
        store.save_run_history(history)

        def worker(t_idx):
            for i in range(updates_per_thread):
                try:
                    res = StepResult(
                        step_id=f"step_{t_idx}_{i}",
                        status=StepStatus.COMPLETED,
                        output={"val": t_idx * 1000 + i}
                    )
                    # Load, mutate, save
                    h = store.load_run_history(run_id)
                    h.add_step_result(res)
                    store.save_run_history(h)
                except Exception as e:
                    errors.append(f"Thread {t_idx} iteration {i}: {e}")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        # Check final history read validity
        try:
            final_h = store.load_run_history(run_id)
            passed = len(errors) == 0 and final_h.run_id == run_id
            details = f"Loaded final history with {len(final_h.step_results)} step results. Errors: {len(errors)}"
        except Exception as e:
            passed = False
            details = f"Failed to load final history: {e}"

        self.log(test_name, passed, details)

    def test_corrupted_json_recovery(self):
        test_name = "Corrupted JSON - Exception Handling & Recovery"
        store_dir = self.storage_dir / "corrupt_store"
        store = RunHistoryStore(store_dir)
        errors = []

        # Case 1: Empty file
        empty_file = store_dir / "empty_run.json"
        empty_file.write_text("", encoding="utf-8")
        try:
            store.load_run_history("empty_run")
            errors.append("Empty JSON did not raise RunCorruptedError")
        except RunCorruptedError:
            pass
        except Exception as e:
            errors.append(f"Empty JSON raised wrong exception: {type(e).__name__}")

        # Case 2: Malformed JSON syntax
        bad_syntax_file = store_dir / "bad_syntax.json"
        bad_syntax_file.write_text("{'run_id': 'abc', missing_quotes: true", encoding="utf-8")
        try:
            store.load_run_history("bad_syntax")
            errors.append("Malformed JSON syntax did not raise RunCorruptedError")
        except RunCorruptedError:
            pass
        except Exception as e:
            errors.append(f"Malformed JSON raised wrong exception: {type(e).__name__}")

        # Case 3: Root element is list, not object
        array_root_file = store_dir / "array_root.json"
        array_root_file.write_text("[1, 2, 3]", encoding="utf-8")
        try:
            store.load_run_history("array_root")
            errors.append("Array root JSON did not raise RunCorruptedError")
        except RunCorruptedError:
            pass
        except Exception as e:
            errors.append(f"Array root JSON raised wrong exception: {type(e).__name__}")

        # Case 4: Missing required fields (e.g. missing 'status')
        missing_field_file = store_dir / "missing_fields.json"
        missing_field_file.write_text(json.dumps({"run_id": "r1", "workflow_name": "wf1"}), encoding="utf-8")
        try:
            store.load_run_history("missing_fields")
            errors.append("Missing fields JSON did not raise RunCorruptedError")
        except RunCorruptedError:
            pass
        except Exception as e:
            errors.append(f"Missing fields JSON raised wrong exception: {type(e).__name__}")

        # Case 5: Invalid Enum string value
        invalid_enum_file = store_dir / "invalid_enum.json"
        invalid_enum_file.write_text(json.dumps({
            "run_id": "invalid_enum",
            "workflow_name": "wf",
            "status": "SUPER_DUPER_UNKNOWN",
            "start_time": "2026-08-01T12:00:00Z"
        }), encoding="utf-8")
        try:
            store.load_run_history("invalid_enum")
            errors.append("Invalid enum JSON did not raise RunCorruptedError")
        except RunCorruptedError:
            pass
        except Exception as e:
            errors.append(f"Invalid enum JSON raised wrong exception: {type(e).__name__}")

        passed = len(errors) == 0
        details = f"Tested 5 corruption scenarios. Errors: {errors}"
        self.log(test_name, passed, details)

    def test_list_runs_skips_corrupted(self):
        test_name = "Corrupted JSON - list_runs Resiliency"
        store_dir = self.storage_dir / "list_corrupt_store"
        store = RunHistoryStore(store_dir)

        # Save 2 valid runs
        h1 = RunHistory(run_id="valid_1", workflow_name="wf", status=RunStatus.COMPLETED, start_time="2026-08-01T10:00:00Z")
        h2 = RunHistory(run_id="valid_2", workflow_name="wf", status=RunStatus.FAILED, start_time="2026-08-01T11:00:00Z")
        store.save_run_history(h1)
        store.save_run_history(h2)

        # Inject 2 corrupted runs
        (store_dir / "corrupt_1.json").write_text("invalid json!!!", encoding="utf-8")
        (store_dir / "corrupt_2.json").write_text('{"run_id": "broken"}', encoding="utf-8")

        runs = store.list_runs()
        passed = len(runs) == 2 and {r.run_id for r in runs} == {"valid_1", "valid_2"}
        details = f"Found {len(runs)} valid runs out of 4 total JSON files (2 corrupt skipped)."
        self.log(test_name, passed, details)

    def test_path_traversal_hardening(self):
        test_name = "Path Traversal - Input Sanitization & Security"
        store = RunHistoryStore(self.storage_dir / "path_store")
        malicious_ids = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/shadow",
            "C:/boot.ini",
            "dir/run_1",
            "run\0id",
            "run id with spaces",
            "run_id; rm -rf /",
            "../run_001",
            "run_001/../../secret",
            "",
            None,
        ]

        rejected = 0
        for bad_id in malicious_ids:
            try:
                store.get_run_path(bad_id)
            except ValueError:
                rejected += 1
            except Exception as e:  # noqa: BLE001
                # Any other exception means the input was rejected by an
                # unexpected route — surface it instead of silently counting
                # it as "not rejected" (bandit B110).
                print(f"    unexpected rejection route for {bad_id!r}: {e!r}")

        passed = rejected == len(malicious_ids)
        details = f"Rejected {rejected}/{len(malicious_ids)} path traversal / malformed run_id inputs with ValueError."
        self.log(test_name, passed, details)

    def test_nonexistent_directory_handling(self):
        test_name = "Directory Handling - Auto Creation & Missing Run Lookup"
        deep_dir = self.storage_dir / "nested" / "sub" / "deep_store"
        self.assert_false(deep_dir.exists())

        store = RunHistoryStore(deep_dir)
        self.assert_true(deep_dir.exists())

        h = RunHistory(run_id="deep_run", workflow_name="wf", status=RunStatus.COMPLETED, start_time="2026-08-01T12:00:00Z")
        saved = store.save_run_history(h)
        self.assert_true(saved.exists())

        # Test querying nonexistent run_id
        errors = []
        try:
            store.load_run_history("nonexistent_run_9999")
            errors.append("Loading nonexistent run_id did not raise RunNotFoundError")
        except RunNotFoundError:
            pass

        passed = len(errors) == 0 and saved.exists()
        details = f"Deep nested dir auto-creation succeeded and missing run lookup properly raised RunNotFoundError."
        self.log(test_name, passed, details)

    def test_large_payload_serialization(self):
        test_name = "Payload Scale - Large History & Step Output Serialization"
        store = RunHistoryStore(self.storage_dir / "large_store")
        run_id = "large_payload_run"

        # Construct a 2MB nested dictionary with keys and long strings
        large_dict = {f"key_{i}": f"value_payload_string_{i}_" + ("x" * 100) for i in range(5000)}
        large_dict["nested_array"] = [list(range(100)) for _ in range(50)]

        history = RunHistory(
            run_id=run_id,
            workflow_name="large_payload_wf",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
            end_time="2026-08-01T12:05:00Z",
        )

        for s in range(20):
            res = StepResult(
                step_id=f"large_step_{s}",
                status=StepStatus.COMPLETED,
                output=large_dict,
                attempts=1,
                start_time="2026-08-01T12:00:00Z",
                end_time="2026-08-01T12:00:05Z",
            )
            history.add_step_result(res)

        start_save = time.time()
        saved_path = store.save_run_history(history)
        save_duration = time.time() - start_save
        file_size_mb = saved_path.stat().st_size / (1024 * 1024)

        start_load = time.time()
        loaded = store.load_run_history(run_id)
        load_duration = time.time() - start_load

        passed = (
            loaded.run_id == run_id
            and len(loaded.step_results) == 20
            and len(loaded.step_results["large_step_0"].output["key_0"]) > 100
        )
        details = f"Saved {file_size_mb:.2f}MB JSON in {save_duration:.2f}s, loaded in {load_duration:.2f}s. Roundtrip verified."
        self.log(test_name, passed, details)

    def test_atomic_temp_file_cleanup(self):
        test_name = "Atomic Cleanup - No Residual Temp Files on Exception"
        store_dir = self.storage_dir / "atomic_clean_store"
        store = RunHistoryStore(store_dir)

        # Create invalid history that fails during dataclass/to_dict serialization
        class UnserializableObject:
            pass

        history = RunHistory(
            run_id="fail_atomic_run",
            workflow_name="wf",
            status=RunStatus.RUNNING,
            start_time="2026-08-01T12:00:00Z",
            step_results={
                "s1": StepResult(
                    step_id="s1",
                    status=StepStatus.RUNNING,
                    output={"bad": UnserializableObject()}
                )
            }
        )

        raised = False
        try:
            store.save_run_history(history)
        except Exception:
            raised = True

        tmp_files = list(store_dir.glob("*.tmp"))
        passed = raised and len(tmp_files) == 0
        details = f"Unserializable payload raised exception as expected. Leftover .tmp files in store_dir: {len(tmp_files)}"
        self.log(test_name, passed, details)

    def test_enum_and_custom_types_fidelity(self):
        test_name = "Serialization Fidelity - Enum & Custom Type Roundtrip"
        store = RunHistoryStore(self.storage_dir / "enum_type_store")
        run_id = "type_fidelity_run"

        test_date = datetime(2026, 8, 1, 15, 30, 45)
        test_path = Path("/var/log/syslog")

        history = RunHistory(
            run_id=run_id,
            workflow_name="type_wf",
            status=RunStatus.FAILED,
            start_time="2026-08-01T15:30:00Z",
            end_time="2026-08-01T15:31:00Z",
        )

        res = StepResult(
            step_id="step_types",
            status=StepStatus.SKIPPED,
            output={
                "datetime": test_date,
                "path": test_path,
                "set_val": {10, 20, 30},
                "tuple_val": ("a", "b", "c"),
                "status_enum": StepStatus.FAILED,
            },
            error="Upstream step dependency failed",
            attempts=0
        )
        history.add_step_result(res)

        store.save_run_history(history)
        loaded = store.load_run_history(run_id)

        passed = (
            isinstance(loaded.status, RunStatus)
            and loaded.status == RunStatus.FAILED
            and isinstance(loaded.step_results["step_types"].status, StepStatus)
            and loaded.step_results["step_types"].status == StepStatus.SKIPPED
            and loaded.step_results["step_types"].output["path"] == "/var/log/syslog"
            and sorted(loaded.step_results["step_types"].output["set_val"]) == [10, 20, 30]
            and loaded.step_results["step_types"].output["tuple_val"] == ["a", "b", "c"]
        )
        details = f"RunStatus enum: {type(loaded.status).__name__}, StepStatus enum: {type(loaded.step_results['step_types'].status).__name__}, Custom types accurately converted."
        self.log(test_name, passed, details)

    def test_state_context_deep_stress(self):
        test_name = "StateContext - Deep Path Resolution & Type Preservation"
        ctx = StateContext()
        errors = []

        ctx.set_step_output("step1", {
            "scalar_int": 999,
            "scalar_float": 3.14159,
            "scalar_bool": False,
            "scalar_none": None,
            "nested": {
                "l1": {
                    "l2": {
                        "value": "deep_target"
                    }
                }
            },
            "items": ["zero", "one", {"nested_in_list": "found_me"}],
            "key.with.dots": 777,
        })

        # Test exact type preservation
        if ctx.interpolate("${steps.step1.output.scalar_int}") != 999 or type(ctx.interpolate("${steps.step1.output.scalar_int}")) is not int:
            errors.append("int type not preserved")
        if ctx.interpolate("${steps.step1.output.scalar_float}") != 3.14159 or type(ctx.interpolate("${steps.step1.output.scalar_float}")) is not float:
            errors.append("float type not preserved")
        if ctx.interpolate("${steps.step1.output.scalar_bool}") is not False:
            errors.append("bool False not preserved")
        if ctx.interpolate("${steps.step1.output.scalar_none}") is not None:
            errors.append("None not preserved")

        # Test deep path resolution
        if ctx.interpolate("${steps.step1.output.nested.l1.l2.value}") != "deep_target":
            errors.append("Deep path resolution failed")

        # Test list index resolution
        if ctx.interpolate("${steps.step1.output.items.0}") != "zero":
            errors.append("List index 0 failed")
        if ctx.interpolate("${steps.step1.output.items.2.nested_in_list}") != "found_me":
            errors.append("List index 2 nested resolution failed")

        # Test direct key with dots
        if ctx.interpolate("${steps.step1.output.key.with.dots}") != 777:
            errors.append("Direct key with dots failed")

        # Test invalid paths and malformed expressions
        invalid_templates = [
            "${steps.nonexistent.output.key}",
            "${steps.step1.output.nonexistent_key}",
            "${steps.step1.output.items.99}",
            "${steps.step1.output.items.abc}",
            "${steps.step1.output.scalar_int.child}",
            "${steps}",
            "${steps.step1}",
            "Invalid prefix ${steps.step1.invalid}",
        ]

        rejected = 0
        for tmpl in invalid_templates:
            try:
                ctx.interpolate(tmpl)
            except (StateInterpolationError, KeyError):
                rejected += 1
            except Exception as e:
                errors.append(f"Template '{tmpl}' raised unexpected exception: {e}")

        if rejected != len(invalid_templates):
            errors.append(f"Rejected {rejected}/{len(invalid_templates)} invalid templates")

        passed = len(errors) == 0
        details = f"Preserved scalar types, resolved deep & list paths, rejected {rejected}/{len(invalid_templates)} invalid expressions. Errors: {errors}"
        self.log(test_name, passed, details)

    def test_state_context_concurrency(self):
        test_name = "StateContext - High Concurrency Thread-Safety"
        ctx = StateContext()
        num_threads = 20
        ops = 50
        errors = []

        def worker(t_id):
            step_id = f"step_thread_{t_id}"
            for i in range(ops):
                try:
                    ctx.set_step_output(step_id, {"counter": i, "data": f"t_{t_id}_v_{i}"})
                    val = ctx.interpolate(f"${{steps.{step_id}.output.counter}}")
                    if type(val) is not int:
                        errors.append(f"Thread {t_id}: interpolated value type is not int")
                except Exception as e:
                    errors.append(f"Thread {t_id} iteration {i}: {e}")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        passed = len(errors) == 0
        details = f"Executed {num_threads * ops} concurrent StateContext mutations & interpolations across {num_threads} threads. Errors: {len(errors)}"
        self.log(test_name, passed, details)

    def assert_true(self, condition):
        if not condition:
            raise AssertionError("Condition is not True")

    def assert_false(self, condition):
        if condition:
            raise AssertionError("Condition is not False")


if __name__ == "__main__":
    harness = StressTestHarness()
    try:
        success = harness.run_all()
        sys.exit(0 if success else 1)
    finally:
        harness.cleanup()
