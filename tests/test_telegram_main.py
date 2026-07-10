"""Tests for telegram entrypoint module (sakthai.telegram.__main__)."""

from __future__ import annotations

import runpy
from unittest.mock import patch


def test_telegram_main_execution() -> None:
    """Running the module as __main__ invokes bot.main() exactly once.

    ``runpy`` (rather than ``exec`` on the file text) attributes the executed
    lines to the real module file, so coverage sees them.
    """
    with patch("sakthai.telegram.bot.main") as mock_main:
        runpy.run_module("sakthai.telegram.__main__", run_name="__main__", alter_sys=False)
    mock_main.assert_called_once()
