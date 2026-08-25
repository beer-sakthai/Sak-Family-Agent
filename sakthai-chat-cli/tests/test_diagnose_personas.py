"""Tests for diagnose_personas.py script."""

import os
import sys

import pytest

# Add the script directory to the path so we can import diagnose_personas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
import diagnose_personas  # noqa: E402


def test_info_with_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info function outputs correctly with both label and detail."""
    diagnose_personas.info("My Label", "My Detail")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] My Label — My Detail\n"


def test_info_without_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info function outputs correctly with only a label."""
    diagnose_personas.info("My Label")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] My Label\n"


def test_info_empty_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info function outputs correctly with an empty detail string."""
    diagnose_personas.info("My Label", "")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] My Label\n"
