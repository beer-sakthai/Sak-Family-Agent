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


class RunNotFoundError(PersistenceError, FileNotFoundError):
    """Raised when a specified run_id is not found in the storage directory."""
    pass


class RunCorruptedError(PersistenceError, ValueError):
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
        """Initialize RunHistoryStore with optional custom storage directory."""
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

        # Check for path separators before taking filename to detect path traversal attempts
        if "/" in clean_id or "\\" in clean_id:
            # If path traversal attempted, check if Path(clean_id).name is different or invalid
            clean_name = Path(clean_id).name
            if not clean_name or clean_name != clean_id:
                raise ValueError(f"Invalid characters or path traversal in run_id: '{run_id}'")
            clean_id = clean_name

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
                if isinstance(e, (TypeError, ValueError, PersistenceError)):
                    raise
                raise PersistenceError(f"Failed to save run history '{history.run_id}': {e}") from e

    def load_run_history(self, run_id: str) -> RunHistory:
        """Load RunHistory from JSON file by run_id or file path."""
        with self._lock:
            # Check if run_id is a direct file path vs run_id string
            try:
                target_path = self.get_run_path(run_id)
            except ValueError:
                # If run_id was a custom file path, ensure it remains inside self.storage_dir
                raw_path = Path(run_id).resolve()
                try:
                    raw_path.relative_to(self.storage_dir)
                except ValueError:
                    raise ValueError(f"Path traversal attempt detected in run_id: '{run_id}'")
                target_path = raw_path

            if not target_path.exists() or target_path.is_dir():
                raise RunNotFoundError(f"Run history not found for run_id or path: '{run_id}'")

            try:
                content = target_path.read_text(encoding="utf-8")
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise RunCorruptedError(f"Run history JSON root must be an object, got {type(data).__name__}")
                return RunHistory.from_dict(data)
            except RunCorruptedError:
                raise
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


# Class aliases for backward compatibility and API contract matching
HistoryStore = RunHistoryStore
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
