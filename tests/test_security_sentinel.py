from __future__ import annotations

import os
from unittest.mock import MagicMock

from sakthai.agent.tools import _send_telegram_message
from sakthai.memory.store import MemoryStore


def test_telegram_token_leak_in_error() -> None:
    """Verify that an invalid TELEGRAM_BOT_TOKEN is not leaked in the error message."""
    sensitive_token = "12345:sensitive_secret_data"
    os.environ["TELEGRAM_BOT_TOKEN"] = sensitive_token
    os.environ["TELEGRAM_CHAT_ID"] = "67890"

    # Use a token that fails the format regex ^[0-9]+:[a-zA-Z0-9_-]+$
    # or just use any invalid token and ensure it's not in the result.
    os.environ["TELEGRAM_BOT_TOKEN"] = "INVALID TOKEN WITH SECRET 12345"

    store = MagicMock(spec=MemoryStore)
    result = _send_telegram_message({"message": "hello"}, store)

    assert "Error: Invalid TELEGRAM_BOT_TOKEN format" in result
    assert "INVALID TOKEN" not in result
    assert "SECRET" not in result
    assert "12345" not in result

if __name__ == "__main__":
    test_telegram_token_leak_in_error()
    print("Security test passed.")
