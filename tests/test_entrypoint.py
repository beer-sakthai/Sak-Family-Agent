"""Test the python -m sakthai entry point (sakthai/__main__.py)."""

from __future__ import annotations

import runpy
import subprocess
import sys
from unittest.mock import patch


def test_main_guard_calls_cli_main() -> None:
    """Running sakthai as __main__ must invoke the CLI's main() function."""
    with patch("sakthai.cli.main") as mock_main:
        runpy.run_module("sakthai", run_name="__main__", alter_sys=False)
    mock_main.assert_called_once()


def test_python_m_sakthai_help_exits_zero() -> None:
    """python -m sakthai --help must exit 0 and print usage."""
    result = subprocess.run(
        [sys.executable, "-m", "sakthai", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout.lower()
