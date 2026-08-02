"""Tests for the comfyui batch run script helpers."""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH_DIR = REPO_ROOT / "personas" / "sakthai" / "skills" / "SakThai-comfyui" / "scripts"

# Add script directory to sys.path to allow imports
if str(BATCH_DIR) not in sys.path:
    sys.path.insert(0, str(BATCH_DIR))

import run_batch


@pytest.fixture
def mock_emit_json():
    with patch("run_batch.emit_json") as mock:
        yield mock


@pytest.fixture
def mock_log():
    with patch("run_batch.log") as mock:
        yield mock


def test_parse_args_valid() -> None:
    argv = ["--workflow", "test.json", "--count", "10", "--parallel", "4"]
    args = run_batch.parse_args(argv)
    assert args.workflow == "test.json"
    assert args.count == 10
    assert args.parallel == 4
    assert args.args == "{}"
    assert args.sweep == ""


def test_load_and_validate_args_no_count_or_sweep(mock_emit_json) -> None:
    args = argparse.Namespace(
        count=0,
        sweep="",
        args="{}",
        randomize_seed=False,
    )
    result = run_batch.load_and_validate_args(args)
    assert result is None
    mock_emit_json.assert_called_once_with({"error": "Specify --count N or --sweep '{...}'"})


def test_load_and_validate_args_invalid_json_args(mock_emit_json) -> None:
    args = argparse.Namespace(
        count=5,
        sweep="",
        args="{invalid",
        randomize_seed=False,
    )
    result = run_batch.load_and_validate_args(args)
    assert result is None
    # Verifying that emit_json is called with an invalid JSON error
    assert mock_emit_json.call_count == 1
    assert "Invalid JSON parameter" in mock_emit_json.call_args[0][0]["error"]


def test_load_and_validate_args_invalid_json_sweep(mock_emit_json) -> None:
    args = argparse.Namespace(
        count=0,
        sweep="{invalid",
        args="{}",
        randomize_seed=False,
    )
    result = run_batch.load_and_validate_args(args)
    assert result is None
    assert mock_emit_json.call_count == 1
    assert "Invalid JSON parameter" in mock_emit_json.call_args[0][0]["error"]


def test_load_and_validate_args_non_dict_sweep(mock_emit_json) -> None:
    args = argparse.Namespace(
        count=0,
        sweep="[1, 2, 3]",
        args="{}",
        randomize_seed=False,
    )
    result = run_batch.load_and_validate_args(args)
    assert result is None
    mock_emit_json.assert_called_once_with({"error": "--sweep must be a JSON object {param: [values]}"})


def test_load_and_validate_args_empty_values_sweep(mock_emit_json) -> None:
    args = argparse.Namespace(
        count=0,
        sweep='{"seed": []}',
        args="{}",
        randomize_seed=False,
    )
    result = run_batch.load_and_validate_args(args)
    assert result is None
    mock_emit_json.assert_called_once_with({"error": "--sweep parameters have empty value lists: ['seed']"})


def test_load_and_validate_args_sweep_warning_ignored(mock_log) -> None:
    args = argparse.Namespace(
        count=5,
        sweep='{"seed": [1, 2]}',
        args="{}",
        randomize_seed=True,
    )
    result = run_batch.load_and_validate_args(args)
    assert result == ({}, {"seed": [1, 2]})
    mock_log.assert_called_once_with("--sweep set; ignoring --count / --randomize-seed (sweep defines the runs)")


def test_load_workflow_not_found(mock_emit_json) -> None:
    result = run_batch.load_workflow("non_existent_file_999.json")
    assert result is None
    mock_emit_json.assert_called_once_with({"error": "Workflow not found: non_existent_file_999.json"})


def test_load_workflow_invalid_json(tmp_path: Path, mock_emit_json) -> None:
    bad_wf = tmp_path / "bad_workflow.json"
    bad_wf.write_text("{bad json")
    result = run_batch.load_workflow(str(bad_wf))
    assert result is None
    assert mock_emit_json.call_count == 1


def test_load_workflow_valid_json(tmp_path: Path) -> None:
    good_wf = tmp_path / "good_workflow.json"
    good_wf.write_text(json.dumps({"1": {"class_type": "KSampler"}}))
    result = run_batch.load_workflow(str(good_wf))
    assert result == {"1": {"class_type": "KSampler"}}


@patch("run_batch.execute_one")
def test_run_batch_execution_sequential(mock_execute_one, mock_log) -> None:
    runner = MagicMock()
    workflow = {"some": "wf"}
    schema = {}
    runs = [{"seed": 1}, {"seed": 2}]
    base_dir = Path("/tmp/mock_batch")

    mock_execute_one.side_effect = [
        {"status": "success", "outputs": ["out1.png"]},
        {"status": "error", "error": "mocked failure"},
    ]

    results, failures = run_batch.run_batch_execution(
        runner, workflow, schema, runs,
        base_dir=base_dir, timeout=10, parallel=1, ws=False, continue_on_error=True
    )

    assert len(results) == 2
    assert results[0]["status"] == "success"
    assert results[1]["status"] == "error"
    assert failures == 1
    assert mock_execute_one.call_count == 2


@patch("run_batch.execute_one")
def test_run_batch_execution_parallel(mock_execute_one, mock_log) -> None:
    runner = MagicMock()
    workflow = {"some": "wf"}
    schema = {}
    runs = [{"seed": 1}, {"seed": 2}]
    base_dir = Path("/tmp/mock_batch")

    mock_execute_one.side_effect = [
        {"status": "success", "outputs": ["out1.png"]},
        {"status": "success", "outputs": ["out2.png"]},
    ]

    results, failures = run_batch.run_batch_execution(
        runner, workflow, schema, runs,
        base_dir=base_dir, timeout=10, parallel=2, ws=False, continue_on_error=True
    )

    assert len(results) == 2
    assert results[0]["status"] == "success"
    assert results[1]["status"] == "success"
    assert failures == 0
    assert mock_execute_one.call_count == 2
