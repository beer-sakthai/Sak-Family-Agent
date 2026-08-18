"""Execution run history and step log persistence store.

Provides atomic, thread-safe persistence of RunHistory and StepResult dataclasses
to structured JSON files under `.workflow_runs/<run_id>.json`.
"""

import contextlib
import json
import os
import re
import tempfile
import threading
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from agent_workflow.models import RunHistory, StepResult


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
    """Custom JSON encoder handling dataclasses, Enums, dates, sets, tuples, and Path objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, "to_dict") and callable(o.to_dict):
            return o.to_dict()
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, (set, tuple)):
            return list(o)
        return super().default(o)


class HistoryStore:
    """Manages persistence and retrieval of RunHistory instances to disk."""

    DEFAULT_STORAGE_DIR = ".workflow_runs"

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        if storage_dir is None:
            self.storage_dir = Path(self.DEFAULT_STORAGE_DIR).resolve()
        else:
            self.storage_dir = Path(storage_dir).resolve()
        self._lock = threading.RLock()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists with safe permissions."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_run_id(self, run_id: str) -> str:
        """Validate and sanitize run_id against directory traversal."""
        if not run_id or not isinstance(run_id, str):
            raise ValueError("run_id must be a non-empty string.")

        # Disallow directory separators and relative navigation components
        if "/" in run_id or "\\" in run_id or ".." in run_id:
            raise ValueError(
                f"Invalid characters or traversal detected in run_id: '{run_id}'"
            )

        # Disallow null bytes
        if "\0" in run_id:
            raise ValueError(f"Null byte detected in run_id: '{run_id}'")

        # Strip any leading/trailing periods or whitespaces
        cleaned = run_id.strip(" .")
        if not cleaned:
            raise ValueError(
                f"run_id '{run_id}' is invalid after trimming spaces/dots."
            )

        # Whitelist alphanumeric and safe symbols: [a-zA-Z0-9_-]
        if not re.match(r"^[a-zA-Z0-9_-]+$", cleaned):
            raise ValueError(
                f"run_id contains invalid characters: '{run_id}'. Allowed: [a-zA-Z0-9_-]"
            )

        return cleaned

    def get_run_path(self, run_id: str) -> Path:
        """Resolve full Path for given run_id inside storage directory."""
        clean_id = self._sanitize_run_id(run_id)
        target_path = (self.storage_dir / f"{clean_id}.json").resolve()

        # Enforce containment inside storage_dir
        try:
            target_path.relative_to(self.storage_dir)
        except ValueError as err:
            raise ValueError(
                f"Resolved run path '{target_path}' is outside storage directory '{self.storage_dir}'"
            ) from err

        return target_path

    def save_run_history(self, history: RunHistory) -> Path:
        """Atomically persist a RunHistory instance to JSON file."""
        if not isinstance(history, RunHistory):
            raise TypeError(
                f"Expected RunHistory instance, got {type(history).__name__}"
            )

        target_path = self.get_run_path(history.run_id)
        data = history.to_dict()

        with self._lock:
            self._ensure_storage_dir()
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=self.storage_dir,
                    delete=False,
                    suffix=".tmp",
                    encoding="utf-8",
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    json.dump(data, temp_file, indent=2, cls=WorkflowJSONEncoder)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())

                temp_path.replace(target_path)
                return target_path
            except Exception as e:
                if temp_path and temp_path.exists():
                    with contextlib.suppress(OSError):
                        temp_path.unlink()
                if isinstance(e, (TypeError, ValueError, PersistenceError)):
                    raise
                raise PersistenceError(
                    f"Failed to save run history '{history.run_id}': {e}"
                ) from e

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
                except ValueError as err:
                    raise ValueError(
                        f"Path traversal attempt detected in run_id: '{run_id}'"
                    ) from err
                target_path = raw_path

            if not target_path.exists() or target_path.is_dir():
                raise RunNotFoundError(f"Run history not found for run_id or path: '{run_id}'")

            try:
                content = target_path.read_text(encoding="utf-8")
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise RunCorruptedError(
                        f"Run history JSON root must be an object, got {type(data).__name__}"
                    )
                return RunHistory.from_dict(data)
            except RunCorruptedError:
                raise
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                raise RunCorruptedError(
                    f"Failed to parse run history file '{target_path}': {e}"
                ) from e

    def list_runs(self) -> list[RunHistory]:
        """List all stored run histories, ordered by start_time descending (newest first)."""
        with self._lock:
            self._ensure_storage_dir()
            runs: list[RunHistory] = []
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

    def get_step_output(self, run_id: str, step_id: str) -> dict[str, Any]:
        """Retrieve execution output dictionary for a specific step within a run history."""
        step_res = self.get_step_result(run_id, step_id)
        return step_res.output


# Class aliases for backward compatibility and API contract matching
RunHistoryStore = HistoryStore
ExecutionStore = HistoryStore


# Module-level convenience functions
def save_run_history(history: RunHistory, storage_dir: str | Path | None = None) -> Path:
    """Convenience function to save a RunHistory."""
    store = HistoryStore(storage_dir)
    return store.save_run_history(history)


def get_run_history(run_id: str, storage_dir: str | Path | None = None) -> RunHistory:
    """Convenience function to retrieve a RunHistory by run_id."""
    store = HistoryStore(storage_dir)
    return store.load_run_history(run_id)


def load_run_history(run_id: str, storage_dir: str | Path | None = None) -> RunHistory:
    """Alias for get_run_history."""
    return get_run_history(run_id, storage_dir)


def list_runs(storage_dir: str | Path | None = None) -> list[RunHistory]:
    """Convenience function to list all saved RunHistories."""
    store = HistoryStore(storage_dir)
    return store.list_runs()


def delete_run_history(run_id: str, storage_dir: str | Path | None = None) -> bool:
    """Convenience function to delete a run history file."""
    store = HistoryStore(storage_dir)
    return store.delete_run_history(run_id)


def get_step_result(
    run_id: str, step_id: str, storage_dir: str | Path | None = None
) -> StepResult:
    """Convenience function to get a StepResult for a step in a run."""
    store = HistoryStore(storage_dir)
    return store.get_step_result(run_id, step_id)


def get_step_output(
    run_id: str, step_id: str, storage_dir: str | Path | None = None
) -> dict[str, Any]:
    """Convenience function to get output dictionary for a step in a run."""
    store = HistoryStore(storage_dir)
    return store.get_step_output(run_id, step_id)
