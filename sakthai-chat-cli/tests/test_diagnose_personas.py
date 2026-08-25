"""Tests for the diagnose_personas script."""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the script as a module
script_path = Path(__file__).parent.parent / "scripts" / "diagnose_personas.py"
spec = importlib.util.spec_from_file_location("diagnose_personas", script_path)
if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    sys.modules["diagnose_personas"] = module
    spec.loader.exec_module(module)
else:
    raise ImportError(f"Could not load script from {script_path}")


def test_warn_basic(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn function adds to warnings list and prints correct output with detail."""
    module.warnings.clear()
    module.warn("test label", "test detail")

    # Check it was added to the warnings list
    assert "test label" in module.warnings

    # Check stdout
    captured = capsys.readouterr()
    assert "  [WARN] test label" in captured.out
    assert "— test detail" in captured.out


def test_warn_no_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn function adds to warnings list and prints correct output without detail."""
    module.warnings.clear()
    module.warn("test label")

    # Check it was added to the warnings list
    assert "test label" in module.warnings

    # Check stdout
    captured = capsys.readouterr()
    assert "  [WARN] test label" in captured.out
    assert "—" not in captured.out


def test_warn_empty_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn function handles empty string detail like no detail."""
    module.warnings.clear()
    module.warn("test label", "")

    # Check it was added to the warnings list
    assert "test label" in module.warnings

    # Check stdout
    captured = capsys.readouterr()
    assert "  [WARN] test label" in captured.out
    assert "—" not in captured.out
    assert "test label\n" in captured.out
