"""Tests for diagnose_personas.py script."""

from __future__ import annotations

import importlib.util
import os
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


def test_persona_mcp_config_path() -> None:
    path = module.persona_mcp_config_path("test-persona")
    assert isinstance(path, Path)
    assert path.parts[-3:] == ("test-persona", "config", "mcp.json")


def test_info_with_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info function outputs correctly with both label and detail."""
    module.info("My Label", "My Detail")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] My Label — My Detail\n"


def test_info_without_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info function outputs correctly with only a label."""
    module.info("My Label")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] My Label\n"


def test_info_empty_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info function outputs correctly with an empty detail string."""
    module.info("My Label", "")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] My Label\n"


def test_warn_basic(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn function adds to warnings list and prints correct output with detail."""
    module.warnings.clear()
    module.warn("test label", "test detail")

    assert "test label" in module.warnings

    captured = capsys.readouterr()
    assert "  [WARN] test label" in captured.out
    assert "— test detail" in captured.out


def test_warn_no_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn function adds to warnings list and prints correct output without detail."""
    module.warnings.clear()
    module.warn("test label")

    assert "test label" in module.warnings

    captured = capsys.readouterr()
    assert "  [WARN] test label" in captured.out
    assert "—" not in captured.out


def test_warn_empty_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn function handles empty string detail like no detail."""
    module.warnings.clear()
    module.warn("test label", "")

    assert "test label" in module.warnings

    captured = capsys.readouterr()
    assert "  [WARN] test label" in captured.out
    assert "—" not in captured.out
    assert "test label\n" in captured.out
