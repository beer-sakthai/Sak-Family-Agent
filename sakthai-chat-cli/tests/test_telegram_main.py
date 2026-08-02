"""Tests for telegram entrypoint module (sakthai.telegram.__main__)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import sakthai.telegram


def test_telegram_main_execution() -> None:
    # Resolve absolute path to __main__.py
    main_file = Path(sakthai.telegram.__file__).parent / "__main__.py"
    code = main_file.read_text(encoding="utf-8")

    # Run the script content with __name__ set to "__main__"
    with patch("sakthai.telegram.bot.main") as mock_main:
        globals_dict = {
            "__name__": "__main__",
            "__package__": "sakthai.telegram",
            "__builtins__": __builtins__,
        }
        exec(code, globals_dict)
        mock_main.assert_called_once()
