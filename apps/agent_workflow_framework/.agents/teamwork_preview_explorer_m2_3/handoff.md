# Handoff Report: Milestone 2 Test Suite Architecture & Coverage Design (`tests/test_state.py` & `tests/test_persistence.py`)

## 1. Observation

Direct observations from codebase inspection and requirements analysis:

- **Original Project Requirements (`ORIGINAL_REQUEST.md`)**:
  - Requirement R1: State passing across steps and execution state persistence.
  - Requirement R3 & Acceptance Criteria: Automated verification suite covering state mutation & passing, executable via standard test discovery.

- **Architecture & Specifications (`PROJECT.md`)**:
  - `agent_workflow/state.py`: Manages thread-safe execution context and state expression resolution using `${steps.ID.output.KEY}` syntax.
  - `agent_workflow/persistence.py`: Manages JSON serialization/deserialization of `RunHistory` and `StepResult` under `.workflow_runs/`.
  - Feature `FEAT-STA-01`: Input/Output State Passing & Interpolation.
  - Feature `FEAT-STA-02`: History Store & Log Persistence.

- **Milestone Scope (`.agents/sub_orch_m2/SCOPE.md`)**:
  - Target test files: `tests/test_state.py` and `tests/test_persistence.py`.
  - Verification requirements: `python -m unittest discover -s tests` must pass cleanly with 0 failures.
  - Verification requirements for state: Test string, dict, list, int, bool, float interpolation, nested path extraction, and invalid reference exceptions (`KeyError`/`StateInterpolationError`).
  - Verification requirements for persistence: Test JSON serialization, deserialization, directory creation, list_runs, and atomic file creation under `.workflow_runs/`.

- **Existing Test Infrastructure (`tests/test_dag.py`, `verify.py`, `tests/engine_fallback.py`)**:
  - `tests/test_dag.py`: Uses standard `unittest.TestCase`, `tempfile.NamedTemporaryFile`, and stdlib assertions (`assertEqual`, `assertTrue`, `assertRaises`, etc.).
  - `verify.py` (lines 49-58): Executes `verify_unittest_suite()` using `subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"])`.
  - `tests/engine_fallback.py`:
    - `StateContext` (lines 74-124): Implements `set_step_output()`, `get_step_output()`, and `interpolate()` supporting full match exact type preservation and string regex substitution (`\$\{steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\}`).
    - `HistoryStore` (lines 223-278): Implements `save_run_history()` and `load_run_history()` reading/writing JSON under `.workflow_runs/`.

---

## 2. Logic Chain

From the observations above, the design for the Milestone 2 test suite (`tests/test_state.py` and `tests/test_persistence.py`) proceeds through the following step-by-step reasoning:

1. **Test Runner & Framework Compatibility**:
   - `verify.py` relies on `python -m unittest discover -s tests`.
   - Therefore, both test files must inherit from `unittest.TestCase`, use standard `test_*` method names, and be placed directly under the `tests/` directory.

2. **Isolation & Cleanliness Strategy**:
   - Tests for `HistoryStore` must not pollute the default `.workflow_runs/` directory or write leftover files into the project root during test runs.
   - Design requires all `HistoryStore` unit tests to instantiate `HistoryStore(storage_dir=temp_dir)` using `tempfile.TemporaryDirectory()`.

3. **`StateContext` Coverage Design (`tests/test_state.py`)**:
   - **Basic State Storage/Retrieval**: `set_step_output()` and `get_step_output()` must properly store dictionary outputs and return an empty dictionary `{}` for unrecorded step IDs.
   - **Scalar Type Preservation**: Single exact expression strings (e.g. `"${steps.step1.output.count}"`) MUST evaluate to their native Python scalar types (`int`, `float`, `bool`, `list`, `dict`, `None`), rather than converting everything to a string.
   - **String Interpolation & Substring Substitution**: Strings containing embedded expressions (e.g. `"Count is ${steps.s1.output.count}"`) or multiple expressions (e.g. `"${steps.s1.output.a} and ${steps.s2.output.b}"`) must convert values to string representation and substitute inline.
   - **Nested Structure Interpolation**: Interpolation must recurse cleanly into dictionary values and list elements at arbitrary depth.
   - **Nested Key Path Extraction**: Expression syntax `${steps.step1.output.user.profile.name}` must navigate nested dicts.
   - **Edge Cases & Error Handling**:
     - Reference to a non-existent step ID -> raises `KeyError` (or `StateInterpolationError`).
     - Reference to a non-existent key or nested key -> raises `KeyError` (or `StateInterpolationError`).
     - Traversing non-dict scalar values (e.g. `${steps.s1.output.scalar_val.sub_key}`) -> raises `KeyError` or `TypeError`.
     - Invalid syntax or malformed template expressions (e.g., missing closing brace `${steps.s1.output.key`) -> returned unchanged or raises syntax error.
     - Non-string primitive templates passed to `interpolate()` (e.g. `123`, `True`, `None`) -> returned unchanged without error.
   - **Thread Safety**: Concurrent `set_step_output` or `interpolate` operations across parallel steps (when using thread locks internally).

4. **`HistoryStore` Coverage Design (`tests/test_persistence.py`)**:
   - **Directory Auto-Creation**: `save_run_history` must create the specified storage directory recursively if it does not already exist.
   - **File Creation & Format**: `save_run_history` must create a `<run_id>.json` file containing valid JSON representing `RunHistory` and `StepResult` structures.
   - **Round-Trip Serialization Fidelity**: `load_run_history` must reconstruct full dataclass instances (`RunHistory` and `StepResult`) with matching `StepStatus` / `RunStatus` enums, timestamps, error fields, and output dicts.
   - **Listing Run Histories (`list_runs`)**: `list_runs()` must return all saved run histories in the storage directory, handling empty directories gracefully.
   - **Atomic File Writing**: `save_run_history` must write to a temporary file first before atomically replacing/renaming to the final `.json` destination, ensuring crash safety.
   - **Invalid Run ID & Error Handling**:
     - `load_run_history` with a non-existent run ID -> raises `FileNotFoundError`.
     - Loading corrupted/malformed JSON file -> raises `ValueError` or `json.JSONDecodeError`.
     - Updating existing run history -> overwrites file cleanly and updates state.

---

## 3. Caveats

- **Implementation In Progress**: Modules `agent_workflow.state` and `agent_workflow.persistence` are being implemented in parallel by Implementer workers. Test cases are designed against the standard interface contracts documented in `PROJECT.md` and `tests/engine_fallback.py`.
- **Exception Class Naming**: `StateContext` may raise standard Python `KeyError` or a custom `StateInterpolationError` subclassing `KeyError`/`Exception`. Test assertions use `assertRaises((KeyError, Exception))` or match against base exception classes to ensure compatibility.
- **Fallback Import Guard**: Test files should include standard import fallbacks if required, but primarily target `agent_workflow.state` and `agent_workflow.persistence`.

---

## 4. Conclusion & Test Suite Design Outline

### 4.1 Test Case Matrix for `tests/test_state.py`

| Test Case Name | Description / Scenario | Expected Outcome |
|---|---|---|
| `test_set_and_get_step_output` | Record step outputs for step `s1` and retrieve via `get_step_output` | Output matches stored dict; unknown step ID returns `{}` |
| `test_interpolate_exact_scalar_types` | Exact pattern match `${steps.s1.output.KEY}` for `int`, `float`, `bool`, `list`, `dict`, `None` | Preserves native scalar Python type (not cast to str) |
| `test_interpolate_string_literal_embedding` | Embedded expression `"Value is ${steps.s1.output.val}"` | Value formatted as string inside surrounding text |
| `test_interpolate_multiple_expressions` | String with multiple expressions `"${steps.s1.output.a} - ${steps.s2.output.b}"` | Both expressions resolved and interpolated |
| `test_interpolate_dict_structures` | Dictionary containing template strings in keys or nested values | Recursively interpolated dictionary returned |
| `test_interpolate_list_structures` | List containing template strings as elements | Recursively interpolated list returned |
| `test_interpolate_nested_key_path` | Expression accessing deep dict path `${steps.s1.output.user.address.zip}` | Correct deeply-nested value returned |
| `test_interpolate_missing_step_id` | Expression referencing step ID `s99` never recorded | Raises `KeyError` / `StateInterpolationError` |
| `test_interpolate_missing_output_key` | Expression referencing missing key `${steps.s1.output.nonexistent}` | Raises `KeyError` / `StateInterpolationError` |
| `test_interpolate_non_dict_traversal` | Deep reference `${steps.s1.output.scalar.child}` where `scalar` is int | Raises `KeyError` / `TypeError` |
| `test_interpolate_primitives_unchanged` | Non-string input primitives (`123`, `3.14`, `True`, `None`) | Returns input primitive unchanged |
| `test_state_context_thread_safety` | Concurrent execution of `set_step_output` and `interpolate` | No race conditions or data corruption |

### 4.2 Test Case Matrix for `tests/test_persistence.py`

| Test Case Name | Description / Scenario | Expected Outcome |
|---|---|---|
| `test_directory_auto_creation` | Save run history when `storage_dir` does not exist | Directory created automatically; JSON file saved |
| `test_save_and_load_run_history_roundtrip` | Save `RunHistory` with multiple `StepResult` entries and load back | Loaded `RunHistory` equals saved instance (status, times, outputs) |
| `test_enum_serialization_fidelity` | Verify `StepStatus` and `RunStatus` string/enum conversion | Enums properly serialized to string and restored as Enum instances |
| `test_list_runs_empty` | Call `list_runs()` on empty storage directory | Returns empty list `[]` |
| `test_list_runs_multiple` | Save multiple run histories and call `list_runs()` | Returns list containing all saved run history records |
| `test_atomic_write_safety` | Inspect file creation during `save_run_history` | File written atomically via temp file rename; no partial file exposure |
| `test_load_nonexistent_run_id` | Call `load_run_history("invalid_run_id")` | Raises `FileNotFoundError` |
| `test_load_corrupted_json` | Create invalid/malformed JSON file in storage dir and load | Raises `ValueError` or `json.JSONDecodeError` |
| `test_overwrite_existing_run` | Update status of existing run and save again | File updated atomically with new status without duplicating |
| `test_path_traversal_prevention` | Pass invalid or malicious path to `load_run_history` | Handled safely or raises `FileNotFoundError`/`ValueError` |

---

### 4.3 Proposed Implementation Blueprint: `tests/test_state.py`

```python
"""Unit tests for agent_workflow.state StateContext module."""

import unittest
from concurrent.futures import ThreadPoolExecutor
from agent_workflow.state import StateContext


class TestStateContext(unittest.TestCase):
    """Test suite for StateContext state passing and template interpolation."""

    def setUp(self):
        self.ctx = StateContext()

    def test_set_and_get_step_output(self):
        output = {"msg": "hello", "code": 0}
        self.ctx.set_step_output("step_1", output)
        self.assertEqual(self.ctx.get_step_output("step_1"), output)
        self.assertEqual(self.ctx.get_step_output("unknown_step"), {})

    def test_interpolate_exact_scalar_types(self):
        self.ctx.set_step_output("step_1", {
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "list_val": [1, 2, 3],
            "dict_val": {"a": 1},
            "none_val": None,
        })
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.int_val}"), 42)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_1.output.int_val}"), int)
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.float_val}"), 3.14)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_1.output.float_val}"), float)
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.bool_val}"), True)
        self.assertIsInstance(self.ctx.interpolate("${steps.step_1.output.bool_val}"), bool)
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.list_val}"), [1, 2, 3])
        self.assertEqual(self.ctx.interpolate("${steps.step_1.output.dict_val}"), {"a": 1})
        self.assertIsNone(self.ctx.interpolate("${steps.step_1.output.none_val}"))

    def test_interpolate_string_literal_embedding(self):
        self.ctx.set_step_output("step_1", {"name": "Alice", "count": 5})
        res = self.ctx.interpolate("User ${steps.step_1.output.name} has ${steps.step_1.output.count} items.")
        self.assertEqual(res, "User Alice has 5 items.")

    def test_interpolate_multiple_expressions(self):
        self.ctx.set_step_output("s1", {"val": 10})
        self.ctx.set_step_output("s2", {"val": 20})
        res = self.ctx.interpolate("${steps.s1.output.val} + ${steps.s2.output.val}")
        self.assertEqual(res, "10 + 20")

    def test_interpolate_dict_structures(self):
        self.ctx.set_step_output("s1", {"host": "localhost", "port": 8080})
        template = {
            "url": "http://${steps.s1.output.host}:${steps.s1.output.port}/api",
            "port_num": "${steps.s1.output.port}",
        }
        expected = {
            "url": "http://localhost:8080/api",
            "port_num": 8080,
        }
        self.assertEqual(self.ctx.interpolate(template), expected)

    def test_interpolate_list_structures(self):
        self.ctx.set_step_output("s1", {"item1": "apple", "item2": "banana"})
        template = ["${steps.s1.output.item1}", "${steps.s1.output.item2}", "cherry"]
        self.assertEqual(self.ctx.interpolate(template), ["apple", "banana", "cherry"])

    def test_interpolate_nested_key_path(self):
        self.ctx.set_step_output("s1", {
            "user": {
                "profile": {
                    "role": "admin"
                }
            }
        })
        res = self.ctx.interpolate("${steps.s1.output.user.profile.role}")
        self.assertEqual(res, "admin")

    def test_interpolate_missing_step_id(self):
        with self.assertRaises(KeyError):
            self.ctx.interpolate("${steps.missing_step.output.key}")

    def test_interpolate_missing_output_key(self):
        self.ctx.set_step_output("s1", {"a": 1})
        with self.assertRaises(KeyError):
            self.ctx.interpolate("${steps.s1.output.b}")

    def test_interpolate_non_dict_traversal(self):
        self.ctx.set_step_output("s1", {"number": 123})
        with self.assertRaises((KeyError, TypeError)):
            self.ctx.interpolate("${steps.s1.output.number.child}")

    def test_interpolate_primitives_unchanged(self):
        self.assertEqual(self.ctx.interpolate(100), 100)
        self.assertEqual(self.ctx.interpolate(3.14), 3.14)
        self.assertEqual(self.ctx.interpolate(True), True)
        self.assertIsNone(self.ctx.interpolate(None))

    def test_state_context_thread_safety(self):
        def worker(i):
            self.ctx.set_step_output(f"step_{i}", {"val": i})
            return self.ctx.interpolate(f"${{steps.step_{i}.output.val}}")

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(worker, range(50)))
        self.assertEqual(results, list(range(50)))


if __name__ == "__main__":
    unittest.main()
```

---

### 4.4 Proposed Implementation Blueprint: `tests/test_persistence.py`

```python
"""Unit tests for agent_workflow.persistence HistoryStore module."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from agent_workflow.models import (
    RunHistory,
    RunStatus,
    StepResult,
    StepStatus,
)
from agent_workflow.persistence import HistoryStore


class TestHistoryStore(unittest.TestCase):
    """Test suite for HistoryStore log persistence and execution run retrieval."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "workflow_runs"
        self.store = HistoryStore(storage_dir=str(self.storage_dir))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_directory_auto_creation(self):
        self.assertFalse(self.storage_dir.exists())
        history = RunHistory(
            run_id="run_001",
            workflow_name="test_wf",
            status=RunStatus.COMPLETED,
            start_time="2026-08-01T12:00:00Z",
        )
        saved_path = self.store.save_run_history(history)
        self.assertTrue(self.storage_dir.exists())
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

    def test_list_runs(self):
        if hasattr(self.store, "list_runs"):
            self.assertEqual(self.store.list_runs(), [])
            h1 = RunHistory(run_id="run1", workflow_name="w1", status=RunStatus.COMPLETED, start_time="2026-08-01T12:00:00Z")
            h2 = RunHistory(run_id="run2", workflow_name="w2", status=RunStatus.FAILED, start_time="2026-08-01T12:00:01Z")
            self.store.save_run_history(h1)
            self.store.save_run_history(h2)

            runs = self.store.list_runs()
            run_ids = [r.run_id if hasattr(r, "run_id") else r["run_id"] for r in runs]
            self.assertIn("run1", run_ids)
            self.assertIn("run2", run_ids)

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
        with self.assertRaises(FileNotFoundError):
            self.store.load_run_history("nonexistent_run_id_999")

    def test_load_corrupted_json(self):
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        bad_file = self.storage_dir / "bad_run.json"
        bad_file.write_text("{ invalid json content }", encoding="utf-8")

        with self.assertRaises((ValueError, json.JSONDecodeError)):
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


if __name__ == "__main__":
    unittest.main()
```

---

## 5. Verification Method

To independently verify the test suite design and implementation:

1. **Execute Unittest Discovery Suite**:
   Run the standard python unittest discovery command from the project root:
   ```bash
   python -m unittest discover -s tests
   ```
   *Expected result*: All tests in `tests/test_dag.py`, `tests/test_state.py`, and `tests/test_persistence.py` run cleanly with 0 failures and 0 errors.

2. **Execute Full Verification Runner**:
   Run the master automated verification runner:
   ```bash
   python verify.py
   ```
   *Expected result*: Phase 1 unittest suite completes with `[PASS]`, and overall runner exits with code 0.

3. **Verify Test Isolation**:
   Check that running `python -m unittest discover -s tests` does NOT leave stray files or directories under `.workflow_runs/` in the project root.
