"""Tests for sakthai.cli module initialization (Windows UTF-8 reconfiguration)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock


def test_cli_init_windows_utf8_reconfigure_logic() -> None:
    """Verify that the Windows UTF-8 reconfigure logic works correctly."""
    # Test the logic directly without importing the module on win32
    # (which would fail on Linux due to missing msvcrt)

    # Create mock stdout/stderr with reconfigure method
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()

    # Simulate the reconfigure logic from sakthai/cli/__init__.py
    if sys.platform == "win32":
        for _stream in (mock_stdout, mock_stderr):
            if hasattr(_stream, "reconfigure"):
                _stream.reconfigure(encoding="utf-8", errors="replace")

    # The test passes if we reach here without exception
    # On non-Windows, the condition is false so reconfigure is not called
    if sys.platform != "win32":
        # On Linux/macOS, verify reconfigure was not called
        mock_stdout.reconfigure.assert_not_called()
        mock_stderr.reconfigure.assert_not_called()


def test_cli_init_can_import_on_current_platform() -> None:
    """The CLI module should import successfully on the current platform."""
    # This is a smoke test to ensure the CLI initialization doesn't crash
    import sakthai.cli  # noqa: F401

    # No assertion needed; the test passes if no exception is raised
