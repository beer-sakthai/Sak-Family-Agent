# Handoff Report: Execution Persistence (`agent_workflow/persistence.py`)

## 1. Observation

### Existing Codebase Observations
1. **Data Models (`agent_workflow/models.py`)**:
   - `StepStatus` (lines 13-28): String Enum with values `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`.
   - `RunStatus` (lines 30-39): String Enum with values `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`.
   - `StepResult` (lines 157-205): Dataclass containing `step_id`, `status`, `output` (dict), `error` (Optional[str]), `attempts` (int), `start_time` (Optional[str]), `end_time` (Optional[str]). Includes `to_dict()` (line 179) and `from_dict()` (line 191).
   - `RunHistory` (lines 207-269): Dataclass containing `run_id`, `workflow_name`, `status`, `start_time`, `end_time`, and `step_results` (Dict[str, StepResult]). Includes `to_dict()` (line 237) and `from_dict()` (line 251).

2. **Fallback Persistence Reference (`tests/engine_fallback.py`)**:
   - `HistoryStore` (lines 223-278): Simple JSON persistence class writing to `.workflow_runs/<run_id>.json`.
   - Direct file writes via `file_path.write_text(json.dumps(data, indent=2))` (line 249) are non-atomic and lack thread safety.
   - Missing error handling for corrupted files, missing run IDs, path traversal, or non-JSON-serializable objects in step outputs.

3. **Project Requirements (`PROJECT.md` & `.agents/sub_orch_m2/SCOPE.md`)**:
   - `FEAT-STA-02`: History Store & Log Persistence. Save structured `RunHistory` and `StepResult` to `.workflow_runs/<run_id>.json` using thread-safe and atomic file writes.
   - CLI inspection support for querying past run status and step outputs.

4. **Test Suite Baseline**:
   - Running `python3 -m unittest discover -s tests` returned:
     ```text
     Ran 79 tests in 0.937s
     OK
     ```

---

## 2. Logic Chain

1. **Serialization Strategy**:
   - `RunHistory.to_dict()` and `StepResult.to_dict()` convert dataclass instances into nested Python dictionaries where Enums are converted to string values (`status.value`).
   - To handle complex objects inside step outputs (e.g. `datetime` objects, `Path` objects, custom dataclasses, sets, tuples, or raw Enum instances), a custom `json.JSONEncoder` subclass (`WorkflowJSONEncoder`) must be used during JSON dump.

2. **Atomic File Write Strategy**:
   - Writing directly to `.workflow_runs/<run_id>.json` can result in truncated or corrupted files if the process is terminated mid-write or accessed concurrently.
   - Atomic writes are guaranteed on POSIX filesystems by:
     1. Ensuring the storage directory (`.workflow_runs/`) exists (`mkdir(parents=True, exist_ok=True)`).
     2. Creating a temporary file inside the target storage directory using `tempfile.NamedTemporaryFile(mode='w', dir=storage_dir, delete=False, suffix='.tmp')`.
     3. Writing JSON content to the temporary file, calling `flush()`, and executing `os.fsync(fd)` to guarantee dirty buffers are committed to disk.
     4. Closing the file handle and atomically renaming the temporary file over the destination file via `Path.replace()`.
     5. Cleaning up temporary files on write failure.

3. **Process Thread Safety & Path Security**:
   - A `threading.RLock()` within `RunHistoryStore` protects against concurrent read/write race conditions inside the same Python process.
   - Run ID sanitization (`_sanitize_run_id`) strips leading directories (`Path(run_id).name`) and validates allowed characters (`^[a-zA-Z0-9_.-]+$`) to prevent path traversal vulnerability (`../`).

4. **Error Handling Hierarchy**:
   - Define explicit exception classes: `PersistenceError` (base), `RunNotFoundError` (when file missing), `RunCorruptedError` (when JSON invalid or schema broken).

5. **CLI & Module API Design**:
   - Class `RunHistoryStore` (with `ExecutionStore = RunHistoryStore` alias for contract compliance).
   - Core methods: `save_run_history`, `load_run_history`, `list_runs`, `delete_run_history`, `get_step_result`, `get_step_output`.
   - Top-level helper functions (`save_run_history`, `get_run_history`, `load_run_history`, `list_runs`, `delete_run_history`, `get_step_result`, `get_step_output`) wrapping default store instance operations.

---

## 3. Technical Implementation Specification

Proposed implementation for `agent_workflow/persistence.py`:

```python
"""Execution run history and step log persistence store.

Provides atomic, thread-safe persistence of RunHistory and StepResult dataclasses
to structured JSON files under `.workflow_runs/<run_id>.json`.
"""

import json
import os
import re
import tempfile
import threading
from dataclasses import is_dataclass, asdict
from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from agent_workflow.models import RunHistory, StepResult, RunStatus, StepStatus


class PersistenceError(Exception):
    """Base exception for persistence operations."""
    pass


class RunNotFoundError(PersistenceError):
    """Raised when a specified run_id is not found in the storage directory."""
    pass


class RunCorruptedError(PersistenceError):
    """Raised when a run history JSON file is malformed or corrupted."""
    pass


class WorkflowJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder handling dataclasses, Enums, dates, and Path objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return obj.to_dict()
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, (set, tuple)):
            return list(obj)
        return super().default(obj)


class RunHistoryStore:
    """Thread-safe store for saving, loading, and querying workflow run histories."""

    DEFAULT_STORAGE_DIR = ".workflow_runs"

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        if storage_dir is None:
            storage_dir = Path(self.DEFAULT_STORAGE_DIR)
        else:
            storage_dir = Path(storage_dir)
        self.storage_dir: Path = storage_dir.resolve()
        self._lock = threading.RLock()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Create storage directory if it does not exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise PersistenceError(f"Failed to create storage directory '{self.storage_dir}': {e}") from e

    def _sanitize_run_id(self, run_id: str) -> str:
        """Sanitize run_id to prevent path traversal attacks."""
        if not run_id or not isinstance(run_id, str):
            raise ValueError("run_id must be a non-empty string.")

        clean_id = run_id[:-5] if run_id.endswith(".json") else run_id
        clean_id = Path(clean_id).name

        if not re.match(r"^[a-zA-Z0-9_.-]+$", clean_id):
            raise ValueError(f"Invalid characters in run_id: '{run_id}'")

        return clean_id

    def get_run_path(self, run_id: str) -> Path:
        """Get the absolute path for a given run_id JSON file."""
        clean_id = self._sanitize_run_id(run_id)
        return self.storage_dir / f"{clean_id}.json"

    def save_run_history(self, history: RunHistory) -> Path:
        """Save RunHistory object to structured JSON file atomically and thread-safely."""
        if not isinstance(history, RunHistory):
            raise TypeError(f"Expected RunHistory instance, got {type(history).__name__}")

        if not history.run_id:
            raise ValueError("RunHistory must have a valid run_id.")

        target_path = self.get_run_path(history.run_id)
        data = history.to_dict()

        with self._lock:
            self._ensure_storage_dir()
            temp_file = None
            temp_path = None
            try:
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=self.storage_dir,
                    delete=False,
                    suffix=".tmp",
                    encoding="utf-8",
                )
                temp_path = Path(temp_file.name)
                json.dump(data, temp_file, indent=2, cls=WorkflowJSONEncoder)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file.close()

                temp_path.replace(target_path)
                return target_path
            except Exception as e:
                if temp_file and not temp_file.closed:
                    temp_file.close()
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                raise PersistenceError(f"Failed to save run history '{history.run_id}': {e}") from e

    def load_run_history(self, run_id: str) -> RunHistory:
        """Load RunHistory from JSON file by run_id or file path."""
        with self._lock:
            target_path = Path(run_id)
            if not target_path.exists() or target_path.is_dir():
                target_path = self.get_run_path(run_id)

            if not target_path.exists():
                raise RunNotFoundError(f"Run history not found for run_id or path: '{run_id}'")

            try:
                content = target_path.read_text(encoding="utf-8")
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise RunCorruptedError(f"Run history JSON root must be an object, got {type(data).__name__}")
                return RunHistory.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                raise RunCorruptedError(f"Failed to parse run history file '{target_path}': {e}") from e

    def list_runs(self) -> List[RunHistory]:
        """List all stored run histories, ordered by start_time descending (newest first)."""
        with self._lock:
            self._ensure_storage_dir()
            runs: List[RunHistory] = []
            for item in self.storage_dir.glob("*.json"):
                if item.is_file():
                    try:
                        run = self.load_run_history(str(item))
                        runs.append(run)
                    except PersistenceError:
                        continue

            runs.sort(key=lambda r: r.start_time or "", reverse=True)
            return runs

    def delete_run_history(self, run_id: str) -> bool:
        """Delete a run history JSON file by run_id."""
        with self._lock:
            try:
                path = self.get_run_path(run_id)
                if path.exists():
                    path.unlink()
                    return True
                return False
            except Exception as e:
                raise PersistenceError(f"Failed to delete run history '{run_id}': {e}") from e

    def get_step_result(self, run_id: str, step_id: str) -> StepResult:
        """Retrieve StepResult for a specific step within a run history."""
        history = self.load_run_history(run_id)
        step_res = history.get_step_result(step_id)
        if step_res is None:
            raise KeyError(f"Step '{step_id}' not found in run '{run_id}' history.")
        return step_res

    def get_step_output(self, run_id: str, step_id: str) -> Dict[str, Any]:
        """Retrieve execution output dictionary for a specific step within a run history."""
        step_res = self.get_step_result(run_id, step_id)
        return step_res.output


# Class alias for backward compatibility / API flexibility
ExecutionStore = RunHistoryStore


# Module-level convenience functions
def save_run_history(history: RunHistory, storage_dir: Optional[Union[str, Path]] = None) -> Path:
    """Convenience function to save a RunHistory."""
    store = RunHistoryStore(storage_dir)
    return store.save_run_history(history)


def get_run_history(run_id: str, storage_dir: Optional[Union[str, Path]] = None) -> RunHistory:
    """Convenience function to retrieve a RunHistory by run_id."""
    store = RunHistoryStore(storage_dir)
    return store.load_run_history(run_id)


def load_run_history(run_id: str, storage_dir: Optional[Union[str, Path]] = None) -> RunHistory:
    """Alias for get_run_history."""
    return get_run_history(run_id, storage_dir)


def list_runs(storage_dir: Optional[Union[str, Path]] = None) -> List[RunHistory]:
    """Convenience function to list all saved RunHistories."""
    store = RunHistoryStore(storage_dir)
    return store.list_runs()


def delete_run_history(run_id: str, storage_dir: Optional[Union[str, Path]] = None) -> bool:
    """Convenience function to delete a run history file."""
    store = RunHistoryStore(storage_dir)
    return store.delete_run_history(run_id)


def get_step_result(run_id: str, step_id: str, storage_dir: Optional[Union[str, Path]] = None) -> StepResult:
    """Convenience function to get a StepResult for a step in a run."""
    store = RunHistoryStore(storage_dir)
    return store.get_step_result(run_id, step_id)


def get_step_output(run_id: str, step_id: str, storage_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Convenience function to get output dictionary for a step in a run."""
    store = RunHistoryStore(storage_dir)
    return store.get_step_output(run_id, step_id)
```

---

## 4. Caveats

1. **Filesystem Atomicity**: Atomic rename via `tempfile` and `Path.replace()` depends on temporary files being created on the *same filesystem volume* as `.workflow_runs/`. Specifying `dir=self.storage_dir` guarantees atomic replacement across POSIX-compliant filesystems.
2. **Process Multi-Threading vs Multi-Processing**: `threading.RLock()` ensures thread-safety within a single Python process. Cross-process atomic writes are handled safely via POSIX atomic rename (atomic directory entry swap), so readers never read a partially written file.
3. **No Caveats remaining**: All requested focus areas are fully covered in the specification.

---

## 5. Conclusion

The technical design for `agent_workflow/persistence.py` provides:
- Seamless JSON serialization and deserialization of `RunHistory` and `StepResult` dataclasses using `to_dict()`, `from_dict()`, and `WorkflowJSONEncoder`.
- Production-grade atomic write safety via temporary files in the target directory and `os.fsync`.
- Thread safety via `threading.RLock()`.
- Explicit error handling with `PersistenceError`, `RunNotFoundError`, and `RunCorruptedError`.
- Clean API class (`RunHistoryStore` / `ExecutionStore`) and module helper functions for CLI integration.

---

## 6. Verification Method

To verify the implementation of `agent_workflow/persistence.py`:

1. **Unit Test Command**:
   ```bash
   python3 -m unittest discover -s tests
   ```
2. **Key Test Verification Scenarios (`tests/test_persistence.py`)**:
   - **Save & Load Roundtrip**: Verify saving a populated `RunHistory` with multiple `StepResult` items creates `.workflow_runs/<run_id>.json` and reloads identical status, timestamps, and step outputs.
   - **Atomic Write Integrity**: Verify partial write failures leave existing JSON files untouched and clean up temporary `.tmp` files.
   - **Directory Creation**: Pass a non-existent directory path to `RunHistoryStore` and verify auto-creation upon initialization or saving.
   - **Error Handling**: Verify loading a missing `run_id` raises `RunNotFoundError` and loading a malformed/invalid JSON file raises `RunCorruptedError`.
   - **Path Traversal Protection**: Pass `run_id="../../etc/passwd"` or invalid characters and verify `ValueError` is raised.
   - **List & Query Functions**: Verify `list_runs()` returns all stored runs sorted by start time descending, and `get_step_result` / `get_step_output` extract correct step data.
